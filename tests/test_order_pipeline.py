from app.core.config import Settings
from app.exceptions import NotificationSendError, PaymentCaptureError
from app.models.order import Order, OrderItem
from app.models.orders_request import CreateOrderRequest, OrderItemRequest
from app.models.types import FailureStep
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.workflows.order_pipeline_service import OrderPipelineService
from app.workflows.worker_service import WorkerService
from tests.helpers import silent_storage_reset


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
    silent_storage_reset()

    try:
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

        order_service = OrderService()

        order_service.create_order(
            order_id="ord_123",
            customer_id=request.customer_id,
            items=[
                OrderItem(sku=item.sku, quantity=item.quantity)
                for item in request.items
            ],
            currency=request.currency,
        )

        order_pipeline = OrderPipelineService(settings=settings)

        processed_order = order_pipeline.process_order("ord_123")

        assert processed_order is not None
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
    finally:
        silent_storage_reset()


class AlwaysFailPaymentService(PaymentService):
    def capture_payment_mock(self, order):
        order.steps.capture_payment = "FAILED"
        raise PaymentCaptureError(f"Payment capture failed for order {order.order_id}")


def test_payment_failure_retries_and_releases_inventory():
    silent_storage_reset()

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

        assert isinstance(processed_order, Order)
        assert processed_order.status == "FAILED"
        assert processed_order.failure_step == FailureStep.CAPTURE_PAYMENT
        assert processed_order.failure_reason == "Payment capture failed"
        assert processed_order.attempt_count == 2
        assert processed_order.steps.capture_payment == "FAILED"
        assert processed_order.steps.reserve_inventory == "RELEASED"

    finally:
        silent_storage_reset()


class AlwaysFailNotificationService(NotificationService):
    def send_notification(self, order):
        order.steps.send_notification = "FAILED"
        raise NotificationSendError(
            f"Notification sending failed for order {order.order_id}"
        )


def test_notification_failure_retries():
    silent_storage_reset()

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

        assert isinstance(processed_order, Order)
        assert processed_order.status == "FAILED"
        assert processed_order.failure_step == FailureStep.SEND_NOTIFICATION
        assert processed_order.failure_reason == "Notification sending failed"
        assert processed_order.attempt_count == 2
        assert processed_order.steps.send_notification == "FAILED"

    finally:
        silent_storage_reset()


class FailOncePaymentService(PaymentService):
    def __init__(self):
        self._failed = False

    def capture_payment_mock(self, order):
        if self._failed:
            order.steps.capture_payment = "CAPTURED"
            return

        order.steps.capture_payment = "FAILED"
        self._failed = True
        raise PaymentCaptureError(f"Payment capture failed for order {order.order_id}")


def test_payment_failure_then_retry_success_completes_order():
    silent_storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=3,
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
            payment_service=FailOncePaymentService(),
        )

        worker = WorkerService(
            settings=settings,
            queue_service=FakeQueueService(order_id),
            order_pipeline_service=pipeline,
        )

        processed_order = worker.process_next_order()

        assert isinstance(processed_order, Order)
        assert processed_order.status == "COMPLETED"
        assert processed_order.attempt_count == 2
        assert processed_order.steps.capture_payment == "CAPTURED"
        assert processed_order.failure_step is None
        assert processed_order.last_failure_step == "CAPTURE_PAYMENT"
        assert processed_order.failure_reason is None
        assert processed_order.last_error == "Payment capture failed"

    finally:
        silent_storage_reset()


class FailOnceNotificationService(NotificationService):
    def __init__(self):
        super().__init__()
        self._failed = False

    def send_notification(self, order):
        if self._failed:
            order.steps.send_notification = "SENT"
            return super().send_notification(order)

        order.steps.send_notification = "FAILED"
        self._failed = True
        raise NotificationSendError(
            f"Notification sending failed for order {order.order_id}"
        )


