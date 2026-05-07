from uuid import uuid4

from app.core.logging_config import get_logger
from app.services.inventory_service import (
    finalize_inventory_sale,
    release_order_inventory,
    reserve_inventory,
)
from app.services.invoice_service import create_invoice
from app.services.notification_service import send_notification
from app.services.payment_service import is_payment_captured, payment_captured_mock
from app.storage import json_storage

ORDERS_PATH = json_storage.STORAGE_PATHS["orders"]
IDEMPOTENCY_KEYS_PATH = json_storage.STORAGE_PATHS["idempotency_keys"]

pipeline_logger = get_logger("orders.pipeline")
service_logger = get_logger("orders.service")


def order_is_completed(order):
    return order["status"] == "COMPLETED"


def order_failed(order):
    return order["status"] == "FAILED"


def order_being_processed(order):
    return order["status"] == "PROCESSING"


def mark_order_status(order, status):
    order["status"] = status
    pipeline_logger.info(
        "order_status_changed order_id=%s status=%s",
        order["order_id"],
        status,
    )


def mark_invoice_created(order):
    order["steps"]["invoice"] = "CREATED"
    pipeline_logger.debug("order_invoice_step_updated order_id=%s", order["order_id"])


def mark_notification_sent(order):
    order["steps"]["notification"] = "SENT"
    pipeline_logger.debug(
        "order_notification_step_updated order_id=%s",
        order["order_id"],
    )


def create_order(idempotency_key, order_id, customer_id, items, currency):
    service_logger.info(
        "order_creation_started order_id=%s customer_id=%s item_count=%s",
        order_id,
        customer_id,
        len(items),
    )
    store_idempotency_key(idempotency_key, order_id)

    orders = get_orders()
    orders[order_id] = {
        "order_id": order_id,
        "customer_id": customer_id,
        "items": items,
        "currency": currency,
        "status": "PENDING",
        "steps": {
            "inventory": "PENDING",
            "payment": "PENDING",
            "invoice": "PENDING",
            "notification": "PENDING",
        },
        "failure_reason": None,
    }
    save_orders(orders)
    service_logger.info(
        "order_created order_id=%s customer_id=%s status=PENDING",
        order_id,
        customer_id,
    )


def process_order(order_id):
    pipeline_logger.info("order_processing_pipeline_started order_id=%s", order_id)
    orders = get_orders()
    order = orders[order_id]

    if order_being_processed(order):
        pipeline_logger.info("order_already_being_processed order_id=%s", order_id)
        return order

    if order_is_completed(order):
        pipeline_logger.info("order_already_completed order_id=%s", order_id)
        return order

    mark_order_status(order, "PROCESSING")
    save_order(order)

    pipeline_logger.info("inventory_reservation_started order_id=%s", order_id)
    reserve_inventory(order)
    save_order(order)

    if order_failed(order):
        pipeline_logger.warning("inventory_reservation_failed order_id=%s", order_id)
        return order

    pipeline_logger.info("payment_capture_started order_id=%s", order_id)
    payment_captured_mock(order)
    save_order(order)

    if is_payment_captured(order):
        pipeline_logger.info(
            "inventory_sale_finalization_started order_id=%s", order_id
        )
        finalize_inventory_sale(order)
        save_order(order)
    else:
        pipeline_logger.warning("payment_capture_failed order_id=%s", order_id)
        mark_order_status(order, "FAILED")
        save_order(order)
        pipeline_logger.info("inventory_release_started order_id=%s", order_id)
        release_order_inventory(order)
        save_order(order)
        return order

    if order_failed(order):
        pipeline_logger.warning(
            "inventory_sale_finalization_failed order_id=%s", order_id
        )
        return order

    pipeline_logger.info("invoice_creation_started order_id=%s", order_id)
    create_invoice(order)
    mark_invoice_created(order)
    save_order(order)
    # what happens if invoice hasn't been created / solution retry logic

    pipeline_logger.info("notification_send_started order_id=%s", order_id)
    send_notification(order)
    mark_notification_sent(order)
    save_order(order)
    # what happens if notification hasn't been sent / solution retry logic

    mark_order_status(order, "COMPLETED")
    save_order(order)
    pipeline_logger.info(
        "order_processing_pipeline_finished order_id=%s status=COMPLETED", order_id
    )

    return order


def get_orders():
    return json_storage.load_json(ORDERS_PATH)


def get_order(order_id):
    orders = get_orders()
    order = orders.get(order_id, None)
    if order is None:
        service_logger.warning("order_not_found order_id=%s", order_id)
    else:
        service_logger.info(
            "order_loaded order_id=%s status=%s",
            order_id,
            order["status"],
        )
    return order


def save_orders(orders):
    json_storage.save_json(ORDERS_PATH, orders)


def save_order(order):
    orders = get_orders()
    orders[order["order_id"]] = order
    save_orders(orders)
    service_logger.debug(
        "order_saved order_id=%s status=%s",
        order["order_id"],
        order["status"],
    )


def generate_order_id():
    orders = get_orders()
    while True:
        order_id = f"ord_{uuid4().hex[:8]}"
        if order_id not in orders:
            service_logger.info("order_id_generated order_id=%s", order_id)
            return order_id


def get_idempotency_keys():
    return json_storage.load_json(IDEMPOTENCY_KEYS_PATH)


def get_order_id_by_idempotency_key(idempotency_key):
    idempotency_keys = get_idempotency_keys()
    order_id = idempotency_keys.get(idempotency_key)
    if order_id is None:
        service_logger.info("idempotency_key_not_found")
    else:
        service_logger.info("idempotency_key_matched order_id=%s", order_id)
    return order_id


def store_idempotency_key(idempotency_key, order_id):
    idempotency_keys = get_idempotency_keys()
    idempotency_keys[idempotency_key] = order_id
    json_storage.save_json(IDEMPOTENCY_KEYS_PATH, idempotency_keys)
    service_logger.info("idempotency_key_stored order_id=%s", order_id)
