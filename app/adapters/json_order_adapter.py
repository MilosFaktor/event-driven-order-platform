from app.models.order import Orders
from app.storage import json_storage

ORDERS_PATH = json_storage.STORAGE_PATHS["orders"]


class JsonOrderAdapter:
    def __init__(self, orders_path: str = ORDERS_PATH):
        self.orders_path = orders_path

    def load_orders(self) -> Orders:
        raw_orders = json_storage.load_json(self.orders_path)
        return Orders.model_validate(raw_orders)

    def save_orders(self, orders: Orders) -> None:
        json_storage.save_json(self.orders_path, orders.model_dump())
