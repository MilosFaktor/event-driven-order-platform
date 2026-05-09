from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class OrderItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    sku: str
    quantity: int = Field(gt=0)


class OrderSteps(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    inventory: Literal["PENDING", "RESERVED", "FAILED"] = "PENDING"
    payment: Literal["PENDING", "CAPTURED", "FAILED"] = "PENDING"
    invoice: Literal["PENDING", "CREATED", "FAILED"] = "PENDING"
    notification: Literal["PENDING", "SENT", "FAILED"] = "PENDING"


class Order(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    order_id: str
    customer_id: str
    items: list[OrderItem]
    currency: Literal["USD", "EUR"] = "EUR"
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"] = "PENDING"
    steps: OrderSteps
    failure_reason: str | None = None


class Orders(RootModel[dict[str, Order]]):
    pass
