import logging
import sys

from app.core.config import settings


def configure_logging_api():
    configure_root_logger()
    configure_api_logger()


def configure_logging_worker():
    configure_root_logger()
    configure_worker_logger()


def configure_root_logger():
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def configure_api_logger():
    logger = logging.getLogger("api")

    if logger.handlers:
        return

    logger.setLevel(settings.log_level)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | API | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)


def configure_worker_logger():
    logger = logging.getLogger("worker.runtime")

    if logger.handlers:
        return

    logger.setLevel(settings.log_level)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | WORKER | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger(name):
    return logging.getLogger(name)
