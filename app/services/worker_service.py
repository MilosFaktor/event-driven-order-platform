import time

from app.services.order_service import process_order
from app.services.queue_service import get_processing_queue


def process_next_order():
    queue = get_processing_queue()
    if not queue:
        return None
    order_id = queue.pop(0)
    return process_order(order_id)


def worker():
    time.sleep(1)
    return print("worker is running...")


def main():
    pass


if __name__ == "__main__":
    main()
