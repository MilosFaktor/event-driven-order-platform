from app.core.logging_config import get_logger
from app.services.inventory_service import (
    finalize_inventory_sale,
    release_order_inventory,
    reserve_inventory,
)
from app.services.invoice_service import create_invoice
from app.services.notification_service import send_notification
from app.services.order_service import (
    get_orders,
    log_order_state,
    order_being_processed,
    order_failed,
    order_is_completed,
    save_order,
)
from app.services.payment_service import is_payment_captured, payment_captured_mock

logger = get_logger("orders.pipeline")


def mark_order_status(order, status):
    order["status"] = status
    logger.info(
        "order_status_changed order_id=%s status=%s",
        order["order_id"],
        status,
    )


def mark_invoice_created(order):
    order["steps"]["invoice"] = "CREATED"
    logger.debug("order_invoice_step_updated order_id=%s", order["order_id"])


def mark_notification_sent(order):
    order["steps"]["notification"] = "SENT"
    logger.debug(
        "order_notification_step_updated order_id=%s",
        order["order_id"],
    )


def process_order(order_id):
    logger.info("order_processing_pipeline_started order_id=%s", order_id)
    orders = get_orders()
    order = orders[order_id]

    if order_being_processed(order):
        logger.info("order_already_being_processed order_id=%s", order_id)
        return order

    if order_is_completed(order):
        logger.info("order_already_completed order_id=%s", order_id)
        return order

    mark_order_status(order, "PROCESSING")
    save_order(order)
    log_order_state(order)

    logger.info("inventory_reservation_started order_id=%s", order_id)
    reserve_inventory(order)
    save_order(order)
    log_order_state(order)

    if order_failed(order):
        logger.warning("inventory_reservation_failed order_id=%s", order_id)
        return order

    logger.info("payment_capture_started order_id=%s", order_id)
    payment_captured_mock(order)
    save_order(order)
    log_order_state(order)

    if is_payment_captured(order):
        logger.info("inventory_sale_finalization_started order_id=%s", order_id)
        finalize_inventory_sale(order)

        save_order(order)
        log_order_state(order)
    else:
        logger.warning("payment_capture_failed order_id=%s", order_id)
        mark_order_status(order, "FAILED")

        logger.info("inventory_release_started order_id=%s", order_id)
        release_order_inventory(order)

        save_order(order)
        log_order_state(order)

        return order

    if order_failed(order):
        logger.warning("inventory_sale_finalization_failed order_id=%s", order_id)
        return order

    logger.info("invoice_creation_started order_id=%s", order_id)
    create_invoice(order)

    mark_invoice_created(order)
    save_order(order)
    log_order_state(order)
    # what happens if invoice hasn't been created / solution retry logic

    logger.info("notification_send_started order_id=%s", order_id)
    send_notification(order)
    mark_notification_sent(order)
    save_order(order)
    log_order_state(order)
    # what happens if notification hasn't been sent / solution retry logic

    mark_order_status(order, "COMPLETED")
    save_order(order)
    logger.info(
        "order_processing_pipeline_finished order_id=%s status=COMPLETED", order_id
    )
    log_order_state(order)

    return order
