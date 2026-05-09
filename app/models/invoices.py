from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, computed_field


class InvoiceItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    sku: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(gt=0)
    # line_total is computed field so i need to change my bussiness logic

    @computed_field  # type: ignore[misc]
    @property
    def line_total(self) -> int:
        return self.quantity * self.unit_price


class Invoice(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    invoice_id: str
    order_id: str
    customer_id: str
    items: list[InvoiceItem]
    currency: Literal["USD", "EUR"] = "EUR"
    status: Literal["PENDING", "CREATED", "FAILED"] = "PENDING"


class Invoices(RootModel[dict[str, Invoice]]):
    pass
