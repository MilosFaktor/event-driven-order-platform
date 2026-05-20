from app.core.logging_config import get_logger
from app.models.invoices import Invoice, InvoiceItem, Invoices
from app.models.order import Order
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.invoice_repository import InvoiceRepository

logger = get_logger("invoice.service")


class InvoiceService:
    def __init__(
        self,
        inventory_repo: InventoryRepository | None = None,
        invoice_repo: InvoiceRepository | None = None,
    ):
        self.inventory_repo = inventory_repo or InventoryRepository()
        self.invoice_repo = invoice_repo or InvoiceRepository()

    def mark_invoice_created(self, order):
        order.steps.create_invoice = "CREATED"
        logger.debug("order_invoice_step_updated order_id=%s", order.order_id)

    def create_invoice_items_snapshot(self, order: Order) -> list[InvoiceItem]:
        invoice_items = []
        inventory = self.inventory_repo.list_inventory()

        for item in order.items:
            sku = item.sku
            quantity = item.quantity
            product = inventory.root[sku]

            invoice_items.append(
                InvoiceItem(
                    sku=sku,
                    name=product.name,
                    quantity=quantity,
                    unit_price=product.price,
                    line_total=product.price * quantity,
                )
            )

        return invoice_items

    def create_invoice(self, order: Order) -> Invoice:
        invoices = self.invoice_repo.list_invoices()
        invoice_id = f"inv_{order.order_id}"
        invoice_items = self.create_invoice_items_snapshot(order)

        invoices.root[invoice_id] = Invoice(
            invoice_id=invoice_id,
            order_id=order.order_id,
            customer_id=order.customer_id,
            items=invoice_items,
            currency=order.currency,
            status="CREATED",
        )

        self.invoice_repo.save_invoices(invoices)

        self.mark_invoice_created(order)

        logger.info(
            "invoice_created order_id=%s invoice_id=%s",
            order.order_id,
            invoice_id,
        )

        return invoices.root[invoice_id]

    def list_invoices(self) -> Invoices:
        return self.invoice_repo.list_invoices()
