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
from app.services.invoice_service import create_invoice, get_invoices
from app.services.notification_service import get_notifications, send_notification

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


# ============== payment_service.py =================


def payment_captured_mock(order):
    # payment mock
    print("Payment captured successfully")
    order["steps"]["payment"] = "CAPTURED"


def is_payment_captured(order):
    return order["steps"]["payment"] == "CAPTURED"


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
