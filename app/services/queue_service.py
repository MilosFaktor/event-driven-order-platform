from app.core.logging_config import get_logger
from app.models.processing_queue import ProcessingQueue
from app.repositories.processing_queue_repository import ProcessingQueueRepository

logger = get_logger("processing_queue.service")


class ProcessingQueueService:
    def __init__(self, repo: ProcessingQueueRepository | None = None):
        if repo is None:
            self.repo = ProcessingQueueRepository()
        else:
            self.repo = repo

    def enqueue_order(self, order_id: str) -> None:
        queue: ProcessingQueue = self.repo.list_processing_queue()

        queue.root.append(order_id)

        self.repo.save_processing_queue(queue)
        logger.info(
            "order_enqueued order_id=%s queue_depth=%s", order_id, len(queue.root)
        )

    def dequeue_order(self) -> str | None:
        queue: ProcessingQueue = self.repo.list_processing_queue()

        if self.queue_empty(queue):
            return None
        order_id = queue.root.pop(0)

        self.repo.save_processing_queue(queue)
        logger.debug(
            "order_dequeued order_id=%s queue_depth=%s", order_id, len(queue.root)
        )

        return order_id

    def list_processing_queue(self) -> ProcessingQueue:
        return self.repo.list_processing_queue()

    def get_first_queue_item(self) -> str | None:
        queue: ProcessingQueue = self.repo.list_processing_queue()
        if self.queue_empty(queue):
            return None
        return queue.root[0]

    def not_queue_empty(self) -> bool:
        return bool(self.repo.list_processing_queue().root)

    def queue_empty(self, queue: ProcessingQueue) -> bool:
        return queue.root == []
