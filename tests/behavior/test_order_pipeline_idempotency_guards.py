from app.core.config import Settings
from app.models.enums import (
    InventorySaleStatus,
    InvoiceCreationStatus,
    NotificationSendStatus,
    OrderFailureStep,
    OrderStatus,
)
from app.models.order import Order
from app.services.order_service import OrderService
from app.workflows.order_pipeline_service import OrderPipelineService
from tests.helpers import create_default_test_order, silent_storage_reset


def test_finalized_inventory_sale_is_not_applied_twice():
    silent_storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=3,
            retry_base_delay_seconds=0,
            retry_backoff_multiplier=2,
            retryable_failure_steps={
                OrderFailureStep.FINALIZE_INVENTORY_SALE,
            },
        )

        order_id = "ord_retry1"

        order_service = OrderService()
        create_default_test_order(order_service, order_id)

        pipeline = OrderPipelineService(settings=settings)

        processed_order = pipeline.process_order(order_id)

        assert isinstance(processed_order, Order)
        assert processed_order.status == OrderStatus.COMPLETED
        assert (
            processed_order.steps.finalize_inventory_sale
            == InventorySaleStatus.FINALIZED
        )

        inventory_after_first_run = pipeline.inventory_service.list_inventory()
        sku_001_sold_after_first_run = inventory_after_first_run.root[
            "SKU-001"
        ].sold_stock
        sku_002_sold_after_first_run = inventory_after_first_run.root[
            "SKU-002"
        ].sold_stock

        processed_order.status = OrderStatus.FAILED
        processed_order.failure_step = OrderFailureStep.FINALIZE_INVENTORY_SALE
        processed_order.failure_reason = "Manual retry test"
        order_service.save_order(processed_order)

        processed_order = pipeline.process_order(order_id)

        inventory_after_second_run = pipeline.inventory_service.list_inventory()

        assert isinstance(processed_order, Order)
        assert processed_order.status == OrderStatus.COMPLETED
        assert (
            processed_order.steps.finalize_inventory_sale
            == InventorySaleStatus.FINALIZED
        )
        assert (
            inventory_after_second_run.root["SKU-001"].sold_stock
            == sku_001_sold_after_first_run
        )
        assert (
            inventory_after_second_run.root["SKU-002"].sold_stock
            == sku_002_sold_after_first_run
        )

    finally:
        silent_storage_reset()


def test_sent_notification_is_not_sent_twice():
    silent_storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=3,
            retry_base_delay_seconds=0,
            retry_backoff_multiplier=2,
            retryable_failure_steps={
                OrderFailureStep.SEND_NOTIFICATION,
            },
        )

        order_id = "ord_retry1"

        order_service = OrderService()
        create_default_test_order(order_service, order_id)

        pipeline = OrderPipelineService(settings=settings)

        processed_order = pipeline.process_order(order_id)

        assert isinstance(processed_order, Order)
        assert processed_order.status == OrderStatus.COMPLETED
        assert processed_order.steps.send_notification == NotificationSendStatus.SENT

        notifications_after_first_run = (
            pipeline.notification_service.list_notifications()
        )
        notification_id = f"ntf_{order_id}"
        notification_after_first_run = notifications_after_first_run.root[
            notification_id
        ]

        processed_order.status = OrderStatus.FAILED
        processed_order.failure_step = OrderFailureStep.SEND_NOTIFICATION
        processed_order.failure_reason = "Manual retry test"
        order_service.save_order(processed_order)

        processed_order = pipeline.process_order(order_id)

        notifications_after_second_run = (
            pipeline.notification_service.list_notifications()
        )

        assert isinstance(processed_order, Order)
        assert processed_order.status == OrderStatus.COMPLETED
        assert processed_order.steps.send_notification == NotificationSendStatus.SENT
        assert len(notifications_after_second_run.root) == len(
            notifications_after_first_run.root
        )
        assert (
            notifications_after_second_run.root[notification_id]
            == notification_after_first_run
        )

    finally:
        silent_storage_reset()


def test_created_invoice_is_not_created_twice():
    silent_storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=3,
            retry_base_delay_seconds=0,
            retry_backoff_multiplier=2,
            retryable_failure_steps={
                OrderFailureStep.CREATE_INVOICE,
            },
        )

        order_id = "ord_retry1"

        order_service = OrderService()
        create_default_test_order(order_service, order_id)

        pipeline = OrderPipelineService(settings=settings)

        processed_order = pipeline.process_order(order_id)

        assert isinstance(processed_order, Order)
        assert processed_order.status == OrderStatus.COMPLETED
        assert processed_order.steps.create_invoice == InvoiceCreationStatus.CREATED

        invoices_after_first_run = pipeline.invoice_service.list_invoices()
        invoice_id = f"inv_{order_id}"
        invoice_after_first_run = invoices_after_first_run.root[invoice_id]

        processed_order.status = OrderStatus.FAILED
        processed_order.failure_step = OrderFailureStep.CREATE_INVOICE
        processed_order.failure_reason = "Manual retry test"
        order_service.save_order(processed_order)

        processed_order = pipeline.process_order(order_id)

        invoices_after_second_run = pipeline.invoice_service.list_invoices()

        assert isinstance(processed_order, Order)
        assert processed_order.status == OrderStatus.COMPLETED
        assert processed_order.steps.create_invoice == InvoiceCreationStatus.CREATED
        assert len(invoices_after_second_run.root) == len(invoices_after_first_run.root)
        assert invoices_after_second_run.root[invoice_id] == invoice_after_first_run

    finally:
        silent_storage_reset()
