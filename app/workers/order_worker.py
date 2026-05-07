import time

from app.core import config
from app.core.logging_config import configure_logging_worker, get_logger
from app.services.queue_service import not_queue_empty
from app.services.worker_service import process_next_order

configure_logging_worker()
logger = get_logger("worker")


def worker_server():
    seconds = 0
    while True:
        if not_queue_empty():
            logger.info("Work registered in queue")
            process_next_order()

        logger.info("[%s] Seconds running ...", seconds)

        seconds += config.QUEUE_INTERVAL
        time.sleep(config.QUEUE_INTERVAL)


def main():
    logger.info("Worker started")
    worker_server()


if __name__ == "__main__":
    main()
