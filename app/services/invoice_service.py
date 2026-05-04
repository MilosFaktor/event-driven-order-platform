from app.services.inventory_service import get_inventory
from app.storage.in_memory import invoices


def mark_invoice_created(order):
    order["steps"]["invoice"] = "CREATED"


def create_invoice_items_snapshot(order):
    invoice_items = []

    for item in order["items"]:
        sku = item["sku"]
        quantity = item["quantity"]
        product = get_inventory()[sku]

        invoice_items.append(
            {
                "sku": sku,
                "name": product["name"],
                "quantity": quantity,
                "unit_price": product["price"],
                "line_total": product["price"] * quantity,
            }
        )

    return invoice_items


def create_invoice(order):
    invoice_id = f"inv_{order['order_id']}"
    invoice_items = create_invoice_items_snapshot(order)

    invoices[invoice_id] = {
        "invoice_id": invoice_id,
        "order_id": order["order_id"],
        "customer_id": order["customer_id"],
        "items": invoice_items,
        "currency": order["currency"],
        "status": "CREATED",
    }

    mark_invoice_created(order)
    return invoices[invoice_id]


def get_invoices():
    return invoices
