import time

from app.core.config import settings
from app.core.logging_config import configure_logging_worker, get_logger
from app.services.queue_service import ProcessingQueueService
from app.services.worker_service import process_next_order

configure_logging_worker()
logger = get_logger("worker.runtime")

queue_service = ProcessingQueueService()


def worker_server():
    seconds = 0
    while True:
        if queue_service.not_queue_empty():
            logger.info("queue_work_detected")

            process_next_order()

        logger.debug("worker_heartbeat seconds=%s", seconds)

        seconds += settings.queue_interval
        time.sleep(settings.queue_interval)


def main():
    logger.info("worker_started")
    worker_server()


if __name__ == "__main__":
    main()
