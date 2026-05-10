from app.core.logging_config import get_logger
from app.models.processing_queue import ProcessingQueue
from app.storage import json_storage

QUEUE_PATH = json_storage.STORAGE_PATHS["queue"]

logger = get_logger("queue.service")


def enqueue_order(order_id):
    queue: list[str] = get_processing_queue()

    queue.append(order_id)

    save_processing_queue(queue)
    logger.info("order_enqueued order_id=%s queue_depth=%s", order_id, len(queue))


def dequeue_order():
    queue = get_processing_queue()

    if queue_empty(queue):
        return None
    order_id = queue.pop(0)

    save_processing_queue(queue)
    logger.debug("order_dequeued order_id=%s queue_depth=%s", order_id, len(queue))

    return order_id


def get_processing_queue():
    raw_queue = json_storage.load_json(QUEUE_PATH)
    logger.debug("processing_queue_loaded count=%s", len(raw_queue))

    validated_queue = ProcessingQueue.model_validate(raw_queue)
    logger.debug(
        "processing_queue_validated_on_load count=%s", len(validated_queue.root)
    )

    return validated_queue.model_dump()


def save_processing_queue(queue):
    validated_queue = ProcessingQueue.model_validate(queue)
    logger.debug(
        "processing_queue_validated_before_save count=%s", len(validated_queue.root)
    )

    json_storage.save_json(QUEUE_PATH, validated_queue.model_dump())


def not_queue_empty():
    return bool(get_processing_queue())


def queue_empty(queue):
    return queue == []
