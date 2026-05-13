from app.adapters.json_notification_adapter import NotificationAdapter
from app.core.logging_config import get_logger
from app.models.notifications import Notifications

logger = get_logger("notifications.repo")


class NotificationRepository:
    def __init__(self, adapter: NotificationAdapter | None = None):
        if adapter is None:
            self.adapter = NotificationAdapter()
        else:
            self.adapter = adapter

    def list_notifications(self) -> Notifications:
        notifications = self.adapter.load_notifications()
        logger.debug("notifications_loaded count=%s", len(notifications.root))

        return notifications

    def save_notifications(self, notifications: Notifications) -> None:
        self.adapter.save_notifications(notifications)
        logger.debug("notifications_saved count=%s", len(notifications.root))