def test_notification_failure_then_retry_success_completes_order():
    silent_storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=3,
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
            notification_service=FailOnceNotificationService(),
        )

        worker = WorkerService(
            settings=settings,
            queue_service=FakeQueueService(order_id),
            order_pipeline_service=pipeline,
        )

        processed_order = worker.process_next_order()

        assert isinstance(processed_order, Order)
        assert processed_order.status == "COMPLETED"
        assert processed_order.attempt_count == 2
        assert processed_order.steps.send_notification == "SENT"
        assert processed_order.failure_step is None
        assert processed_order.last_failure_step == FailureStep.SEND_NOTIFICATION
        assert processed_order.failure_reason is None
        assert processed_order.last_error == "Notification sending failed"

    finally:
        silent_storage_reset()


def test_finalized_inventory_sale_is_not_applied_twice():
    silent_storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=3,
            retry_base_delay_seconds=0,
            retry_backoff_multiplier=2,
            retryable_failure_steps={
                FailureStep.FINALIZE_INVENTORY_SALE,
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

        pipeline = OrderPipelineService(settings=settings)

        processed_order = pipeline.process_order(order_id)

        assert isinstance(processed_order, Order)
        assert processed_order.status == "COMPLETED"
        assert processed_order.steps.finalize_inventory_sale == "FINALIZED"

        inventory_after_first_run = pipeline.inventory_service.list_inventory()
        sku_001_sold_after_first_run = inventory_after_first_run.root[
            "SKU-001"
        ].sold_stock
        sku_002_sold_after_first_run = inventory_after_first_run.root[
            "SKU-002"
        ].sold_stock

        processed_order.status = "FAILED"
        processed_order.failure_step = FailureStep.FINALIZE_INVENTORY_SALE
        processed_order.failure_reason = "Manual retry test"
        order_service.save_order(processed_order)

        processed_order = pipeline.process_order(order_id)

        inventory_after_second_run = pipeline.inventory_service.list_inventory()

        assert isinstance(processed_order, Order)
        assert processed_order.status == "COMPLETED"
        assert processed_order.steps.finalize_inventory_sale == "FINALIZED"
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

        pipeline = OrderPipelineService(settings=settings)

        processed_order = pipeline.process_order(order_id)

        assert isinstance(processed_order, Order)
        assert processed_order.status == "COMPLETED"
        assert processed_order.steps.send_notification == "SENT"

        notifications_after_first_run = (
            pipeline.notification_service.list_notifications()
        )
        notification_id = f"ntf_{order_id}"
        notification_after_first_run = notifications_after_first_run.root[
            notification_id
        ]

        processed_order.status = "FAILED"
        processed_order.failure_step = FailureStep.SEND_NOTIFICATION
        processed_order.failure_reason = "Manual retry test"
        order_service.save_order(processed_order)

        processed_order = pipeline.process_order(order_id)

        notifications_after_second_run = (
            pipeline.notification_service.list_notifications()
        )

        assert isinstance(processed_order, Order)
        assert processed_order.status == "COMPLETED"
        assert processed_order.steps.send_notification == "SENT"
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
                FailureStep.CREATE_INVOICE,
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

        pipeline = OrderPipelineService(settings=settings)

        processed_order = pipeline.process_order(order_id)

        assert isinstance(processed_order, Order)
        assert processed_order.status == "COMPLETED"
        assert processed_order.steps.create_invoice == "CREATED"

        invoices_after_first_run = pipeline.invoice_service.list_invoices()
        invoice_id = f"inv_{order_id}"
        invoice_after_first_run = invoices_after_first_run.root[invoice_id]

        processed_order.status = "FAILED"
        processed_order.failure_step = FailureStep.CREATE_INVOICE
        processed_order.failure_reason = "Manual retry test"
        order_service.save_order(processed_order)

        processed_order = pipeline.process_order(order_id)

        invoices_after_second_run = pipeline.invoice_service.list_invoices()

        assert isinstance(processed_order, Order)
        assert processed_order.status == "COMPLETED"
        assert processed_order.steps.create_invoice == "CREATED"
        assert len(invoices_after_second_run.root) == len(invoices_after_first_run.root)
        assert invoices_after_second_run.root[invoice_id] == invoice_after_first_run

    finally:
        silent_storage_reset()
