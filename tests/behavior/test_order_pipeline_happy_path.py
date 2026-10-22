from app.core.config import Settings
from app.core.dependencies import AppDependencies
from app.models.enums import (
    InventoryReservationStatus,
    InventorySaleStatus,
    InvoiceCreationStatus,
    NotificationSendStatus,
    OrderStatus,
    PaymentCaptureStatus,
)
from tests.helpers import create_default_test_order


def test_order_pipeline_service_happy_path(clean_storage):

    settings = Settings(
        max_processing_attempts=4,
        retry_base_delay_seconds=1,
        retry_backoff_multiplier=2,
    )
    deps = AppDependencies(settings=settings)

    order_pipeline = deps.order_pipeline_service()
    order_service = deps.order_service()
    order_id = "ord_123"

    create_default_test_order(order_service, order_id)

    processed_order = order_pipeline.process_order(order_id)

    assert processed_order is not None
    assert processed_order.order_id == "ord_123"
    assert processed_order.customer_id == "cust_123"
    assert processed_order.status == OrderStatus.COMPLETED
    assert (
        processed_order.steps.reserve_inventory == InventoryReservationStatus.RESERVED
    )
    assert processed_order.steps.capture_payment == PaymentCaptureStatus.CAPTURED
    assert (
        processed_order.steps.finalize_inventory_sale == InventorySaleStatus.FINALIZED
    )
    assert processed_order.steps.create_invoice == InvoiceCreationStatus.CREATED
    assert processed_order.steps.send_notification == NotificationSendStatus.SENT
    assert processed_order.failure_reason is None
    assert processed_order.failure_step is None
    assert processed_order.attempt_count == 1
