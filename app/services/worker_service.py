from app.core.dependencies import app_dependencies as deps
from app.core.logging_config import get_logger
from app.services.order_pipeline_service import process_order

logger = get_logger("worker.service")

queue_service = deps.queue_service()


def process_next_order():
    order_id = queue_service.dequeue_order()
    logger.info("order_dequeued order_id=%s", order_id)
    if order_id is None:
        logger.warning("no_order_to_process")
        return None
    logger.info("order_processing_started order_id=%s", order_id)
    processed_order = process_order(order_id)
    logger.info("order_processing_finished order_id=%s", order_id)

    return processed_order
