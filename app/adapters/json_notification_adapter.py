from app.models.notifications import Notifications
from app.storage import json_storage

NOTIFICATIONS_PATH = json_storage.STORAGE_PATHS["notifications"]


class NotificationAdapter:
    def __init__(self, notifications_path: str = NOTIFICATIONS_PATH):
        self.notifications_path = notifications_path

    def load_notifications(self) -> Notifications:
        raw_notifications = json_storage.load_json(self.notifications_path)
        return Notifications.model_validate(raw_notifications)

    def save_notifications(self, notifications: Notifications) -> None:
        json_storage.save_json(self.notifications_path, notifications.model_dump())
