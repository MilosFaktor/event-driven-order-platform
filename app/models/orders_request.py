from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Currency


class OrderItemRequest(BaseModel):
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


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    customer_id: str
    items: list[OrderItemRequest]
    currency: Currency = Currency.EUR

    @field_validator("items")
    @classmethod
    def ensure_non_empty_items(
        cls, v: list[OrderItemRequest]
    ) -> list[OrderItemRequest]:
        if not v:
            raise ValueError("Order Request must contain at least one item")
        return v


class CreateOrderResponse(BaseModel):
    order_id: str
    status: str
