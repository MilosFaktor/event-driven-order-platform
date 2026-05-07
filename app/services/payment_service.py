from app.core.logging_config import get_logger

logger = get_logger("payment.service")


def payment_captured_mock(order):
    # payment mock
    order["steps"]["payment"] = "CAPTURED"
    logger.info("payment_captured order_id=%s", order["order_id"])


def is_payment_captured(order):
    return order["steps"]["payment"] == "CAPTURED"
