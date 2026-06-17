from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator

from app.models.enums import (
    Currency,
    InventoryReservationStatus,
    InventorySaleStatus,
    InvoiceCreationStatus,
    NotificationSendStatus,
    OrderFailureStep,
    OrderStatus,
    PaymentCaptureStatus,
)


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

    reserve_inventory: InventoryReservationStatus = InventoryReservationStatus.PENDING
    capture_payment: PaymentCaptureStatus = PaymentCaptureStatus.PENDING
    finalize_inventory_sale: InventorySaleStatus = InventorySaleStatus.PENDING
    create_invoice: InvoiceCreationStatus = InvoiceCreationStatus.PENDING
    send_notification: NotificationSendStatus = NotificationSendStatus.PENDING


class Order(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, str_strip_whitespace=True
    )

    order_id: str
    customer_id: str
    items: list[OrderItem]
    currency: Currency = Currency.EUR
    status: OrderStatus = OrderStatus.PENDING
    steps: OrderSteps
    failure_reason: str | None = None
    failure_step: OrderFailureStep | None = None
    attempt_count: int = 0
    last_error: str | None = None
    last_failure_step: OrderFailureStep | None = None

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
