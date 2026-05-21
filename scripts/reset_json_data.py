from app.storage.json_storage import STORAGE_PATHS, load_json, save_json


def storage_reset():
    print("\nResetting persistent storage JSON...")

    save_json(STORAGE_PATHS["queue"], [])
    print("Queue:")
    print(load_json(STORAGE_PATHS["queue"]))

    save_json(STORAGE_PATHS["invoices"], {})
    print("Invoices:")
    print(load_json(STORAGE_PATHS["invoices"]))

    save_json(STORAGE_PATHS["notifications"], {})
    print("Notifications:")
    print(load_json(STORAGE_PATHS["notifications"]))

    save_json(STORAGE_PATHS["idempotency_keys"], {})
    print("Idempotency_keys:")
    print(load_json(STORAGE_PATHS["idempotency_keys"]))

    save_json(STORAGE_PATHS["orders"], {})
    print("Orders:")
    print(load_json(STORAGE_PATHS["orders"]))

    save_json(
        STORAGE_PATHS["inventory"],
        {
            "SKU-001": {
                "name": "Laptop",
                "price": 950.50,
                "available_stock": 100,
                "reserved_stock": 0,
                "sold_stock": 0,
            },
            "SKU-002": {
                "name": "Mouse",
                "price": 30,
                "available_stock": 100,
                "reserved_stock": 0,
                "sold_stock": 0,
            },
        },
    )
    print("Inventory:")
    print(load_json(STORAGE_PATHS["inventory"]))

    print("JSON storage resetted.")


if __name__ == "__main__":
    storage_reset()
