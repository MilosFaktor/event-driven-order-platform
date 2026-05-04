"""
Experimental order pipeline sandbox.

This file is for exploring workflow logic before moving it into app/services.
The production app should not import from this file.
"""

import json

from app.services.inventory_service import (
    finalize_inventory_sale,
    get_inventory,
    release_order_inventory,
    reserve_inventory,
)
from app.storage.in_memory import invoices, notifications

orders = {}


def create_order_sand():
    order_id = "ord_" + "test"
    orders[order_id] = {
        "order_id": order_id,
        "customer_id": "cust_123",
        "items": [{"sku": "SKU-001", "quantity": 2}, {"sku": "SKU-002", "quantity": 1}],
        "currency": "EUR",
        "status": "PENDING",
        "steps": {
            "inventory": "PENDING",
            "payment": "PENDING",
            "invoice": "PENDING",
            "notification": "PENDING",
        },
        "failure_reason": None,
    }

    return orders[order_id]


# ========== inventory_service.py new ===========


# ============== payment_service.py =================


def payment_captured_mock(order):
    # payment mock
    print("Payment captured successfully")
    order["steps"]["payment"] = "CAPTURED"


def is_payment_captured(order):
    return order["steps"]["payment"] == "CAPTURED"


# ============= invoice_service.py =================


def mark_invoice_created(order):
    order["steps"]["invoice"] = "CREATED"


def create_invoice_items_snapshot(order):
    invoice_items = []

    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        product = get_inventory()[sku]

        invoice_items.append(
            {
                "sku": sku,
                "name": product["name"],
                "quantity": quantity,
                "unit_price": product["price"],
                "line_total": product["price"] * quantity,
            }
        )

    return invoice_items


def create_invoice(order):
    invoice_id = f"inv_{order['order_id']}"
    invoice_items = create_invoice_items_snapshot(order)

    invoices[invoice_id] = {
        "invoice_id": invoice_id,
        "order_id": order["order_id"],
        "customer_id": order["customer_id"],
        "items": invoice_items,
        "currency": order["currency"],
        "status": "CREATED",
    }

    mark_invoice_created(order)
    return invoices[invoice_id]


def get_invoices():
    return invoices


# =============== notification_service.py ===============


def mark_notification_sent(order):
    order["steps"]["notification"] = "SENT"


def send_notification(order):
    notification_id = f"ntf_{order['order_id']}"
    notifications[notification_id] = {
        "notification_id": notification_id,
        "order_id": order["order_id"],
        "customer_id": order["customer_id"],
        "channel": "email",
        "type": "ORDER_CONFIRMED",
        "status": "SENT",
        "message": f"Your order {order['order_id']} has been confirmed.",
    }
    mark_notification_sent(order)
    return notifications[notification_id]


def get_notifications():
    return notifications


# ============= order_service.py ===============


def order_is_completed(order):
    return order["status"] == "COMPLETED"


def mark_order_processing(order):
    order["status"] = "PROCESSING"


def mark_order_completed(order):
    order["status"] = "COMPLETED"


def order_failed(order):
    return order["status"] == "FAILED"


def mark_order_failed(order):
    order["status"] = "FAILED"


# ============================================


def process_order_sand(order_id):
    order = orders[order_id]

    if order_is_completed(order):
        return order

    mark_order_processing(order)
    reserve_inventory(order)

    if order_failed(order):
        return order

    payment_captured_mock(order)

    if is_payment_captured(order):
        finalize_inventory_sale(order)
    else:
        mark_order_failed(order)
        release_order_inventory(order)
        return order

    if order_failed(order):
        return order

    create_invoice(order)
    # what happens if invoice hasn't been created / solution retry logic

    send_notification(order)
    # what happens if notification hasn't been sent / solution retry logic

    mark_order_completed(order)

    return order


order = create_order_sand()
print(json.dumps(order, indent=2))
print(process_order_sand("ord_test"))
print(json.dumps(order, indent=2))
print(get_inventory())
print("INVOICES: ...")
print(get_invoices())
print("NOTIFICATIONS: ...")
print(get_notifications())
print()
print(create_invoice_items_snapshot(order))
