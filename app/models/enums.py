from enum import StrEnum


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"


class OrderFailureStep(StrEnum):
    RESERVE_INVENTORY = "RESERVE_INVENTORY"
    CAPTURE_PAYMENT = "CAPTURE_PAYMENT"
    FINALIZE_INVENTORY_SALE = "FINALIZE_INVENTORY_SALE"
    CREATE_INVOICE = "CREATE_INVOICE"
    SEND_NOTIFICATION = "SEND_NOTIFICATION"


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InventoryReservationStatus(StrEnum):
    PENDING = "PENDING"
    RESERVED = "RESERVED"
    RELEASED = "RELEASED"
    FAILED = "FAILED"


class PaymentCaptureStatus(StrEnum):
    PENDING = "PENDING"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"


class InventorySaleStatus(StrEnum):
    PENDING = "PENDING"
    FINALIZED = "FINALIZED"
    FAILED = "FAILED"


class InvoiceCreationStatus(StrEnum):
    PENDING = "PENDING"
    CREATED = "CREATED"
    FAILED = "FAILED"


class NotificationSendStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class WorkerProcessResultOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    NO_WORK = "NO_WORK"
    STALE_QUEUE_DISCARDED = "STALE_QUEUE_DISCARDED"
