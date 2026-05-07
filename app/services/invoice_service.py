from app.core.logging_config import get_logger
from app.services.inventory_service import get_inventory
from app.storage import json_storage

INVOICES_PATH = json_storage.STORAGE_PATHS["invoices"]

logger = get_logger("invoice.service")


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
    invoices = get_invoices()
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

    save_invoices(invoices)
    logger.info(
        "invoice_created order_id=%s invoice_id=%s",
        order["order_id"],
        invoice_id,
    )

    return invoices[invoice_id]


def get_invoices():
    return json_storage.load_json(INVOICES_PATH)


def save_invoices(invoices):
    json_storage.save_json(INVOICES_PATH, invoices)
