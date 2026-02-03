import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FOLDER = Path(__file__).resolve().parent


def setup_logging():
    LOG_FOLDER.mkdir(exist_ok=True)

    root_logger = logging.getLogger()

    root_logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        f"{LOG_FOLDER}/log.log",
        maxBytes=5 * 1024 * 1024,
        encoding="utf-8",
    )
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
