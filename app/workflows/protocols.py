from typing import Protocol

from app.models.order import Order


class QueueServiceProtocol(Protocol):
    def get_first_queue_item(self) -> str | None: ...

    def dequeue_order(self) -> str | None: ...

    def not_queue_empty(self) -> bool: ...


class OrderPipelineProtocol(Protocol):
    def process_order(self, order_id) -> Order | None: ...
