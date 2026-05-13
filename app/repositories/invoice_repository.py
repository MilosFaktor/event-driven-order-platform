from app.adapters.json_invoice_adapter import InvoiceAdapter
from app.core.logging_config import get_logger
from app.models.invoices import Invoices

logger = get_logger("invoice.repo")


class InvoiceRepository:
    def __init__(self, adapter: InvoiceAdapter | None = None):
        if adapter is None:
            self.adapter = InvoiceAdapter()
        else:
            self.adapter = adapter

    def list_invoices(self) -> Invoices:
        invoices = self.adapter.load_invoices()
        logger.debug("invoices_loaded count=%s", len(invoices.root))

        return invoices

    def save_invoices(self, invoices: Invoices) -> None:
        self.adapter.save_invoices(invoices)
        logger.debug("invoices_saved count=%s", len(invoices.root))
