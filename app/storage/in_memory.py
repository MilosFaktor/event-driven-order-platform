orders = {}

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

idempotency_keys = {}

processing_queue = []
