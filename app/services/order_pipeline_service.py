from app.core.logging_config import get_logger
from app.services.inventory_service import InventoryService
from app.services.invoice_service import InvoiceService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.payment_service import is_payment_captured, payment_captured_mock

logger = get_logger("orders.pipeline")

order_service = OrderService()
inventory_service = InventoryService()
invoice_service = InvoiceService()
notification_service = NotificationService()


def mark_order_status(order, status):
    order.status = status
    logger.info(
        "order_status_changed order_id=%s status=%s",
        order.order_id,
        status,
    )


def mark_invoice_created(order):
    order.steps.invoice = "CREATED"
    logger.debug("order_invoice_step_updated order_id=%s", order.order_id)


def mark_notification_sent(order):
    order.steps.notification = "SENT"
    logger.debug(
        "order_notification_step_updated order_id=%s",
        order.order_id,
    )


def process_order(order_id):
    logger.info("order_processing_pipeline_started order_id=%s", order_id)

    order = order_service.get_order(order_id)

    if order is None:
        logger.warning("queued_order_not_found order_id=%s", order_id)
        return None

    if order_service.order_being_processed(order):
        logger.info("order_already_being_processed order_id=%s", order_id)
        return order

    if order_service.order_is_completed(order):
        logger.info("order_already_completed order_id=%s", order_id)
        return order

    mark_order_status(order, "PROCESSING")
    order_service.save_order(order)
    order_service.log_order_state(order)

    logger.info("inventory_reservation_started order_id=%s", order_id)
    inventory_service.reserve_inventory(order)
    order_service.save_order(order)
    order_service.log_order_state(order)

    if order_service.order_failed(order):
        logger.warning("inventory_reservation_failed order_id=%s", order_id)
        return order

    logger.info("payment_capture_started order_id=%s", order_id)
    payment_captured_mock(order)
    order_service.save_order(order)
    order_service.log_order_state(order)

    if is_payment_captured(order):
        logger.info("inventory_sale_finalization_started order_id=%s", order_id)
        inventory_service.finalize_inventory_sale(order)

        order_service.save_order(order)
        order_service.log_order_state(order)
    else:
        logger.warning("payment_capture_failed order_id=%s", order_id)
        mark_order_status(order, "FAILED")

        logger.info("inventory_release_started order_id=%s", order_id)
        inventory_service.release_order_inventory(order)

        order_service.save_order(order)
        order_service.log_order_state(order)

        return order

    if order_service.order_failed(order):
        logger.warning("inventory_sale_finalization_failed order_id=%s", order_id)
        return order

    logger.info("invoice_creation_started order_id=%s", order_id)
    invoice_service.create_invoice(order)

    mark_invoice_created(order)
    order_service.save_order(order)
    order_service.log_order_state(order)
    # what happens if invoice hasn't been created / solution retry logic

    logger.info("notification_send_started order_id=%s", order_id)
    notification_service.send_notification(order)
    mark_notification_sent(order)
    order_service.save_order(order)
    order_service.log_order_state(order)
    # what happens if notification hasn't been sent / solution retry logic

    mark_order_status(order, "COMPLETED")
    order_service.save_order(order)
    logger.info(
        "order_processing_pipeline_finished order_id=%s status=COMPLETED", order_id
    )
    order_service.log_order_state(order)

    return order
