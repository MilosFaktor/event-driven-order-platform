from app.storage.in_memory import inventory, orders


def create_order(order_id, customer_id, items, currency):
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


def process_order(order_id):
    orders[order_id]["status"] = "PROCESSING"
    for item in orders[order_id]["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        if inventory[sku]["stock"] >= quantity:
            inventory[sku]["stock"] -= quantity
            print(f"Reserved {quantity} x {inventory[sku]['name']}")
            orders[order_id]["steps"]["inventory"] = "RESERVED"
        else:
            orders[order_id]["status"] = "FAILED"
            orders[order_id]["failure_reason"] = (
                f"Insufficient stock for {inventory[sku]['name']}"
            )
            print(orders[order_id]["failure_reason"])
            orders[order_id]["steps"]["inventory"] = "FAILED"
            break

    if orders[order_id]["status"] != "FAILED":
        # payment mock
        orders[order_id]["steps"]["payment"] = "CAPTURED"

        # invoice mock
        orders[order_id]["steps"]["invoice"] = "CREATED"

        # notification mock
        orders[order_id]["steps"]["notification"] = "SENT"

        orders[order_id]["status"] = "COMPLETED"

    return orders[order_id]


def get_all_orders():
    return list(orders.values())


def get_order(order_id):
    return orders.get(order_id, None)


def generate_order_id():
    return "order_" + str(len(orders) + 1)
