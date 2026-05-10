from app.core.logging_config import get_logger
from app.models.inventory import Inventory
from app.storage import json_storage

INVENTORY_PATH = json_storage.STORAGE_PATHS["inventory"]

logger = get_logger("inventory.service")


def has_available_stock(inventory, sku, quantity):
    return inventory[sku]["available_stock"] >= quantity


def reserve_inventory_item(inventory, order, sku, quantity):
    inventory[sku]["available_stock"] -= quantity
    inventory[sku]["reserved_stock"] += quantity
    order["steps"]["inventory"] = "RESERVED"
    logger.debug(
        "inventory_item_reserved order_id=%s sku=%s quantity=%s available_stock=%s reserved_stock=%s",
        order["order_id"],
        sku,
        quantity,
        inventory[sku]["available_stock"],
        inventory[sku]["reserved_stock"],
    )


def fail_inventory_reservation(inventory, order, sku):
    order["status"] = "FAILED"
    order["failure_reason"] = f"Insufficient stock for {inventory[sku]['name']}"
    order["steps"]["inventory"] = "FAILED"
    logger.warning(
        "inventory_reservation_failed order_id=%s sku=%s available_stock=%s failure_reason=%s",
        order["order_id"],
        sku,
        inventory[sku]["available_stock"],
        order["failure_reason"],
    )


def reserve_inventory(order):
    logger.debug("inventory_reservation_started order_id=%s", order["order_id"])
    inventory = get_inventory()

    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        if has_available_stock(inventory, sku, quantity):
            reserve_inventory_item(inventory, order, sku, quantity)

        else:
            fail_inventory_reservation(inventory, order, sku)  # else fail
            break  # potential problem to solve what happens if stock is available for many items
            # and missing only for 1 item
            # solution: checks can be done in the future before placing item into cart

    save_inventory(inventory)

    if order["steps"]["inventory"] == "RESERVED":
        logger.info("inventory_reserved order_id=%s", order["order_id"])


def release_reserved_inventory(sku, quantity):
    inventory = get_inventory()
    inventory[sku]["reserved_stock"] -= quantity
    inventory[sku]["available_stock"] += quantity
    save_inventory(inventory)
    logger.debug(
        "inventory_item_released sku=%s quantity=%s available_stock=%s reserved_stock=%s",
        sku,
        quantity,
        inventory[sku]["available_stock"],
        inventory[sku]["reserved_stock"],
    )


def release_order_inventory(order):
    logger.info("inventory_release_started order_id=%s", order["order_id"])
    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        release_reserved_inventory(sku, quantity)
    logger.info("inventory_release_finished order_id=%s", order["order_id"])


def mark_inventory_as_sold(inventory, sku, quantity):
    inventory[sku]["reserved_stock"] -= quantity
    inventory[sku]["sold_stock"] += quantity

    logger.debug(
        "inventory_item_sold sku=%s quantity=%s reserved_stock=%s sold_stock=%s",
        sku,
        quantity,
        inventory[sku]["reserved_stock"],
        inventory[sku]["sold_stock"],
    )
    return inventory


def finalize_inventory_sale(order):
    logger.debug("inventory_sale_finalization_started order_id=%s", order["order_id"])
    inventory = get_inventory()

    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        inventory = mark_inventory_as_sold(inventory, sku, quantity)

    save_inventory(inventory)
    logger.info("inventory_sale_finalized order_id=%s", order["order_id"])


def get_inventory():
    raw_inventory = json_storage.load_json(INVENTORY_PATH)
    logger.debug("inventory_loaded count=%s", len(raw_inventory))

    validated_inventory = Inventory.model_validate(raw_inventory)
    logger.debug("inventory_validated_on_load count=%s", len(validated_inventory.root))

    return validated_inventory.model_dump()


def save_inventory(inventory):
    validated_inventory = Inventory.model_validate(inventory)
    logger.debug(
        "inventory_validated_before_save count=%s", len(validated_inventory.root)
    )

    json_storage.save_json(INVENTORY_PATH, validated_inventory.model_dump())
