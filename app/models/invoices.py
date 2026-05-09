from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    computed_field,
    field_validator,
)


class InvoiceItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    sku: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(gt=0)
    # line_total is computed field so i need to change my business logic

    @computed_field  # type: ignore[misc]
    @property
    def line_total(self) -> int:
        return self.quantity * self.unit_price

    @field_validator("sku")
    @classmethod
    def ensure_sku_starts_with_sku(cls, v: str) -> str:
        if not v.startswith("SKU-"):
            raise ValueError("SKU must start with 'SKU-'")
        return v


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

    @field_validator("items")
    @classmethod
    def ensure_non_empty_items(cls, v: list[InvoiceItem]) -> list[InvoiceItem]:
        if not v:
            raise ValueError("Invoice must contain at least one item")
        return v

    @field_validator("invoice_id")
    @classmethod
    def ensure_invoice_id_starts_with_inv(cls, v: str) -> str:
        if not v.startswith("inv_"):
            raise ValueError("Invoice ID must start with 'inv_'")
        return v


class Invoices(RootModel[dict[str, Invoice]]):
    pass
