"""
Configuration management for ImageOCR application.
Handles environment variables and default settings.
"""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration class for ImageOCR application."""

    # Application settings
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "3000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Paths
    BASE_DIR: Path = Path(__file__).parent
    INPUT_DIR: Path = BASE_DIR / "Input"
    OUTPUT_DIR: Path = BASE_DIR / "Output"
    MODELS_DIR: Path = BASE_DIR / "models"

    # Tesseract Configuration
    TESSERACT_PATH: str = os.getenv(
        "TESSERACT_PATH",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    # Poppler Configuration (for PDF processing)
    POPPLER_PATH: str = os.getenv(
        "POPPLER_PATH",
        r"C:\Program Files\poppler-25.07.0\Library\bin"
    )

    # Google Vision API
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0"))
    OPENAI_MAX_RETRIES: int = int(os.getenv("OPENAI_MAX_RETRIES", "3"))

    # PaddleOCR Model Paths
    PADDLE_DET_MODEL: str = os.getenv(
        "PADDLE_DET_MODEL",
        "models/en_PP-OCRv3_det_infer"
    )
    PADDLE_REC_MODEL: str = os.getenv(
        "PADDLE_REC_MODEL",
        "models/en_PP-OCRv4_rec_infer"
    )
    PADDLE_CLS_MODEL: str = os.getenv(
        "PADDLE_CLS_MODEL",
        "models/ch_ppocr_mobile_v2.0_cls_infer"
    )

    # Super Resolution Model
    SUPER_RES_MODEL: str = os.getenv("SUPER_RES_MODEL", "FSRCNN_x4.pb")

    # OCR Settings
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
    USE_SUPER_RESOLUTION: bool = os.getenv("USE_SUPER_RESOLUTION", "True").lower() == "true"
    USE_DESKEW: bool = os.getenv("USE_DESKEW", "True").lower() == "true"

    # Cache Settings
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    CACHE_TYPE: str = os.getenv("CACHE_TYPE", "file")  # file, redis, memory
    CACHE_DIR: Path = BASE_DIR / "cache"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "86400"))  # 24 hours in seconds

    # Redis Configuration (if using Redis cache)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "log.txt")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10 MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Video Processing
    VIDEO_FRAME_INTERVAL_SEC: int = int(os.getenv("VIDEO_FRAME_INTERVAL_SEC", "1"))

    # PDF Processing
    PDF_BATCH_SIZE: int = int(os.getenv("PDF_BATCH_SIZE", "5"))

    # Excel Processing
    EXCEL_CHUNK_SIZE: int = int(os.getenv("EXCEL_CHUNK_SIZE", "1000"))

    # Keyword Extraction
    KEYWORD_TOP_N: int = int(os.getenv("KEYWORD_TOP_N", "100"))

    # Image Validation
    BLUR_THRESHOLD: float = float(os.getenv("BLUR_THRESHOLD", "100.0"))
    MIN_RESOLUTION_HEIGHT: int = int(os.getenv("MIN_RESOLUTION_HEIGHT", "500"))
    LOW_CONTRAST_THRESHOLD: float = float(os.getenv("LOW_CONTRAST_THRESHOLD", "15.0"))

    # CORS Settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    # File Upload Settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50 MB
    ALLOWED_EXTENSIONS: set = {
        "png", "jpg", "jpeg", "tiff", "bmp", "gif", "webp",  # Images
        "mp4", "avi", "mov", "mkv",  # Videos
        "pdf", "docx", "xlsx", "xls", "csv", "txt"  # Documents
    }

    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration settings."""
        errors = []

        # Check if Tesseract exists
        if not os.path.exists(cls.TESSERACT_PATH):
            errors.append(f"Tesseract not found at: {cls.TESSERACT_PATH}")

        # Check if OpenAI API key is set (if needed)
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY not set in environment variables")

        # Create necessary directories
        for directory in [cls.INPUT_DIR, cls.OUTPUT_DIR, cls.CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

        if errors:
            for error in errors:
                print(f"Configuration Warning: {error}")
            return False

        return True

config = Config()
