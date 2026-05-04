from app.storage.in_memory import notifications


def mark_notification_sent(order):
    order["steps"]["notification"] = "SENT"


def send_notification(order):
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
    mark_notification_sent(order)
    return notifications[notification_id]


def get_notifications():
    return notifications
