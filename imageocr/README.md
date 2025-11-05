
# 📝 ImageOCR – Multi-format Intelligent OCR Pipeline

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95-green)](https://fastapi.tiangolo.com/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.6-orange)](https://github.com/PaddlePaddle/PaddleOCR)

**ImageOCR** is a production-ready Python OCR framework for extracting text from images, videos, PDFs, DOCX, Excel, and CSV/TXT files.  
It combines **FastAPI**, **PaddleOCR**, and **Tesseract** with advanced image preprocessing, caching, and keyword extraction for high accuracy.

---

## 🚀 Key Features

- 🖼 **Multi-format Support:**  
  Images (`png/jpg/jpeg/tiff/bmp/gif/webp`), Videos (`mp4/avi/mov/mkv`), PDFs, DOCX, Excel (`xls/xlsx`), CSV, TXT

- ✨ **Advanced Image Preprocessing:**  
  Super-resolution, deskewing, blur detection & correction, white background enforcement, adaptive thresholding

- 🔍 **Robust OCR Pipeline:**  
  PaddleOCR → Tesseract for low-confidence refinement

- 🗝 **Keyword Extraction:**  
  RAKE + NLTK integration for automatic keyword generation

- 💾 **Caching System:**  
  Avoid redundant OCR for repeated images

- 📊 **Logging:**  
  Rotating file logger with UTF-8 support

---

## ⚙️ Installation

1. **Clone the repository:**

```bash
git clone https://github.com/YourUsername/ImageOCR.git
cd ImageOCR
````

2. **Create a virtual environment and activate it:**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Install Tesseract OCR & Poppler for PDF processing.**

5. **Download PaddleOCR models** (if not included in `models/`).

---

## 🖥 Usage

### Start the FastAPI server:

```bash
uvicorn app:app --host 0.0.0.0 --port 3000 --reload
```

### API Endpoint

**POST** `/api/upload`

* Accepts multi-format files: image, pdf, docx, xlsx, csv, txt, video
* Returns extracted text with success status and message

### Python Example

```python
from utils import extract_text_sync

with open("Input/sample.pdf", "rb") as f:
    content = f.read()

text = extract_text_sync(content, "sample.pdf")
print(text)
```

---

## 📂 Project Structure

```
ImageOCR/
├─ app.py                # FastAPI application & routes
├─ log.py                # Rotating logger
├─ openai_client.py      # Async OpenAI API wrapper with retries
├─ utils.py              # OCR pipeline & multi-format extraction
├─ image.py              # Image preprocessing & PaddleOCR/Tesseract
├─ models/               # PaddleOCR models
├─ Input/                # Example input files
├─ Output/               # Extracted results
├─ requirements.txt      # Python dependencies
├─ .gitignore
└─ log.txt               # Rotating logs
```

---

## ⚠️ Notes & Recommendations

* Use **Git LFS** for files >100MB
* Confirm Tesseract and Poppler paths are correct
* This OCR workflow is production-ready with advanced preprocessing and caching
* The system handles low-confidence OCR by combining PaddleOCR + Tesseract refinement

---

## 📖 References

* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
* [RAKE + NLTK](https://pypi.org/project/rake-nltk/)

---

✅ **Next Steps:**

1. Save this content as `README.md` in the project root.
2. Commit and push to GitHub:

```bash
git add README.md
git commit -m "Add polished README"
git push
```

```


