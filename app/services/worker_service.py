import json
import time

from app import config
from app.services.order_service import create_order, process_order
from app.services.queue_service import (
    enqueue_order,
    get_processing_queue,
    not_queue_empty,
)


def process_next_order():
    queue = get_processing_queue()
    if not queue:
        return None
    order_id = queue.pop(0)
    return process_order(order_id)


def process_next_order_worker_server():
    queue = get_processing_queue()
    print("Processing order ")

    order_id = queue.pop(0)
    return json.dumps(process_order(order_id), indent=2)


def worker_server():
    order_id = "order_123"
    seconds = 0
    while True:
        if not_queue_empty():
            process_next_order_worker_server()

        print(f"[{seconds}]Queue: Empty")
        if (seconds % 4) == 0:
            create_order(
                idempotency_key="5sdfg5sdfg5",
                order_id=order_id,
                customer_id="cust_123",
                items=[
                    {"sku": "SKU-001", "quantity": 2},
                    {"sku": "SKU-002", "quantity": 1},
                ],
                currency="EUR",
            )
            enqueue_order(order_id)
            print("Queue: Enqueued_order")
        seconds += config.QUEUE_INTERVAL
        time.sleep(config.QUEUE_INTERVAL)


def main():
    print("Worker has been started.")
    worker_server()


if __name__ == "__main__":
    main()
