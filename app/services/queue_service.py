from app.core.logging_config import get_logger
from app.models.processing_queue import ProcessingQueue
from app.repositories.processing_queue_repository import ProcessingQueueRepository

logger = get_logger("processing_queue.service")

repo = ProcessingQueueRepository()


def enqueue_order(order_id):
    queue: ProcessingQueue = repo.list_processing_queue()

    queue.root.append(order_id)

    repo.save_processing_queue(queue)
    logger.info("order_enqueued order_id=%s queue_depth=%s", order_id, len(queue.root))


def dequeue_order():
    queue: ProcessingQueue = repo.list_processing_queue()

    if queue_empty(queue):
        return None
    order_id = queue.root.pop(0)

    repo.save_processing_queue(queue)
    logger.debug("order_dequeued order_id=%s queue_depth=%s", order_id, len(queue.root))

    return order_id


def not_queue_empty():
    return bool(repo.list_processing_queue().root)


def queue_empty(queue: ProcessingQueue):
    return queue.root == []
