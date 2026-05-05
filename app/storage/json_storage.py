import json

STORAGE_PATHS = {
    "queue": "data/processing_queue.json",
    "inventory": "data/inventory.json",
    "invoices": "data/invoices.json",
    "notifications": "data/notifications.json",
    "idempotency_keys": "data/idempotency_keys.json",
    "orders": "data/orders.json",
}


def load_json(filename):
    with open(filename, "r") as f:
        return json.load(f)


def save_json(filename, content):
    with open(filename, "w") as f:
        json.dump(content, f, indent=2)
