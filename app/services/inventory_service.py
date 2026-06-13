from app.core.logging_config import get_logger
from app.models.inventory import Inventory
from app.models.order import Order
from app.repositories.inventory_repository import InventoryRepository

logger = get_logger("inventory.service")


class InventoryService:
    def __init__(self, repo: InventoryRepository | None = None):
        self.repo = repo or InventoryRepository()

    def has_available_stock(
        self, inventory: Inventory, sku: str, quantity: int
    ) -> bool:
        return inventory.root[sku].available_stock >= quantity

    def reserve_inventory_item(
        self, inventory: Inventory, order: Order, sku: str, quantity: int
    ) -> None:
        inventory.root[sku].available_stock -= quantity
        inventory.root[sku].reserved_stock += quantity
        order.steps.reserve_inventory = "RESERVED"
        logger.debug(
            "inventory_item_reserved order_id=%s sku=%s quantity=%s available_stock=%s reserved_stock=%s",
            order.order_id,
            sku,
            quantity,
            inventory.root[sku].available_stock,
            inventory.root[sku].reserved_stock,
        )

    def fail_inventory_reservation(
        self, inventory: Inventory, order: Order, sku: str
    ) -> None:
        order.failure_reason = f"Insufficient stock for {inventory.root[sku].name}"
        order.steps.reserve_inventory = "FAILED"

    def reserve_inventory(self, order: Order) -> None:
        inventory = self.repo.list_inventory()

        items_to_reserve = []
        for item in order.items:
            sku = item.sku
            quantity = item.quantity
            if self.has_available_stock(inventory, sku, quantity):
                items_to_reserve.append((sku, quantity))

            else:
                self.fail_inventory_reservation(inventory, order, sku)

                break

        if order.steps.reserve_inventory != "FAILED":
            for sku, quantity in items_to_reserve:
                self.reserve_inventory_item(inventory, order, sku, quantity)

        self.repo.save_inventory(inventory)

        if order.steps.reserve_inventory == "RESERVED":
            logger.info("inventory_reserved order_id=%s", order.order_id)

    def release_reserved_inventory(
        self, inventory: Inventory, sku: str, quantity: int
    ) -> None:
        inventory.root[sku].reserved_stock -= quantity
        inventory.root[sku].available_stock += quantity

        logger.debug(
            "inventory_item_released sku=%s quantity=%s available_stock=%s reserved_stock=%s",
            sku,
            quantity,
            inventory.root[sku].available_stock,
            inventory.root[sku].reserved_stock,
        )

    def release_order_inventory(self, order: Order) -> None:
        inventory = self.repo.list_inventory()
        logger.info("inventory_release_started order_id=%s", order.order_id)
        for item in order.items:
            sku = item.sku
            quantity = item.quantity
            self.release_reserved_inventory(inventory, sku, quantity)

        self.repo.save_inventory(inventory)

        order.steps.reserve_inventory = "RELEASED"
        logger.info("inventory_release_finished order_id=%s", order.order_id)

    def mark_inventory_as_sold(
        self, inventory: Inventory, sku: str, quantity: int
    ) -> Inventory:
        inventory.root[sku].reserved_stock -= quantity
        inventory.root[sku].sold_stock += quantity

        logger.debug(
            "inventory_item_sold sku=%s quantity=%s reserved_stock=%s sold_stock=%s",
            sku,
            quantity,
            inventory.root[sku].reserved_stock,
            inventory.root[sku].sold_stock,
        )
        return inventory

    def finalize_inventory_sale(self, order: Order) -> None:

        inventory = self.repo.list_inventory()

        for item in order.items:
            sku = item.sku
            quantity = item.quantity
            inventory = self.mark_inventory_as_sold(inventory, sku, quantity)

        order.steps.finalize_inventory_sale = "FINALIZED"

        self.repo.save_inventory(inventory)
        logger.info("inventory_sale_finalized order_id=%s", order.order_id)

    def list_inventory(self) -> Inventory:
        return self.repo.list_inventory()

    def save_inventory(self, inventory: Inventory) -> None:
        self.repo.save_inventory(inventory)
