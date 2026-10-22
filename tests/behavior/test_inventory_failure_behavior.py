from app.core.config import Settings
from app.core.dependencies import AppDependencies
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
from app.models.inventory import Inventory, InventoryItem
from app.models.order import Order, OrderItem


def test_inventory_reservation_failure_fails_order_without_running_later_steps(
    clean_storage,
):

    settings = Settings(
        max_processing_attempts=3,
        retry_base_delay_seconds=1,
        retry_backoff_multiplier=2,
    )

    order_id = "ord_123"

    deps = AppDependencies(settings=settings)

    order_service = deps.order_service()
    inventory_service = deps.inventory_service()
    pipeline = deps.order_pipeline_service()

    inventory = {
        "SKU-001": InventoryItem(
            name="Laptop",
            price=950.5,
            available_stock=10,
            reserved_stock=0,
            sold_stock=0,
        ),
        "SKU-002": InventoryItem(
            name="Mouse",
            price=30,
            available_stock=10,
            reserved_stock=0,
            sold_stock=0,
        ),
    }
    inventory_service.save_inventory(Inventory(root=inventory))

    order_service.create_order(
        order_id=order_id,
        customer_id="cust_123",
        items=[
            OrderItem(sku="SKU-001", quantity=20),
            OrderItem(sku="SKU-002", quantity=10),
        ],
        currency=Currency.EUR,
    )

    processed_order = pipeline.process_order(order_id)

    assert isinstance(processed_order, Order)
    assert processed_order.status == OrderStatus.FAILED
    assert processed_order.failure_step == OrderFailureStep.RESERVE_INVENTORY
    assert processed_order.failure_reason == "Insufficient stock for Laptop"
    assert processed_order.steps.reserve_inventory == InventoryReservationStatus.FAILED
    assert processed_order.steps.capture_payment == PaymentCaptureStatus.PENDING
    assert processed_order.steps.finalize_inventory_sale == InventorySaleStatus.PENDING
    assert processed_order.steps.create_invoice == InvoiceCreationStatus.PENDING
    assert processed_order.steps.send_notification == NotificationSendStatus.PENDING


def test_inventory_reservation_failure_does_not_partially_reserve_stock(clean_storage):

    settings = Settings(
        max_processing_attempts=3,
        retry_base_delay_seconds=1,
        retry_backoff_multiplier=2,
    )

    order_id = "ord_123"

    deps = AppDependencies(settings=settings)

    order_service = deps.order_service()
    inventory_service = deps.inventory_service()
    pipeline = deps.order_pipeline_service()

    inventory = {
        "SKU-001": InventoryItem(
            name="Laptop",
            price=950.5,
            available_stock=10,
            reserved_stock=0,
            sold_stock=0,
        ),
        "SKU-002": InventoryItem(
            name="Mouse",
            price=30,
            available_stock=10,
            reserved_stock=0,
            sold_stock=0,
        ),
    }
    inventory_service.save_inventory(Inventory(root=inventory))

    order_service.create_order(
        order_id=order_id,
        customer_id="cust_123",
        items=[
            OrderItem(sku="SKU-001", quantity=5),
            OrderItem(sku="SKU-002", quantity=20),
        ],
        currency=Currency.EUR,
    )

    processed_order = pipeline.process_order(order_id)

    assert isinstance(processed_order, Order)
    assert processed_order.status == OrderStatus.FAILED
    assert processed_order.failure_step == OrderFailureStep.RESERVE_INVENTORY
    assert processed_order.failure_reason == "Insufficient stock for Mouse"
    assert processed_order.steps.reserve_inventory == InventoryReservationStatus.FAILED

    assert inventory_service.list_inventory().model_dump() == {
        "SKU-001": {
            "name": "Laptop",
            "price": 950.5,
            "available_stock": 10,
            "reserved_stock": 0,
            "sold_stock": 0,
        },
        "SKU-002": {
            "name": "Mouse",
            "price": 30.0,
            "available_stock": 10,
            "reserved_stock": 0,
            "sold_stock": 0,
        },
    }
