from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator

from app.models.types import Currency, FailureStep


class OrderItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    sku: str
    quantity: int = Field(gt=0)

    @field_validator("sku")
    @classmethod
    def ensure_sku_starts_with_sku(cls, v: str) -> str:
        if not v.startswith("SKU-"):
            raise ValueError("SKU must start with 'SKU-'")
        return v


class OrderSteps(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    reserve_inventory: Literal["PENDING", "RESERVED", "RELEASED", "FAILED"] = "PENDING"
    capture_payment: Literal["PENDING", "CAPTURED", "FAILED"] = "PENDING"
    finalize_inventory_sale: Literal["PENDING", "FINALIZED", "FAILED"] = "PENDING"
    create_invoice: Literal["PENDING", "CREATED", "FAILED"] = "PENDING"
    send_notification: Literal["PENDING", "SENT", "FAILED"] = "PENDING"


class Order(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    order_id: str
    customer_id: str
    items: list[OrderItem]
    currency: Currency = "EUR"
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"] = "PENDING"
    steps: OrderSteps
    failure_reason: str | None = None
    failure_step: FailureStep | None = None
    attempt_count: int = 0
    last_error: str | None = None
    last_failure_step: FailureStep | None = None

    @field_validator("items")
    @classmethod
    def ensure_non_empty_items(cls, v: list[OrderItem]) -> list[OrderItem]:
        if not v:
            raise ValueError("Order must contain at least one item")
        return v

    @field_validator("order_id")
    @classmethod
    def ensure_order_id_starts_with_ord(cls, v: str) -> str:
        if not v.startswith("ord_"):
            raise ValueError("Order ID must start with 'ord_'")
        return v


class Orders(RootModel[dict[str, Order]]):
    pass
