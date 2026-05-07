from app.core.logging_config import get_logger
from app.services.order_service import process_order
from app.services.queue_service import dequeue_order

logger = get_logger(__name__)


def process_next_order():
    order_id = dequeue_order()
    if order_id is None:
        return None
    return process_order(order_id)
