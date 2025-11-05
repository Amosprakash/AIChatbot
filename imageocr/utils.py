"""
Utility functions for multi-format text extraction.
Supports images, videos, PDFs, DOCX, Excel, CSV, and TXT files.
"""

import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from docx import Document
import pandas as pd
import io
from rake_nltk import Rake
import nltk
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from nltk.corpus import stopwords
from PyPDF2 import PdfReader
import cv2
import numpy as np
import asyncio

import log as Log
from config import config
from image import run_paddle_ocr, run_tesseract_on_low_conf

# --- Configure Tesseract and Poppler ---
TESSERACT_PATH = config.TESSERACT_PATH
POPPLER_PATH = config.POPPLER_PATH

if not os.path.exists(TESSERACT_PATH):
    Log.log.warning(f"Tesseract not found at {TESSERACT_PATH}")
else:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# --- Download NLTK resources ---
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
except Exception as e:
    Log.log.warning(f"Failed to download NLTK data: {e}")


class FileCache:
    """Simple file-based cache for OCR results."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl: int = None):
        """
        Initialize file cache.

        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live for cache entries in seconds
        """
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.ttl = ttl or config.CACHE_TTL
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "cache_index.json"
        self._index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                Log.log.warning(f"Failed to load cache index: {e}")
        return {}

    def _save_index(self):
        """Save cache index to disk."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            Log.log.error(f"Failed to save cache index: {e}")

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        age = datetime.now().timestamp() - timestamp
        return age > self.ttl

    def get(self, key: str) -> Optional[str]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._index:
            return None

        entry = self._index[key]
        if self._is_expired(entry['timestamp']):
            self.delete(key)
            return None

        cache_file = self.cache_dir / f"{key}.txt"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                Log.log.error(f"Failed to read cache file: {e}")
                return None
        return None

    def set(self, key: str, value: str):
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_file = self.cache_dir / f"{key}.txt"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(value)

            self._index[key] = {
                'timestamp': datetime.now().timestamp(),
                'file': str(cache_file)
            }
            self._save_index()
        except Exception as e:
            Log.log.error(f"Failed to write to cache: {e}")

    def delete(self, key: str):
        """
        Delete cache entry.

        Args:
            key: Cache key
        """
        if key in self._index:
            cache_file = self.cache_dir / f"{key}.txt"
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except Exception as e:
                    Log.log.error(f"Failed to delete cache file: {e}")

            del self._index[key]
            self._save_index()

    def clear_expired(self):
        """Remove all expired cache entries."""
        expired_keys = [
            key for key, entry in self._index.items()
            if self._is_expired(entry['timestamp'])
        ]
        for key in expired_keys:
            self.delete(key)
        Log.log.info(f"Cleared {len(expired_keys)} expired cache entries")


# Initialize cache
ocr_cache = FileCache() if config.ENABLE_CACHE else {}


def get_image_hash(content: bytes) -> str:
    """
    Generate a unique hash for file content.

    Args:
        content: File content as bytes

    Returns:
        MD5 hash of content
    """
    return hashlib.md5(content).hexdigest()


def extract_keywords(text: str, top_n: int = None) -> str:
    """
    Extract keywords from text using RAKE algorithm.

    Args:
        text: Input text
        top_n: Number of top keywords to extract (uses config default if None)

    Returns:
        Space-separated keywords string
    """
    if top_n is None:
        top_n = config.KEYWORD_TOP_N

    try:
        stop_words = stopwords.words("english")
        rake = Rake(stopwords=stop_words)
        rake.extract_keywords_from_text(text)
        keywords = rake.get_ranked_phrases()[:top_n]
        return " ".join(keywords)
    except Exception as e:
        Log.log.error(f"Keyword extraction failed: {e}")
        return ""


def enhance_and_correct_image(image: np.ndarray) -> np.ndarray:
    """
    Enhance image quality for better OCR results.

    Args:
        image: Input image as numpy array

    Returns:
        Enhanced image
    """
    try:
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Auto-rotate if needed
        h, w = gray.shape
        if w > h:
            gray = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)

        # Resize for better OCR
        resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(resized, h=30)

        # Sharpen
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(denoised, -1, kernel)

        # Histogram equalization
        equalized = cv2.equalizeHist(sharpened)

        # Adaptive thresholding
        binarized = cv2.adaptiveThreshold(
            equalized, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11, C=2
        )

        return binarized
    except Exception as e:
        Log.log.error(f"Image enhancement failed: {e}")
        return image


