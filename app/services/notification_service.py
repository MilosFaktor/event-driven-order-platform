from app.core.logging_config import get_logger
from app.models.notifications import Notification, Notifications
from app.models.order import Order
from app.repositories.notification_repository import NotificationRepository

logger = get_logger("notification.service")


class NotificationService:
    def __init__(self, repo: NotificationRepository | None = None):
        self.repo = repo or NotificationRepository()

    def mark_notification_sent(self, order):
        order.steps.notification = "SENT"
        logger.debug(
            "order_notification_step_updated order_id=%s",
            order.order_id,
        )

    def failed_send_notification_mock(self, order: Order) -> None:
        # notification mock
        order.steps.notification = "FAILED"
        logger.info(
            "notification_send_failed order_id=%s",
            order.order_id,
        )

    def send_notification(self, order: Order) -> Notification:
        notifications = self.repo.list_notifications()
        notification_id = f"ntf_{order.order_id}"

        notifications.root[notification_id] = Notification(
            notification_id=notification_id,
            order_id=order.order_id,
            customer_id=order.customer_id,
            channel="email",
            type="ORDER_CONFIRMED",
            status="SENT",
            message=f"Your order {order.order_id} has been confirmed.",
        )

        self.repo.save_notifications(notifications)

        self.mark_notification_sent(order)

        logger.info(
            "notification_sent order_id=%s notification_id=%s channel=%s",
            order.order_id,
            notification_id,
            notifications.root[notification_id].channel,
        )

        return notifications.root[notification_id]

    def list_notifications(self) -> Notifications:
        return self.repo.list_notifications()
