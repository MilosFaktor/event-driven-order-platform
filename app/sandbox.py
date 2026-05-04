import json

orders = {}

input = {
    "customer_id": "cust_123",
    "items": [{"sku": "SKU-001", "quantity": 2}, {"sku": "SKU-002", "quantity": 1}],
    "currency": "EUR",
}

inventory = {
    "SKU-001": {
        "name": "Laptop",
        "price": 999.99,
        "available_stock": 100,
        "reserved_stock": 0,
        "sold_stock": 0,
    },
    "SKU-002": {
        "name": "Mouse",
        "price": 29.99,
        "available_stock": 100,
        "reserved_stock": 0,
        "sold_stock": 0,
    },
}


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


# ========== inventory_service.py ===========


def has_available_stock(sku, quantity):
    return inventory[sku]["available_stock"] >= quantity


def reserve_inventory_item(order, sku, quantity):
    inventory[sku]["available_stock"] -= quantity
    inventory[sku]["reserved_stock"] += quantity
    print(f"Reserved {quantity} x {inventory[sku]['name']}")
    order["steps"]["inventory"] = "RESERVED"


def fail_inventory_reservation(order, sku):
    order["status"] = "FAILED"
    order["failure_reason"] = f"Insufficient stock for {inventory[sku]['name']}"
    order["steps"]["inventory"] = "FAILED"


def reserve_inventory(order):

    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        if has_available_stock(sku, quantity):  # if item in order has_available_stock
            reserve_inventory_item(order, sku, quantity)  # reserve stock
        else:
            fail_inventory_reservation(order, sku)  # else fail
            break  # potential problem to solve what happens if stock is available for many items
            # and missing only for 1 item
            # solution: checks can be done in the future before placing item into cart


def release_reserved_inventory(sku, quantity):
    inventory[sku]["reserved_stock"] -= quantity
    inventory[sku]["available_stock"] += quantity


def mark_inventory_as_sold(sku, quantity):
    inventory[sku]["reserved_stock"] -= quantity
    inventory[sku]["sold_stock"] += quantity


def finalize_inventory_sale(order):
    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        mark_inventory_as_sold(sku, quantity)


def release_order_inventory(order):
    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        release_reserved_inventory(sku, quantity)


def mark_order_failed(order):
    order["status"] = "FAILED"


# ============== payment_service.py =================


def payment_captured_mock(order):
    # payment mock
    print("Payment captured successfully")
    order["steps"]["payment"] = "CAPTURED"


def is_payment_captured(order):
    return order["steps"]["payment"] == "CAPTURED"


# ============= invoice_service.py =================


def invoice_created_mock(order):
    # invoice mock
    print("Invoice created successfully")
    order["steps"]["invoice"] = "CREATED"


# =============== notification_service.py ===============


def notification_sent_mock(order):
    # notification mock
    print("Notification sent successfully")
    order["steps"]["notification"] = "SENT"


# ============= order_service.py ===============


def order_is_completed(order):
    return order["status"] == "COMPLETED"


def mark_order_processing(order):
    order["status"] = "PROCESSING"


def mark_order_completed(order):
    order["status"] = "COMPLETED"


def order_failed(order):
    return order["status"] == "FAILED"


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

    invoice_created_mock(
        order
    )  # what happens if invoice hasn't been created / solution retry logic

    notification_sent_mock(
        order
    )  # what happens if notification hasn't been sent / solution retry logic

    mark_order_completed(order)

    return order


order = create_order_sand()
print(json.dumps(order, indent=2))
print(process_order_sand("ord_test"))
print(json.dumps(order, indent=2))
print(inventory)
