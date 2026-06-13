from app.core.config import Settings, settings
from app.models.order import Order, OrderItem
from app.models.types import FailureStep
from app.services.order_service import OrderService
from app.services.queue_service import ProcessingQueueService
from app.workflows.order_pipeline_service import OrderPipelineService
from app.workflows.worker_service import WorkerService
from tests.helpers import silent_storage_reset


def test_empty_queue_returns_none():
    silent_storage_reset()

    try:
        queue_service = ProcessingQueueService()

        assert queue_service.get_first_queue_item() is None

        worker = WorkerService(
            settings=settings,
            queue_service=queue_service,
            order_pipeline_service=OrderPipelineService(settings=settings),
        )
        result = worker.process_next_order()

        assert result is None

    finally:
        silent_storage_reset()


def test_stale_queue_item_is_discarded():
    silent_storage_reset()

    try:
        queue_service = ProcessingQueueService()
        queue_service.enqueue_order("ord_missing")

        assert queue_service.list_processing_queue().root == ["ord_missing"]

        worker = WorkerService(
            settings=settings,
            queue_service=queue_service,
            order_pipeline_service=OrderPipelineService(settings=settings),
        )
        result = worker.process_next_order()

        assert result == "stale_queue_discarded"
        assert queue_service.list_processing_queue().root == []

    finally:
        silent_storage_reset()


def test_non_retryable_failed_order_dequeues_and_stops():
    silent_storage_reset()

    try:
        test_settings = Settings(retryable_failure_steps={FailureStep.CAPTURE_PAYMENT})
        queue_service = ProcessingQueueService()
        order_service = OrderService()
        order_pipeline_service = OrderPipelineService(
            settings=test_settings, order_service=order_service
        )

        items = [
            OrderItem(sku="SKU-001", quantity=1),
            OrderItem(sku="SKU-002", quantity=2),
        ]
        order_service.create_order(
            order_id="ord_123",
            customer_id="cust_123",
            items=items,
            currency="EUR",
        )

        order = order_service.get_order("ord_123")
        assert isinstance(order, Order)
        order.status = "FAILED"
        order.steps.reserve_inventory = "FAILED"
        order.failure_step = FailureStep.RESERVE_INVENTORY
        order.failure_reason = "Inventory reservation failed"
        order_service.save_order(order)

        queue_service.enqueue_order("ord_123")

        worker_service = WorkerService(
            settings=test_settings,
            queue_service=queue_service,
            order_pipeline_service=order_pipeline_service,
        )
        result = worker_service.process_next_order()

        assert isinstance(result, Order)
        assert result.status == "FAILED"
        assert result.failure_step == FailureStep.RESERVE_INVENTORY
        assert result.failure_reason == "Inventory reservation failed"
        assert queue_service.list_processing_queue().root == []

    finally:
        silent_storage_reset()
