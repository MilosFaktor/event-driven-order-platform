from app.storage.in_memory import processing_queue


def enqueue_order(order_id):
    processing_queue.append(order_id)


def get_processing_queue():
    return processing_queue
