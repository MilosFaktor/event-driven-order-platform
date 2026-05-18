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
        order.steps.inventory = "RESERVED"
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
        order.status = "FAILED"
        order.failure_reason = f"Insufficient stock for {inventory.root[sku].name}"
        order.failure_step = "INVENTORY"
        order.steps.inventory = "FAILED"
        logger.warning(
            "inventory_reservation_failed order_id=%s sku=%s available_stock=%s failure_reason=%s",
            order.order_id,
            sku,
            inventory.root[sku].available_stock,
            order.failure_reason,
        )

    def reserve_inventory(self, order: Order) -> None:
        logger.debug("inventory_reservation_started order_id=%s", order.order_id)
        inventory = self.repo.list_inventory()

        for item in order.items:
            sku = item.sku
            quantity = item.quantity
            if self.has_available_stock(inventory, sku, quantity):
                self.reserve_inventory_item(inventory, order, sku, quantity)

            else:
                self.fail_inventory_reservation(inventory, order, sku)  # else fail
                break  # potential problem to solve what happens if stock is available for many items
                # and missing only for 1 item
                # solution: checks can be done in the future before placing item into cart

        self.repo.save_inventory(inventory)

        if order.steps.inventory == "RESERVED":
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

        order.steps.inventory = "RELEASED"
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
        logger.debug("inventory_sale_finalization_started order_id=%s", order.order_id)
        inventory = self.repo.list_inventory()

        for item in order.items:
            sku = item.sku
            quantity = item.quantity
            inventory = self.mark_inventory_as_sold(inventory, sku, quantity)

        order.steps.inventory = "FINALIZED"

        self.repo.save_inventory(inventory)
        logger.info("inventory_sale_finalized order_id=%s", order.order_id)

    def list_inventory(self) -> Inventory:
        return self.repo.list_inventory()
