from services.order_service import create_order, process_order
from storage.in_memory import inventory, orders


def main():
    order_id = "order_001"

    create_order(order_id)

    print(f"Order status: {orders[order_id]['status']}")
    print()

    process_order(order_id)

    print()
    print("After PROCESSING:")
    print()
    print(f"Order status: {orders[order_id]['status']}")
    print(f"Remaining stock: {[item['stock'] for item in inventory.values()]}")
    print(orders[order_id]["steps"])


if __name__ == "__main__":
    main()
