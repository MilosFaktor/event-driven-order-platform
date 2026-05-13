from app.models.processing_queue import ProcessingQueue
from app.storage import json_storage

QUEUE_PATH = json_storage.STORAGE_PATHS["queue"]


class JsonProcessingQueueAdapter:
    def __init__(self, queue_path: str = QUEUE_PATH):
        self.queue_path = queue_path

    def load_processing_queue(self) -> ProcessingQueue:
        raw_queue = json_storage.load_json(self.queue_path)
        return ProcessingQueue.model_validate(raw_queue)

    def save_processing_queue(self, queue: ProcessingQueue) -> None:
        json_storage.save_json(self.queue_path, queue.model_dump())
