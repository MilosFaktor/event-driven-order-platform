import time

from app.storage.in_memory import orders, processing_queue


def worker():
    time.sleep(1)
    return print("worker is running...")


def main():
    pass


if __name__ == "__main__":
    main()
