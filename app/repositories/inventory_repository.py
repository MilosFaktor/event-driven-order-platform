from app.adapters.json_inventory_adapter import JsonInventoryAdapter
from app.core.logging_config import get_logger
from app.models.inventory import Inventory

logger = get_logger("inventory.repo")


class InventoryRepository:
    def __init__(self, adapter: JsonInventoryAdapter | None = None):
        if adapter is None:
            self.adapter = JsonInventoryAdapter()
        else:
            self.adapter = adapter

    def get_inventory(self) -> Inventory:
        inventory = self.adapter.load_inventory()
        logger.debug("inventory_loaded count=%s", len(inventory.root))

        return inventory

    def save_inventory(self, inventory: Inventory) -> None:
        self.adapter.save_inventory(inventory)
        logger.debug("inventory_saved count=%s", len(inventory.root))
