from app.core.logging_config import get_logger
from app.models.order import Order

logger = get_logger("payment.service")


class PaymentService:
    def capture_payment_mock(self, order: Order) -> None:
        # payment mock
        order.steps.payment = "CAPTURED"
        logger.info("payment_captured order_id=%s", order.order_id)

    def is_payment_captured(self, order: Order) -> bool:
        return order.steps.payment == "CAPTURED"
