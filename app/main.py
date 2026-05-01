orders = {}

inventory = {
    "SKU-001": {"name": "Laptop", "price": 999.99, "stock": 2},
    "SKU-002": {"name": "Mouse", "price": 29.99, "stock": 5},
}


def main():
    order_id = "order_001"

    orders[order_id] = {
        "order_id": order_id,
        "customer_id": "customer_123",
        "items": [
            {"sku": "SKU-001", "quantity": 2},
            {"sku": "SKU-002", "quantity": 1},
        ],
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

    print(f"Order status: {orders[order_id]['status']}")
    print()

    # start PROCESSING
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

    print()
    print("After PROCESSING:")
    print()
    print(f"Order status: {orders[order_id]['status']}")
    print(f"Remaining stock: {[item['stock'] for item in inventory.values()]}")
    print(orders[order_id]["steps"])


if __name__ == "__main__":
    main()
