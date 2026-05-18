from app.core.logging_config import get_logger
from app.models.order import Order

logger = get_logger("payment.service")


class PaymentService:
    def mark_payment_captured(self, order):
        order.steps.payment = "CAPTURED"
        logger.debug("order_payment_step_updated order_id=%s", order.order_id)

    def capture_payment_mock(self, order: Order) -> None:
        # payment mock
        self.mark_payment_captured(order)
        logger.info("payment_captured order_id=%s", order.order_id)
