from pydantic import BaseModel, ConfigDict, Field


class OrderItemRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    sku: str
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    customer_id: str
    items: list[OrderItemRequest]
    currency: str
