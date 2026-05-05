from app.storage import json_storage

NOTIFICATIONS_PATH = json_storage.STORAGE_PATHS["notifications"]


def send_notification(order):
    notifications = get_notifications()
    notification_id = f"ntf_{order['order_id']}"

    notifications[notification_id] = {
        "notification_id": notification_id,
        "order_id": order["order_id"],
        "customer_id": order["customer_id"],
        "channel": "email",
        "type": "ORDER_CONFIRMED",
        "status": "SENT",
        "message": f"Your order {order['order_id']} has been confirmed.",
    }

    save_notifications(notifications)

    return notifications[notification_id]


def get_notifications():
    return json_storage.load_json(NOTIFICATIONS_PATH)


def save_notifications(notifications):
    json_storage.save_json(NOTIFICATIONS_PATH, notifications)
