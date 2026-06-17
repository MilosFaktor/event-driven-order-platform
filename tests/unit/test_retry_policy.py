from app.core.config import Settings
from app.models.order import Order
from app.workflows.worker_service import WorkerService


class FakeQueueService:
    def __init__(self, order_id: str | None = None):
        self.items = [order_id] if order_id is not None else []

    def get_first_queue_item(self):
        return self.items[0] if self.items else None

    def dequeue_order(self):
        return self.items.pop(0)

    def not_queue_empty(self):
        return bool(self.items)


class FakeOrderPipelineService:
    def process_order(self, order_id) -> Order | None:
        return None


def test_retry_delay_uses_exponential_backoff():
    settings = Settings(
        max_processing_attempts=4,
        retry_base_delay_seconds=1,
        retry_backoff_multiplier=2,
    )

    worker = WorkerService(
        settings=settings,
        queue_service=FakeQueueService(),
        order_pipeline_service=FakeOrderPipelineService(),
    )

    assert worker.calculate_retry_delay_seconds(1) == 1
    assert worker.calculate_retry_delay_seconds(2) == 2
    assert worker.calculate_retry_delay_seconds(3) == 4
