"""
Image processing and OCR module for ImageOCR.
Handles image preprocessing, PaddleOCR, and Tesseract OCR integration with
advanced image enhancement techniques.
"""

import cv2
import numpy as np
import pytesseract
from paddleocr import PaddleOCR
from typing import Dict, List, Tuple, Any, Optional
import os

import log as Log
from config import config
from Levenshtein import ratio as lev_ratio

# === Initialize PaddleOCR ===
try:
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="en",
        det_model_dir=config.PADDLE_DET_MODEL,
        rec_model_dir=config.PADDLE_REC_MODEL,
        cls_model_dir=config.PADDLE_CLS_MODEL
    )
    Log.log.info("Loaded PP-OCRv4 custom models successfully")
except Exception as e:
    Log.log.warning(f"Custom PP-OCR models not found, using default: {e}")
    ocr = PaddleOCR(use_angle_cls=True, lang='en')

# === Configure Tesseract ===
if os.path.exists(config.TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH
else:
    Log.log.warning(f"Tesseract not found at {config.TESSERACT_PATH}")

CONFIDENCE_THRESHOLD = config.CONFIDENCE_THRESHOLD


def super_resolve(img: np.ndarray, debug: bool = False) -> np.ndarray:
    """
    Apply super-resolution to enhance image quality.

    Args:
        img: Input image as numpy array
        debug: If True, save intermediate results

    Returns:
        Super-resolved image
    """
    try:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        model_path = config.SUPER_RES_MODEL
        if os.path.exists(model_path):
            sr.readModel(model_path)
            sr.setModel("fsrcnn", 4)
            img = sr.upsample(img)
            if debug:
                cv2.imwrite("1_superres.png", img)
            Log.log.info("Super-resolution applied successfully")
        else:
            Log.log.warning(f"Super-resolution model not found at {model_path}")
    except Exception as e:
        Log.log.info(f"Super-resolution skipped: {e}")
    return img


def safe_to_gray(img: np.ndarray) -> np.ndarray:
    """
    Safely convert image to grayscale regardless of input format.

    Args:
        img: Input image (grayscale, BGR, or BGRA)

    Returns:
        Grayscale image

    Raises:
        ValueError: If image shape is unsupported
    """
    if len(img.shape) == 2:  # already grayscale
        return img
    elif len(img.shape) == 3 and img.shape[2] == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif len(img.shape) == 3 and img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    else:
        raise ValueError(f"Unsupported image shape: {img.shape}")


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Automatically deskew (straighten) a rotated image.

    Args:
        image: Input image

    Returns:
        Deskewed image
    """
    try:
        gray = safe_to_gray(image)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        angles = []
        for cnt in contours:
            rect = cv2.minAreaRect(cnt)
            angle = rect[-1]
            if angle < -45:
                angle += 90
            if -45 < angle < 45:
                angles.append(angle)

        if angles:
            median_angle = np.median(angles)
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE
            )
            Log.log.info(f"Image deskewed by {median_angle:.2f} degrees")
            return rotated
    except Exception as e:
        Log.log.warning(f"Deskew failed: {e}")
    return image


def detect_blur(image: np.ndarray, threshold: float = None) -> Tuple[bool, float]:
    """
    Detect if an image is blurry using Laplacian variance.

    Args:
        image: Input image (BGR format)
        threshold: Blur threshold (lower = more blurry), uses config if None

    Returns:
        Tuple of (is_blurry: bool, blur_score: float)
    """
    if threshold is None:
        threshold = config.BLUR_THRESHOLD

    gray = safe_to_gray(image)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold, laplacian_var


def conditional_deblur(img: np.ndarray) -> np.ndarray:
    """
    Conditionally deblur an image if it's detected as blurry.

    Args:
        img: Input image

    Returns:
        Deblurred image if blurry, otherwise original image
    """
    is_blurry, score = detect_blur(img)
    if not is_blurry:
        return img

    gaussian = cv2.GaussianBlur(img, (9, 9), 10.0)
    deblurred = cv2.addWeighted(img, 1.5, gaussian, -0.5, 0)
    Log.log.info(f"Deblurred image (blur score={score:.2f})")
    return deblurred


def force_white_background(img: np.ndarray) -> np.ndarray:
    """
    Convert image background to white using thresholding.

    Args:
        img: Input image (BGR format)

    Returns:
        Image with white background
    """
    gray = safe_to_gray(img)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    white_bg = np.ones_like(img, dtype=np.uint8) * 255
    white_bg[mask == 0] = img[mask == 0]
    return white_bg


def preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
    """
    Quick preprocessing pipeline for OCR.

    Args:
        img: Input image

    Returns:
        Preprocessed binary image
    """
    img = force_white_background(img)
    img = conditional_deblur(img)
    gray = safe_to_gray(img)
    gray = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return gray


def preprocess_crop(crop: np.ndarray) -> np.ndarray:
    """
    Preprocess individual text region crops for Tesseract OCR.

    Args:
        crop: Cropped text region image

    Returns:
        Preprocessed binary image
    """
    gray = safe_to_gray(crop)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )


def ensure_bgr(img: np.ndarray) -> np.ndarray:
    """
    Ensure image is in BGR format (OpenCV's default).

    Args:
        img: Input image in various formats

    Returns:
        BGR image

    Raises:
        ValueError: If image format is unsupported
    """
    if len(img.shape) == 2:  # grayscale → BGR
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 1:  # single channel
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 3:  # already BGR
        return img
    elif len(img.shape) == 3 and img.shape[2] == 4:  # has alpha channel
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        raise ValueError(f"Unsupported image format: {img.shape}")


def preprocess_image(img: np.ndarray, debug: bool = False) -> np.ndarray:
    """
    Comprehensive preprocessing pipeline for robust OCR.
    Handles glare, blur, shadows, and uneven lighting.

    Args:
        img: Input image
        debug: If True, save intermediate processing steps

    Returns:
        Preprocessed binary image optimized for OCR
    """
    # Ensure BGR format
    img = ensure_bgr(img)
    img = force_white_background(img)
    img = conditional_deblur(img)

    # 1. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Denoise (helps with compression artifacts or mobile blur)
    gray = cv2.fastNlMeansDenoising(gray, h=30)

    # 3. Remove uneven lighting (morphological background subtraction)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    norm = cv2.divide(gray, background, scale=255)

    # 4. Sharpen (helps recover blurred edges from mobile captures)
    sharpen_kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])
    sharp = cv2.filter2D(norm, -1, sharpen_kernel)

    # 5. Adaptive threshold (good for mixed lighting)
    thresh = cv2.adaptiveThreshold(
        sharp, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 15
    )

    # 6. Optional – invert if white text on dark background
    white_pixels = np.sum(thresh == 255)
    black_pixels = np.sum(thresh == 0)
    if black_pixels > white_pixels:  # mostly dark
        thresh = cv2.bitwise_not(thresh)
        Log.log.info("Inverted image (white text on dark background detected)")

    if debug:
        cv2.imwrite("debug_1_gray.png", gray)
        cv2.imwrite("debug_2_norm.png", norm)
        cv2.imwrite("debug_3_sharp.png", sharp)
        cv2.imwrite("debug_4_thresh.png", thresh)
        Log.log.info("Debug images saved")

    return thresh


def is_low_contrast(image: np.ndarray, threshold: float = None) -> bool:
    """
    Check if image has low contrast.

    Args:
        image: Input image (BGR format)
        threshold: Minimum contrast threshold, uses config if None

    Returns:
        True if image has low contrast, False otherwise
    """
    if threshold is None:
        threshold = config.LOW_CONTRAST_THRESHOLD

    gray = safe_to_gray(image)
    min_value, max_value = gray.min(), gray.max()
    return (max_value - min_value) < threshold


def is_low_resolution(img: np.ndarray, min_height: int = None) -> bool:
    """
    Check if image resolution is too low for reliable OCR.

    Args:
        img: Input image
        min_height: Minimum acceptable height in pixels, uses config if None

    Returns:
        True if resolution is too low, False otherwise
    """
    if min_height is None:
        min_height = config.MIN_RESOLUTION_HEIGHT

    return img.shape[0] < min_height


def validate(img: np.ndarray) -> Tuple[bool, str]:
    """
    Validate image quality for OCR processing.

    Args:
        img: Input image to validate

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    # Check for blur
    is_blurry, blur_score = detect_blur(img)
    if is_blurry:
        return False, f"Image is too blurry (focus score = {blur_score:.2f})"

    # Check for low contrast
    if is_low_contrast(img):
        return False, "Image has low contrast - please provide a clearer image"

    # Check resolution
    if is_low_resolution(img):
        return False, f"Image resolution too low (height: {img.shape[0]}px) - please upload a higher resolution image"

    return True, "Image quality validated successfully"


def run_paddle_ocr(
    img: np.ndarray,
    use_superres: bool = None,
    use_deskew: bool = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Run PaddleOCR on the given image with preprocessing.

    Args:
        img: Input image as numpy array
        use_superres: Apply super-resolution (uses config default if None)
        use_deskew: Apply deskewing (uses config default if None)
        debug: Save intermediate processing steps

    Returns:
        Dictionary with keys:
            - success (bool): Whether OCR succeeded
            - message (str): Status message
            - lines (list): List of detected text lines with confidence scores
    """
    try:
        # Use config defaults if not specified
        if use_superres is None:
            use_superres = config.USE_SUPER_RESOLUTION
        if use_deskew is None:
            use_deskew = config.USE_DESKEW

        # 1. Optional super-resolution
        if use_superres:
            img = super_resolve(img, debug=debug)

        # 2. Validate image quality
        valid, msg = validate(img)
        if not valid:
            Log.log.warning(f"Image validation failed: {msg}")
            return {"success": False, "message": msg, "lines": []}

        # 3. Preprocess image
        img = preprocess_image(img, debug=debug)

        # 4. Optional deskewing
        if use_deskew:
            img = deskew_image(img)

        # 5. Ensure BGR format for PaddleOCR
        img = ensure_bgr(img)

        # 6. Run PaddleOCR
        results = ocr.ocr(img, cls=True)
        if not results or not results[0]:
            Log.log.info("PaddleOCR returned no results")
            return {"success": False, "message": "No text detected in image", "lines": []}

        # 7. Process OCR results
        paddle_lines = []
        for line in results[0]:
            box = line[0]
            text, conf = line[1]

            # Extract bounding box coordinates
            x_min = int(min(pt[0] for pt in box))
            x_max = int(max(pt[0] for pt in box))
            y_min = int(min(pt[1] for pt in box))
            y_max = int(max(pt[1] for pt in box))

            # Crop text region
            cropped = img[y_min:y_max, x_min:x_max]

            # Skip invalid crops
            if cropped.size == 0 or cropped.shape[0] < 5 or cropped.shape[1] < 5:
                continue

            # Preprocess crop for Tesseract refinement
            processed_crop = preprocess_crop(cropped)
            paddle_lines.append({
                "text": text.strip(),
                "conf": conf,
                "crop": processed_crop
            })
            Log.log.info(f"PaddleOCR detected: '{text.strip()}' (confidence={conf:.2f})")

        if not paddle_lines:
            return {"success": False, "message": "No valid text found", "lines": []}

        Log.log.info(f"PaddleOCR extracted {len(paddle_lines)} text lines")
        return {"success": True, "message": "Text extracted successfully", "lines": paddle_lines}

    except Exception as e:
        Log.log.error(f"PaddleOCR failed: {e}", exc_info=True)
        return {"success": False, "message": f"OCR failed: {str(e)}", "lines": []}


def run_tesseract_on_low_conf(paddle_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Refine low-confidence PaddleOCR results using Tesseract.

    Args:
        paddle_lines: List of dictionaries containing PaddleOCR results
                     Each dict has keys: text, conf, crop

    Returns:
        Dictionary with keys:
            - success (bool): Whether refinement succeeded
            - message (str): Status message
            - lines (str): Refined text as multi-line string
    """
    merged_lines = []
    tesseract_config = r"--oem 3 --psm 6"

    for line in paddle_lines:
        text = line["text"]
        conf = line["conf"]
        crop = line["crop"]

        # If confidence is high, keep PaddleOCR result as-is
        if conf >= CONFIDENCE_THRESHOLD:
            merged_lines.append(text)
            continue

        # Try Tesseract for low-confidence results
        try:
            t_text = pytesseract.image_to_string(
                crop,
                lang="eng",
                config=tesseract_config
            ).strip()

            # Calculate similarity between PaddleOCR and Tesseract results
            similarity = lev_ratio(t_text, text) if t_text else 0

            # Decide which text to keep based on similarity and length
            if t_text and (similarity >= 0.85 or len(t_text) > len(text) + 3):
                merged_lines.append(t_text)
                Log.log.info(f"Tesseract refinement: '{text}' → '{t_text}'")
            else:
                # Keep original if Tesseract result is unreliable
                merged_lines.append(text)
                Log.log.info(f"Kept PaddleOCR result: '{text}' (conf={conf:.2f})")

        except Exception as e:
            Log.log.warning(f"Tesseract refinement failed for '{text}': {e}")
            merged_lines.append(text)

    # Post-process all lines
    cleaned_text = "\n".join(postprocess_text(merged_lines))
    return {
        "success": True,
        "message": "Text extraction and refinement completed",
        "lines": cleaned_text
    }


def postprocess_text(lines: List[str]) -> List[str]:
    """
    Clean and fix common OCR errors in text lines.

    Args:
        lines: List of text lines to clean

    Returns:
        List of cleaned text lines
    """
    cleaned = []
    for line in lines:
        txt = line

        # Common OCR character fixes
        txt = txt.replace("I1em", "Item")
        txt = txt.replace("0CR", "OCR")
        txt = txt.replace("$ ", "$")
        txt = txt.replace(" - ", "-")
        txt = txt.replace("l0", "10")  # lowercase L to digit
        txt = txt.replace("O0", "00")  # Letter O to digit

        # Strip whitespace
        txt = txt.strip()

        if txt:
            cleaned.append(txt)

    return cleaned
