from app.storage import json_storage

INVENTORY_PATH = json_storage.STORAGE_PATHS["inventory"]


def has_available_stock(inventory, sku, quantity):
    return inventory[sku]["available_stock"] >= quantity


def reserve_inventory_item(inventory, order, sku, quantity):
    inventory[sku]["available_stock"] -= quantity
    inventory[sku]["reserved_stock"] += quantity
    print(f"Reserved {quantity} x {inventory[sku]['name']}")
    order["steps"]["inventory"] = "RESERVED"


def fail_inventory_reservation(inventory, order, sku):
    order["status"] = "FAILED"
    order["failure_reason"] = f"Insufficient stock for {inventory[sku]['name']}"
    order["steps"]["inventory"] = "FAILED"


def reserve_inventory(order):
    inventory = get_inventory()

    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        if has_available_stock(inventory, sku, quantity):
            reserve_inventory_item(inventory, order, sku, quantity)
            save_inventory(inventory)

        else:
            fail_inventory_reservation(inventory, order, sku)  # else fail
            break  # potential problem to solve what happens if stock is available for many items
            # and missing only for 1 item
            # solution: checks can be done in the future before placing item into cart


def release_reserved_inventory(sku, quantity):
    inventory = get_inventory()
    inventory[sku]["reserved_stock"] -= quantity
    inventory[sku]["available_stock"] += quantity
    save_inventory(inventory)


def release_order_inventory(order):
    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        release_reserved_inventory(sku, quantity)


def mark_inventory_as_sold(sku, quantity):
    inventory = get_inventory()
    inventory[sku]["reserved_stock"] -= quantity
    inventory[sku]["sold_stock"] += quantity
    save_inventory(inventory)


def finalize_inventory_sale(order):
    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        mark_inventory_as_sold(sku, quantity)


def get_inventory():
    return json_storage.load_json(INVENTORY_PATH)


def save_inventory(inventory):
    json_storage.save_json(INVENTORY_PATH, inventory)
