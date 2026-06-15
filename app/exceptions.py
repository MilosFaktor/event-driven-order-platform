class PaymentCaptureError(Exception):
    pass


class NotificationSendError(Exception):
    pass


class InconsistentIdempotencyState(Exception):
    pass
