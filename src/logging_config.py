"""Logging configuration for PriceRadar."""
import logging
import logging.handlers
from pathlib import Path

# Create logs directory
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler for API
api_file_handler = logging.handlers.RotatingFileHandler(
    LOG_DIR / "api.log",
    maxBytes=10485760,  # 10MB
    backupCount=5,
)
api_file_handler.setLevel(logging.INFO)
api_file_handler.setFormatter(console_formatter)

# File handler for pipeline
pipeline_file_handler = logging.handlers.RotatingFileHandler(
    LOG_DIR / "pipeline.log",
    maxBytes=10485760,  # 10MB
    backupCount=5,
)
pipeline_file_handler.setLevel(logging.INFO)
pipeline_file_handler.setFormatter(console_formatter)

# File handler for errors
error_file_handler = logging.handlers.RotatingFileHandler(
    LOG_DIR / "errors.log",
    maxBytes=10485760,  # 10MB
    backupCount=5,
)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(console_formatter)

logger.addHandler(api_file_handler)
logger.addHandler(pipeline_file_handler)
logger.addHandler(error_file_handler)

# Set specific loggers
logging.getLogger("src.api").setLevel(logging.INFO)
logging.getLogger("src.pipeline").setLevel(logging.INFO)
logging.getLogger("src.models").setLevel(logging.INFO)
logging.getLogger("src.analytics").setLevel(logging.INFO)
logging.getLogger("src.scrapers").setLevel(logging.INFO)

# Suppress verbose third-party loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
