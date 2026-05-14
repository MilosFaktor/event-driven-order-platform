from app.services.idempotency_service import IdempotencyKeysService
from app.services.inventory_service import InventoryService
from app.services.invoice_service import InvoiceService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.queue_service import ProcessingQueueService


class AppDependencies:
    def __init__(self):
        self._idempotency_service = None
        self._inventory_service = None
        self._invoice_service = None
        self._notification_service = None
        self._order_service = None
        self._payment_service = None
        self._queue_service = None

    def idempotency_service(self) -> IdempotencyKeysService:
        if self._idempotency_service is None:
            self._idempotency_service = IdempotencyKeysService()
        return self._idempotency_service

    def inventory_service(self) -> InventoryService:
        if self._inventory_service is None:
            self._inventory_service = InventoryService()
        return self._inventory_service

    def invoice_service(self) -> InvoiceService:
        if self._invoice_service is None:
            self._invoice_service = InvoiceService()
        return self._invoice_service

    def notification_service(self) -> NotificationService:
        if self._notification_service is None:
            self._notification_service = NotificationService()
        return self._notification_service

    def order_service(self) -> OrderService:
        if self._order_service is None:
            self._order_service = OrderService()
        return self._order_service

    def payment_service(self) -> PaymentService:
        if self._payment_service is None:
            self._payment_service = PaymentService()
        return self._payment_service

    def queue_service(self) -> ProcessingQueueService:
        if self._queue_service is None:
            self._queue_service = ProcessingQueueService()
        return self._queue_service


app_dependencies = AppDependencies()
