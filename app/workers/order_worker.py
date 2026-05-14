import time

from app.core.config import settings
from app.core.dependencies import app_dependencies as deps
from app.core.logging_config import configure_logging_worker, get_logger

configure_logging_worker()
logger = get_logger("worker.runtime")


worker_service = deps.worker_service()


def worker_server():
    seconds = 0
    while True:
        if worker_service.has_work():
            logger.info("queue_work_detected")
            worker_service.process_next_order()

        logger.debug("worker_heartbeat seconds=%s", seconds)

        seconds += settings.queue_interval
        time.sleep(settings.queue_interval)


def main():
    logger.info("worker_started")
    worker_server()


if __name__ == "__main__":
    main()
