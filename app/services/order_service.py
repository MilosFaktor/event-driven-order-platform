from uuid import uuid4

from app.services.inventory_service import (
    finalize_inventory_sale,
    release_order_inventory,
    reserve_inventory,
)
from app.services.invoice_service import create_invoice
from app.services.notification_service import send_notification
from app.storage import json_storage

ORDERS_PATH = json_storage.STORAGE_PATHS["orders"]
IDEMPOTENCY_KEYS_PATH = json_storage.STORAGE_PATHS["idempotency_keys"]


def order_is_completed(order):
    return order["status"] == "COMPLETED"


def order_failed(order):
    return order["status"] == "FAILED"


def mark_order_status(order, status):
    order["status"] = status
    orders = get_orders()
    orders[order["order_id"]] = order
    save_orders(orders)


# ============== future payment_service.py =================


def payment_captured_mock(order):
    # payment mock
    print("Payment captured successfully")
    order["steps"]["payment"] = "CAPTURED"


def is_payment_captured(order):
    return order["steps"]["payment"] == "CAPTURED"


# ==================================================


def create_order(idempotency_key, order_id, customer_id, items, currency):
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


def process_order(order_id):
    orders = get_orders()
    order = orders[order_id]

    if order_is_completed(order):
        return order

    mark_order_status(order, "PROCESSING")
    reserve_inventory(order)

    if order_failed(order):
        return order

    payment_captured_mock(order)

    if is_payment_captured(order):
        finalize_inventory_sale(order)
    else:
        mark_order_status(order, "FAILED")
        release_order_inventory(order)
        return order

    if order_failed(order):
        return order

    create_invoice(order)
    # what happens if invoice hasn't been created / solution retry logic

    send_notification(order)
    # what happens if notification hasn't been sent / solution retry logic

    mark_order_status(order, "COMPLETED")

    return order


def get_orders():
    return json_storage.load_json(ORDERS_PATH)


def save_orders(orders):
    json_storage.save_json(ORDERS_PATH, orders)


def get_order(order_id):
    orders = get_orders()
    return orders.get(order_id, None)


def generate_order_id():
    orders = get_orders()
    while True:
        order_id = f"ord_{uuid4().hex[:8]}"
        if order_id not in orders:
            return order_id


def get_order_id_by_idempotency_key(idempotency_key):
    idempotency_keys = get_idempotency_keys()
    return idempotency_keys.get(idempotency_key)


def get_idempotency_keys():
    return json_storage.load_json(IDEMPOTENCY_KEYS_PATH)


def store_idempotency_key(idempotency_key, order_id):
    idempotency_keys = get_idempotency_keys()
    idempotency_keys[idempotency_key] = order_id
    json_storage.save_json(IDEMPOTENCY_KEYS_PATH, idempotency_keys)
