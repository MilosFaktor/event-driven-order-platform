from app.models.inventory import Inventory
from app.storage import json_storage

INVENTORY_PATH = json_storage.STORAGE_PATHS["inventory"]


class JsonInventoryAdapter:
    def __init__(self, inventory_path: str = INVENTORY_PATH):
        self.inventory_path = inventory_path

    def load_inventory(self) -> Inventory:
        raw_inventory = json_storage.load_json(self.inventory_path)
        return Inventory.model_validate(raw_inventory)

    def save_inventory(self, inventory: Inventory) -> None:
        json_storage.save_json(self.inventory_path, inventory.model_dump())