async def extract_text(file) -> Dict[str, Any]:
    """
    Extract text from various file formats asynchronously.

    Args:
        file: UploadFile object with filename and read() method

    Returns:
        Dictionary with keys:
            - success (bool): Whether extraction succeeded
            - message (str): Status/error message
            - text (str): Extracted text
    """
    ext = file.filename.split(".")[-1].lower()
    content = await file.read()
    text = ""

    image_exts = ["png", "jpg", "jpeg", "tiff", "bmp", "gif", "webp"]
    video_exts = ["mp4", "avi", "mov", "mkv"]

    try:
        # ----- IMAGE OCR -----
        if ext in image_exts:
            # Compute hash for caching
            image_hash = get_image_hash(content)

            # Check cache
            if config.ENABLE_CACHE:
                cached_text = ocr_cache.get(image_hash)
                if cached_text:
                    Log.log.info(f"OCR cache hit for image hash {image_hash}")
                    return {
                        "success": True,
                        "message": "Text extracted from cache",
                        "text": cached_text
                    }

            # Convert bytes to image
            try:
                image = Image.open(io.BytesIO(content)).convert("RGB")
                img_np = np.array(image)
            except Exception as e:
                Log.log.error(f"Failed to load image: {e}")
                return {
                    "success": False,
                    "message": f"Invalid image file: {str(e)}",
                    "text": ""
                }

            # Run PaddleOCR
            result = run_paddle_ocr(img_np, debug=False)
            if not result["success"]:
                return {"success": False, "message": result["message"], "text": ""}

            paddle_lines = result["lines"]

            # Refine with Tesseract
            result1 = run_tesseract_on_low_conf(paddle_lines)
            if not result1["success"]:
                return {"success": False, "message": result1["message"], "text": ""}

            tesseract_text = result1["lines"]

            # Deduplicate lines
            seen = set()
            final_lines = []
            for line in tesseract_text.splitlines():
                clean_line = line.strip()
                if clean_line and clean_line not in seen:
                    final_lines.append(clean_line)
                    seen.add(clean_line)

            final_text = "\n".join(final_lines)

            # Cache result
            if config.ENABLE_CACHE:
                ocr_cache.set(image_hash, final_text)

            return {
                "success": True,
                "message": "Text extracted successfully",
                "text": final_text
            }

        # ----- VIDEO OCR -----
        elif ext in video_exts:
            temp_video_path = f"temp_video_{get_image_hash(content)}.{ext}"
            try:
                with open(temp_video_path, "wb") as f:
                    f.write(content)

                cap = cv2.VideoCapture(temp_video_path)
                frame_texts = []
                frame_interval = config.VIDEO_FRAME_INTERVAL_SEC
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps
                current_time = 0

                while cap.isOpened() and current_time < duration:
                    cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                    ret, frame = cap.read()
                    if not ret:
                        break

                    enhanced_frame = enhance_and_correct_image(frame)
                    frame_text = pytesseract.image_to_string(enhanced_frame, lang="eng")
                    if frame_text.strip():
                        frame_texts.append(frame_text)
                    current_time += frame_interval

                cap.release()
                text = "\n\n".join(frame_texts)

                return {
                    "success": True,
                    "message": f"Extracted text from {len(frame_texts)} video frames",
                    "text": text
                }

            except Exception as e:
                Log.log.error(f"Video OCR failed: {e}")
                return {
                    "success": False,
                    "message": f"Video processing error: {str(e)}",
                    "text": ""
                }
            finally:
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)

        # ----- PDF -----
        elif ext == "pdf":
            try:
                pdf_reader = PdfReader(io.BytesIO(content))
                text = "\n".join([
                    page.extract_text() or ""
                    for page in pdf_reader.pages
                ]).strip()

                # If no text, use OCR on PDF images
                if not text:
                    batch_size = config.PDF_BATCH_SIZE
                    total_pages = len(pdf_reader.pages)
                    ocr_texts = []

                    for i in range(0, total_pages, batch_size):
                        images = convert_from_bytes(
                            content,
                            poppler_path=POPPLER_PATH,
                            first_page=i + 1,
                            last_page=min(i + batch_size, total_pages)
                        )
                        for img in images:
                            img_np = np.array(img.convert("RGB"))
                            processed = enhance_and_correct_image(img_np)
                            page_text = pytesseract.image_to_string(processed, lang='eng')
                            if page_text.strip():
                                ocr_texts.append(page_text)

                    text = "\n".join(ocr_texts)

                return {
                    "success": True,
                    "message": f"Extracted text from {len(pdf_reader.pages)} PDF pages",
                    "text": text
                }

            except Exception as e:
                Log.log.error(f"PDF extraction failed: {e}")
                return {
                    "success": False,
                    "message": f"PDF processing error: {str(e)}",
                    "text": ""
                }

        # ----- DOCX -----
        elif ext == "docx":
            try:
                doc = Document(io.BytesIO(content))
                text = "\n".join([p.text for p in doc.paragraphs])
                return {
                    "success": True,
                    "message": "Text extracted from DOCX",
                    "text": text
                }
            except Exception as e:
                Log.log.error(f"DOCX extraction failed: {e}")
                return {
                    "success": False,
                    "message": f"DOCX processing error: {str(e)}",
                    "text": ""
                }

        # ----- EXCEL -----
        elif ext in ["xlsx", "xls"]:
            try:
                text = excel_to_text_in_chunks(content, chunk_size=config.EXCEL_CHUNK_SIZE)
                return {
                    "success": True,
                    "message": "Text extracted from Excel",
                    "text": text
                }
            except Exception as e:
                Log.log.error(f"Excel extraction failed: {e}")
                return {
                    "success": False,
                    "message": f"Excel processing error: {str(e)}",
                    "text": ""
                }

        # ----- TXT / CSV -----
        elif ext in ["txt", "csv"]:
            try:
                text = content.decode("utf-8")
                return {
                    "success": True,
                    "message": f"Text extracted from {ext.upper()}",
                    "text": text
                }
            except UnicodeDecodeError:
                try:
                    text = content.decode("latin-1")
                    return {
                        "success": True,
                        "message": f"Text extracted from {ext.upper()} (latin-1 encoding)",
                        "text": text
                    }
                except Exception as e:
                    Log.log.error(f"Text file decoding failed: {e}")
                    return {
                        "success": False,
                        "message": f"Text decoding error: {str(e)}",
                        "text": ""
                    }

        else:
            Log.log.warning(f"Unsupported file type: {ext}")
            return {
                "success": False,
                "message": f"Unsupported file type: {ext}",
                "text": ""
            }

    except Exception as e:
        Log.log.error(f"Extraction error for {file.filename}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "text": ""
        }


def extract_text_sync(content: bytes, filename: str) -> str:
    """
    Synchronous wrapper for extract_text function.

    Args:
        content: File content as bytes
        filename: Original filename

    Returns:
        Extracted text string
    """
    class DummyFile:
        def __init__(self, content, filename):
            self._content = content
            self.filename = filename

        async def read(self):
            return self._content

    dummy_file = DummyFile(content, filename)
    result = asyncio.run(extract_text(dummy_file))
    return result.get("text", "")


def excel_to_text_in_chunks(content: bytes, chunk_size: int = 1000) -> str:
    """
    Convert Excel file to text in chunks to handle large files.

    Args:
        content: Excel file content as bytes
        chunk_size: Number of rows per chunk

    Returns:
        Text representation of Excel data
    """
    try:
        df = pd.read_excel(io.BytesIO(content))
        all_chunks_text = []

        for start in range(0, len(df), chunk_size):
            chunk = df.iloc[start:start + chunk_size]
            chunk_text = chunk.to_csv(index=False)
            all_chunks_text.append(chunk_text)

        return "\n\n".join(all_chunks_text)
    except Exception as e:
        Log.log.error(f"Excel to text conversion failed: {e}")
        return ""
