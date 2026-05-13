from app.adapters.json_queue_adapter import JsonProcessingQueueAdapter
from app.core.logging_config import get_logger
from app.models.processing_queue import ProcessingQueue

logger = get_logger("processing_queue.repo")


class ProcessingQueueRepository:
    def __init__(self, adapter: JsonProcessingQueueAdapter | None = None):
        if adapter is None:
            self.adapter = JsonProcessingQueueAdapter()
        else:
            self.adapter = adapter

    def list_processing_queue(self) -> ProcessingQueue:
        queue = self.adapter.load_processing_queue()
        logger.debug("processing_queue_loaded count=%s", len(queue.root))

        return queue

    def save_processing_queue(self, queue: ProcessingQueue) -> None:
        self.adapter.save_processing_queue(queue)
        logger.debug("processing_queue_saved count=%s", len(queue.root))
