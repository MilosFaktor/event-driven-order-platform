from app.core.logging_config import get_logger
from app.models.notifications import Notifications
from app.storage import json_storage

NOTIFICATIONS_PATH = json_storage.STORAGE_PATHS["notifications"]

logger = get_logger("notification.service")


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
    logger.info(
        "notification_sent order_id=%s notification_id=%s channel=%s",
        order["order_id"],
        notification_id,
        notifications[notification_id]["channel"],
    )

    return notifications[notification_id]


def get_notifications():
    raw_notifications = json_storage.load_json(NOTIFICATIONS_PATH)
    logger.debug("notifications_loaded count=%s", len(raw_notifications))

    validated_notifications = Notifications.model_validate(raw_notifications)
    logger.debug(
        "notifications_validated_on_load count=%s", len(validated_notifications.root)
    )

    return validated_notifications.model_dump()


def save_notifications(notifications):
    validated_notifications = Notifications.model_validate(notifications)
    logger.debug(
        "notifications_validated_before_save count=%s",
        len(validated_notifications.root),
    )

    json_storage.save_json(NOTIFICATIONS_PATH, validated_notifications.model_dump())
