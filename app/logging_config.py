import logging
import sys


def configure_logging():
    configure_root_logger()
    configure_api_logger()
    configure_worker_logger()


def configure_root_logger():
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def configure_api_logger():
    logger = logging.getLogger("api")

    if logger.handlers:
        return

    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | API | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)


def configure_worker_logger():
    logger = logging.getLogger("worker")

    if logger.handlers:
        return

    logger.setLevel(logging.INFO)
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
