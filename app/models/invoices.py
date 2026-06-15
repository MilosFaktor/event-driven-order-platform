from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)

from app.models.types import Currency, InvoiceCreationStatus


class InvoiceItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    sku: str
    name: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    line_total: float

    @model_validator(mode="after")
    def validate_line_total(self):
        if self.line_total != self.quantity * self.unit_price:
            raise ValueError("line_total must equal quantity * unit_price")
        return self

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
    currency: Currency = Currency.EUR
    status: InvoiceCreationStatus = InvoiceCreationStatus.PENDING

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
