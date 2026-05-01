orders = {}


def main():
    order_id = "ord_001"

    orders[order_id] = {
        "order_id": order_id,
        "customer_id": "cust_123",
        "items": [
            {"sku": "SKU-001", "quantity": 2},
            {"sku": "SKU-002", "quantity": 1},
        ],
        "currency": "EUR",
        "status": "PENDING",
    }

    print(orders[order_id])


if __name__ == "__main__":
    main()
