import time

from app import config
from app.logging_config import configure_logging, get_logger
from app.services.order_service import process_order
from app.services.queue_service import (
    dequeue_order,
    not_queue_empty,
)

logger = get_logger("worker")


def process_next_order():
    order_id = dequeue_order()
    if order_id is None:
        return None
    return process_order(order_id)


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
    configure_logging()
    logger.info("Worker started")
    worker_server()


if __name__ == "__main__":
    main()
