from app.models.invoices import Invoices
from app.storage import json_storage

INVOICES_PATH = json_storage.STORAGE_PATHS["invoices"]


class InvoiceAdapter:
    def __init__(self, invoices_path: str = INVOICES_PATH):
        self.invoices_path = invoices_path

    def load_invoices(self) -> Invoices:
        raw_invoices = json_storage.load_json(self.invoices_path)
        return Invoices.model_validate(raw_invoices)

    def save_invoices(self, invoices: Invoices) -> None:
        json_storage.save_json(self.invoices_path, invoices.model_dump())
