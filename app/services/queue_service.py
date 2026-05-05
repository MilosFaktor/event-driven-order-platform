from app.storage import json_storage

QUEUE_PATH = json_storage.STORAGE_PATHS["queue"]


def enqueue_order(order_id):
    queue: list[str] = get_processing_queue()
    if not isinstance(queue, list):
        raise TypeError("queue must be a list")

    queue.append(order_id)
    json_storage.save_json(QUEUE_PATH, queue)


def dequeue_order():
    queue = get_processing_queue()
    if not isinstance(queue, list):
        raise TypeError("queue must be a list")

    if queue_empty(queue):
        return None
    order_id = queue.pop(0)
    json_storage.save_json(QUEUE_PATH, queue)
    return order_id


def get_processing_queue():
    return json_storage.load_json(QUEUE_PATH)


def not_queue_empty():
    return get_processing_queue() != []


def queue_empty(queue):
    return queue == []
