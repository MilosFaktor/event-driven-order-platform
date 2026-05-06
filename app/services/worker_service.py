import time

from app import config
from app.services.order_service import process_order
from app.services.queue_service import (
    dequeue_order,
    not_queue_empty,
)


def process_next_order():
    order_id = dequeue_order()
    if order_id is None:
        return None
    return process_order(order_id)


def worker_server():
    # order_id = "order_123"
    seconds = 0
    while True:
        if not_queue_empty():
            print("Work registered in queue")
            process_next_order()

        print(f"[{seconds}]seconds, running ...")

        seconds += config.QUEUE_INTERVAL
        time.sleep(config.QUEUE_INTERVAL)


def main():
    print("Worker has been started.")
    worker_server()


if __name__ == "__main__":
    main()
