from app.core.config import Settings, settings
from app.models.order import Order
from app.models.types import (
    InventoryReservationStatus,
    OrderFailureStep,
    OrderStatus,
    WorkerProcessResultOutcome,
)
from app.services.order_service import OrderService
from app.services.queue_service import ProcessingQueueService
from app.workflows.order_pipeline_service import OrderPipelineService
from app.workflows.worker_service import WorkerProcessResult, WorkerService
from tests.helpers import create_default_test_order, silent_storage_reset


def test_empty_queue_returns_no_work():
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

        assert isinstance(result, WorkerProcessResult)
        assert result.outcome == WorkerProcessResultOutcome.NO_WORK
        assert result.order is None

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

        assert isinstance(result, WorkerProcessResult)
        assert result.outcome == WorkerProcessResultOutcome.STALE_QUEUE_DISCARDED
        assert result.order is None
        assert queue_service.list_processing_queue().root == []

    finally:
        silent_storage_reset()


def test_non_retryable_failed_order_dequeues_and_stops():
    silent_storage_reset()

    try:
        test_settings = Settings(
            retryable_failure_steps={OrderFailureStep.CAPTURE_PAYMENT}
        )
        queue_service = ProcessingQueueService()
        order_service = OrderService()
        order_pipeline_service = OrderPipelineService(
            settings=test_settings, order_service=order_service
        )

        order_id = "ord_123"

        create_default_test_order(order_service, order_id)

        order = order_service.get_order(order_id)
        assert isinstance(order, Order)
        order.status = OrderStatus.FAILED
        order.steps.reserve_inventory = InventoryReservationStatus.FAILED
        order.failure_step = OrderFailureStep.RESERVE_INVENTORY
        order.failure_reason = "Inventory reservation failed"
        order_service.save_order(order)

        queue_service.enqueue_order(order_id)

        worker_service = WorkerService(
            settings=test_settings,
            queue_service=queue_service,
            order_pipeline_service=order_pipeline_service,
        )
        result = worker_service.process_next_order()

        assert isinstance(result, WorkerProcessResult)
        assert result.outcome == WorkerProcessResultOutcome.FAILURE
        assert isinstance(result.order, Order)
        assert result.order.status == OrderStatus.FAILED
        assert result.order.failure_step == OrderFailureStep.RESERVE_INVENTORY
        assert result.order.failure_reason == "Inventory reservation failed"
        assert queue_service.list_processing_queue().root == []

    finally:
        silent_storage_reset()
