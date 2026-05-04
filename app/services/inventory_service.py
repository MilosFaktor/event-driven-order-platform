from app.storage.in_memory import inventory


def has_available_stock(sku, quantity):
    return inventory[sku]["available_stock"] >= quantity


def reserve_inventory_item(order, sku, quantity):
    inventory[sku]["available_stock"] -= quantity
    inventory[sku]["reserved_stock"] += quantity
    print(f"Reserved {quantity} x {inventory[sku]['name']}")
    order["steps"]["inventory"] = "RESERVED"


def fail_inventory_reservation(order, sku):
    order["status"] = "FAILED"
    order["failure_reason"] = f"Insufficient stock for {inventory[sku]['name']}"
    order["steps"]["inventory"] = "FAILED"


def reserve_inventory(order):

    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        if has_available_stock(sku, quantity):  # if item in order has_available_stock
            reserve_inventory_item(order, sku, quantity)  # reserve stock
        else:
            fail_inventory_reservation(order, sku)  # else fail
            break  # potential problem to solve what happens if stock is available for many items
            # and missing only for 1 item
            # solution: checks can be done in the future before placing item into cart


def release_reserved_inventory(sku, quantity):
    inventory[sku]["reserved_stock"] -= quantity
    inventory[sku]["available_stock"] += quantity


def mark_inventory_as_sold(sku, quantity):
    inventory[sku]["reserved_stock"] -= quantity
    inventory[sku]["sold_stock"] += quantity


def finalize_inventory_sale(order):
    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        mark_inventory_as_sold(sku, quantity)


def release_order_inventory(order):
    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        release_reserved_inventory(sku, quantity)


def get_inventory():
    return inventory
