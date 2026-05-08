from uuid import uuid4

from app.core.logging_config import get_logger
from app.services.idempotency_service import store_idempotency_key
from app.storage import json_storage

ORDERS_PATH = json_storage.STORAGE_PATHS["orders"]


logger = get_logger("orders.service")


def order_is_completed(order):
    return order["status"] == "COMPLETED"


def order_failed(order):
    return order["status"] == "FAILED"


def order_being_processed(order):
    return order["status"] == "PROCESSING"


def create_order(idempotency_key, order_id, customer_id, items, currency):
    logger.info(
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
    logger.info(
        "order_created order_id=%s customer_id=%s status=PENDING",
        order_id,
        customer_id,
    )


def get_orders():
    return json_storage.load_json(ORDERS_PATH)


def get_order(order_id):
    orders = get_orders()
    order = orders.get(order_id, None)
    if order is None:
        logger.warning("order_not_found order_id=%s", order_id)
    else:
        logger.info(
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
    logger.debug(
        "order_saved order_id=%s status=%s",
        order["order_id"],
        order["status"],
    )


def generate_order_id():
    orders = get_orders()
    while True:
        order_id = f"ord_{uuid4().hex[:8]}"
        if order_id not in orders:
            logger.info("order_id_generated order_id=%s", order_id)
            return order_id
