from app.core.config import Settings
from app.exceptions import NotificationSendError, PaymentCaptureError
from app.models.order import OrderItem
from app.models.orders_request import CreateOrderRequest, OrderItemRequest
from app.models.types import FailureStep
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.workflows.order_pipeline_service import OrderPipelineService
from app.workflows.worker_service import WorkerService
from scripts.reset_json_data import storage_reset


def test_failure_step_capture_payment_value():
    assert FailureStep.CAPTURE_PAYMENT == "CAPTURE_PAYMENT"


class FakeQueueService:
    def __init__(self, order_id: str | None = None):
        self.items = [order_id] if order_id is not None else []

    def get_first_queue_item(self):
        return self.items[0] if self.items else None

    def dequeue_order(self):
        return self.items.pop(0)

    def not_queue_empty(self):
        return bool(self.items)


class FakeOrderPipelineService:
    pass


def test_retry_delay_uses_exponential_backoff():
    settings = Settings(
        max_processing_attempts=4,
        retry_base_delay_seconds=1,
        retry_backoff_multiplier=2,
    )

    worker = WorkerService(
        settings=settings,
        queue_service=FakeQueueService(),
        order_pipeline_service=FakeOrderPipelineService(),
    )

    assert worker.calculate_retry_delay_seconds(1) == 1
    assert worker.calculate_retry_delay_seconds(2) == 2
    assert worker.calculate_retry_delay_seconds(3) == 4


def test_order_pipeline_service_happy_path():
    settings = Settings(
        max_processing_attempts=4,
        retry_base_delay_seconds=1,
        retry_backoff_multiplier=2,
    )
    request = CreateOrderRequest(
        customer_id="cust_123",
        items=[
            OrderItemRequest(
                sku="SKU-001",
                quantity=2,
            ),
            OrderItemRequest(
                sku="SKU-002",
                quantity=1,
            ),
        ],
        currency="EUR",
    )

    storage_reset()

    order_service = OrderService()

    order_service.create_order(
        order_id="ord_123",
        customer_id=request.customer_id,
        items=[
            OrderItem(sku=item.sku, quantity=item.quantity) for item in request.items
        ],
        currency=request.currency,
    )

    order_pipeline = OrderPipelineService(settings=settings)

    processed_order = order_pipeline.process_order("ord_123")

    assert processed_order.order_id == "ord_123"
    assert processed_order.customer_id == "cust_123"
    assert processed_order.status == "COMPLETED"
    assert processed_order.steps.reserve_inventory == "RESERVED"
    assert processed_order.steps.capture_payment == "CAPTURED"
    assert processed_order.steps.finalize_inventory_sale == "FINALIZED"
    assert processed_order.steps.create_invoice == "CREATED"
    assert processed_order.steps.send_notification == "SENT"
    assert processed_order.failure_reason is None
    assert processed_order.failure_step is None
    assert processed_order.attempt_count == 1

    storage_reset()


class AlwaysFailPaymentService(PaymentService):
    def capture_payment_mock(self, order):
        order.steps.capture_payment = "FAILED"
        raise PaymentCaptureError(f"Payment capture failed for order {order.order_id}")


def test_payment_failure_retries_and_releases_inventory():
    storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=2,
            retry_base_delay_seconds=0,
            retry_backoff_multiplier=2,
            retryable_failure_steps={
                FailureStep.CAPTURE_PAYMENT,
            },
        )

        order_id = "ord_retry1"

        order_service = OrderService()
        order_service.create_order(
            order_id=order_id,
            customer_id="cust_123",
            items=[
                OrderItem(sku="SKU-001", quantity=2),
                OrderItem(sku="SKU-002", quantity=1),
            ],
            currency="EUR",
        )

        pipeline = OrderPipelineService(
            settings=settings,
            payment_service=AlwaysFailPaymentService(),
        )

        worker = WorkerService(
            settings=settings,
            queue_service=FakeQueueService(order_id),
            order_pipeline_service=pipeline,
        )

        processed_order = worker.process_next_order()

        assert processed_order.status == "FAILED"
        assert processed_order.failure_step == FailureStep.CAPTURE_PAYMENT
        assert processed_order.failure_reason == "Payment capture failed"
        assert processed_order.attempt_count == 2
        assert processed_order.steps.capture_payment == "FAILED"
        assert processed_order.steps.reserve_inventory == "RELEASED"

    finally:
        storage_reset()


class AlwaysFailNotificationService(NotificationService):
    def send_notification(self, order):
        order.steps.send_notification = "FAILED"
        raise NotificationSendError(
            f"Notification sending failed for order {order.order_id}"
        )


def test_notification_failure_retries():
    storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=2,
            retry_base_delay_seconds=0,
            retry_backoff_multiplier=2,
            retryable_failure_steps={
                FailureStep.SEND_NOTIFICATION,
            },
        )

        order_id = "ord_retry1"

        order_service = OrderService()
        order_service.create_order(
            order_id=order_id,
            customer_id="cust_123",
            items=[
                OrderItem(sku="SKU-001", quantity=2),
                OrderItem(sku="SKU-002", quantity=1),
            ],
            currency="EUR",
        )

        pipeline = OrderPipelineService(
            settings=settings,
            notification_service=AlwaysFailNotificationService(),
        )

        worker = WorkerService(
            settings=settings,
            queue_service=FakeQueueService(order_id),
            order_pipeline_service=pipeline,
        )

        processed_order = worker.process_next_order()

        assert processed_order.status == "FAILED"
        assert processed_order.failure_step == FailureStep.SEND_NOTIFICATION
        assert processed_order.failure_reason == "Notification sending failed"
        assert processed_order.attempt_count == 2
        assert processed_order.steps.send_notification == "FAILED"

    finally:
        storage_reset()
