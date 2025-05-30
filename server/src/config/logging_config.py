import logging
import os
from pathlib import Path

from src.config.settings import settings


def setup_logging():
    LOG_FILE = os.getenv("LOG_FILE")
    log_handler = (
        logging.FileHandler(LOG_FILE)
        if LOG_FILE and Path(LOG_FILE).parent.exists()
        else logging.StreamHandler()
    )
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] [%(module)s:%(lineno)d] - %(message)s",
        handlers=[log_handler],
    )
    logger = logging.getLogger(__name__)

    logger.info(f"{settings.APP_NAME} API started. Debug mode: {settings.DEBUG}")
    logger.info(f"Output audio directory: {settings.OUTPUT_AUDIO_DIR}")
    logger.info(f"Input directory: {settings.INPUT_DIR}")
    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        logger.info(f"Using Google Credentials from: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
    else:
        logger.warning(
            "GOOGLE_APPLICATION_CREDENTIALS not set. Google Cloud services might not be available."
        )
    return logger


# Initialize logger when this module is imported
logger = setup_logging()
