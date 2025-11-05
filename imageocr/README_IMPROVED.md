# 📝 ImageOCR v2.0 – Intelligent Multi-Format OCR Pipeline

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.7-orange)](https://github.com/PaddlePaddle/PaddleOCR)

**ImageOCR v2.0** is a production-ready, enterprise-grade Python OCR framework for extracting text from images, videos, PDFs, DOCX, Excel, CSV files, and more. This improved version features enhanced configuration management, persistent caching, comprehensive type hints, improved error handling, and extensive documentation.

---

## 🚀 What's New in v2.0

### Major Improvements

- **🔧 Configuration Management**: Centralized configuration system using environment variables
- **💾 Persistent File-Based Cache**: Intelligent caching with TTL support to avoid redundant OCR processing
- **📝 Type Hints**: Complete type annotations throughout the codebase for better IDE support
- **🛡️ Enhanced Error Handling**: Comprehensive exception handling with detailed logging
- **📖 Documentation**: Extensive docstrings and improved README
- **🔧 Bug Fixes**: Fixed typos (is_resoultion → is_low_resolution) and improved code quality
- **🎯 Better Validation**: Improved image quality validation with configurable thresholds
- **⚡ Performance**: Optimized async operations and batch processing

---

## ✨ Key Features

### Multi-Format Support
- 🖼️ **Images**: PNG, JPG, JPEG, TIFF, BMP, GIF, WebP
- 🎬 **Videos**: MP4, AVI, MOV, MKV
- 📄 **Documents**: PDF, DOCX
- 📊 **Spreadsheets**: XLS, XLSX
- 📝 **Text**: CSV, TXT

### Advanced Image Processing
- Super-resolution enhancement (4x upscaling)
- Automatic deskewing and rotation correction
- Blur detection and adaptive deblurring
- White background enforcement
- Adaptive thresholding for various lighting conditions
- Shadow and glare removal

### Robust OCR Pipeline
- **PaddleOCR** for initial text detection
- **Tesseract OCR** for low-confidence refinement
- Levenshtein distance-based result merging
- Common OCR error correction

### Intelligent Features
- Persistent file-based caching with TTL
- RAKE + NLTK keyword extraction
- Configurable quality validation
- Comprehensive logging with rotation
- RESTful API with FastAPI

---

## ⚙️ Installation

### Prerequisites

1. **Python 3.10+**
2. **Tesseract OCR**
   - Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt install tesseract-ocr`
   - macOS: `brew install tesseract`

3. **Poppler** (for PDF processing)
   - Windows: [Download Poppler](https://github.com/oschwartz10612/poppler-windows/releases)
   - Linux: `sudo apt install poppler-utils`
   - macOS: `brew install poppler`

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/Amosprakash/ImageOCR.git
cd ImageOCR
```

2. **Create a virtual environment:**
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

4. **Configure environment variables:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

5. **Update configuration:**
Edit `.env` file with your paths:
```env
# Paths (adjust for your OS)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\Program Files\poppler-25.07.0\Library\bin

# OpenAI API (required for GPT features)
OPENAI_API_KEY=your-api-key-here

# Optional: Google Cloud Vision
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

---

## 🖥️ Usage

### Start the FastAPI Server

```bash
uvicorn app:app --host 0.0.0.0 --port 3000 --reload
```

Or use the built-in runner:
```bash
python app.py
```

### API Endpoints

#### POST `/api/upload`

Upload files for text extraction.

**Parameters:**
- `files`: List of files (multipart/form-data)
- `question`: Question to ask about the content (string)

**Supported File Types:**
- Images: png, jpg, jpeg, tiff, bmp, gif, webp
- Videos: mp4, avi, mov, mkv
- Documents: pdf, docx
- Spreadsheets: xls, xlsx
- Text: csv, txt

**Example using cURL:**
```bash
curl -X POST "http://localhost:3000/api/upload" \
  -F "files=@document.pdf" \
  -F "files=@image.png" \
  -F "question=Extract all invoice details"
```

**Example using Python:**
```python
import requests

url = "http://localhost:3000/api/upload"
files = [
    ("files", open("invoice.pdf", "rb")),
    ("files", open("receipt.jpg", "rb"))
]
data = {"question": "What is the total amount?"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response:**
```json
{
  "answer": "The total amount is $1,234.56"
}
```

### Python Library Usage

```python
from utils import extract_text_sync

# Extract text from a file
with open("Input/sample.pdf", "rb") as f:
    content = f.read()

text = extract_text_sync(content, "sample.pdf")
print(text)
```

---

## 📂 Project Structure

```
ImageOCR/
├── app.py                # FastAPI application & routes
├── config.py             # Configuration management
├── log.py                # Logging configuration
├── image.py              # Image preprocessing & OCR
├── utils.py              # Multi-format extraction utilities
├── upload.py             # Upload endpoint handlers
├── openai_client.py      # OpenAI API integration
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your local configuration (git-ignored)
├── .gitignore            # Git ignore rules
├── models/               # PaddleOCR models
├── Input/                # Example input files
├── Output/               # Extracted results
├── cache/                # OCR cache directory
└── README.md             # This file
```

---

## ⚙️ Configuration

All configuration is managed through environment variables (`.env` file) or can be set directly in `config.py`.

### Key Configuration Options

```python
# Application
APP_HOST=0.0.0.0          # Server host
APP_PORT=3000             # Server port
DEBUG=False               # Debug mode

# OCR Settings
CONFIDENCE_THRESHOLD=0.75   # OCR confidence threshold
USE_SUPER_RESOLUTION=True   # Enable super-resolution
USE_DESKEW=True            # Enable deskewing

# Cache Settings
ENABLE_CACHE=True          # Enable OCR caching
CACHE_TYPE=file            # Cache type (file/redis/memory)
CACHE_TTL=86400           # Cache TTL in seconds (24 hours)

# Image Validation
BLUR_THRESHOLD=100.0       # Blur detection threshold
MIN_RESOLUTION_HEIGHT=500  # Minimum image height
LOW_CONTRAST_THRESHOLD=15.0 # Contrast threshold

# Processing
VIDEO_FRAME_INTERVAL_SEC=1  # Video frame sampling interval
PDF_BATCH_SIZE=5           # PDF batch processing size
EXCEL_CHUNK_SIZE=1000      # Excel chunk size
KEYWORD_TOP_N=100          # Number of keywords to extract
```

---

## 🔍 Advanced Features

### Image Quality Validation

The system automatically validates image quality before OCR:
- **Blur Detection**: Using Laplacian variance
- **Contrast Analysis**: Ensuring sufficient contrast
- **Resolution Check**: Minimum resolution requirements

### Intelligent Caching

Files are cached based on content hash (MD5):
- **Persistent Storage**: Survives application restarts
- **TTL Support**: Automatic expiration of old entries
- **Cache Invalidation**: Smart cache management

### Hybrid OCR Approach

1. **PaddleOCR**: Initial text detection with high accuracy
2. **Tesseract**: Refinement of low-confidence results
3. **Levenshtein Matching**: Intelligent result merging
4. **Post-processing**: Common OCR error correction

---

## 🛠️ Troubleshooting

### Common Issues

**1. Tesseract not found**
```
Solution: Install Tesseract and update TESSERACT_PATH in .env
```

**2. Poppler not found (PDF processing fails)**
```
Solution: Install Poppler and update POPPLER_PATH in .env
```

**3. PaddleOCR model not found**
```
Solution: Models will be downloaded automatically on first run
Ensure you have internet connection and sufficient disk space
```

**4. Out of memory errors**
```
Solution: Reduce batch sizes in config:
- PDF_BATCH_SIZE=2
- EXCEL_CHUNK_SIZE=500
```

**5. Slow OCR performance**
```
Solution:
- Disable super-resolution: USE_SUPER_RESOLUTION=False
- Enable caching: ENABLE_CACHE=True
- Use smaller images
```

---

## 📊 Performance Tips

1. **Enable Caching**: Significantly faster for repeated files
2. **Adjust Image Size**: Resize very large images before OCR
3. **Batch Processing**: Process multiple files in parallel
4. **Disable Debug Mode**: Set DEBUG=False in production
5. **Use Super-Resolution Wisely**: Only for low-resolution images

---

## 🧪 Testing

```bash
# Install development dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

---

## 📖 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:3000/docs
- **ReDoc**: http://localhost:3000/redoc

---

## 🔐 Security

- API keys and credentials should be in `.env` (never committed to Git)
- Use environment-specific `.env` files
- Consider rate limiting for production deployments
- Validate file types and sizes before processing

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - Deep learning OCR toolkit
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Open source OCR engine
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [RAKE-NLTK](https://pypi.org/project/rake-nltk/) - Keyword extraction

---

## 📞 Support

For issues and questions:
- Create an issue on [GitHub](https://github.com/Amosprakash/ImageOCR/issues)
- Check existing issues for solutions

---

## 🗺️ Roadmap

- [ ] Redis cache support
- [ ] Batch processing API
- [ ] WebSocket support for real-time OCR
- [ ] Multi-language OCR support
- [ ] Cloud storage integration (S3, Azure Blob)
- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] Performance benchmarks
- [ ] Unit and integration tests

---

**Made with ❤️ by the ImageOCR Team**
