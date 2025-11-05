"""
Logging configuration for ImageOCR application.
Provides rotating file and console logging with UTF-8 support.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
from config import config

LogFile = config.LOG_FILE
log = logging.getLogger("imageocr_logger")

# Set log level from config
log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
log.setLevel(log_level)

# --- File handler (UTF-8 safe) ---
file_handler = RotatingFileHandler(
    LogFile,
    maxBytes=config.LOG_MAX_BYTES,
    backupCount=config.LOG_BACKUP_COUNT,
    encoding="utf-8"
)

# --- Console handler (force UTF-8) ---
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setStream(sys.stdout)  # stdout is safer for UTF-8
try:
    console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
except Exception as e:
    print("Console logging setup failed:", e)

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(console_handler)
