from app.core.config import Settings
from app.core.logging_config import get_logger
from app.exceptions import NotificationSendError, PaymentCaptureError
from app.models.types import FailureStep
from app.services.inventory_service import InventoryService
from app.services.invoice_service import InvoiceService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

logger = get_logger("orders.pipeline")

PIPELINE_STEPS = [
    FailureStep.RESERVE_INVENTORY,
    FailureStep.CAPTURE_PAYMENT,
    FailureStep.FINALIZE_INVENTORY_SALE,
    FailureStep.CREATE_INVOICE,
    FailureStep.SEND_NOTIFICATION,
]


class OrderPipelineService:
    def __init__(
        self,
        settings: Settings,
        order_service: OrderService | None = None,
        inventory_service: InventoryService | None = None,
        payment_service: PaymentService | None = None,
        invoice_service: InvoiceService | None = None,
        notification_service: NotificationService | None = None,
    ):
        self.settings = settings

        self.order_service = order_service or OrderService()
        self.inventory_service = inventory_service or InventoryService()
        self.payment_service = payment_service or PaymentService()
        self.invoice_service = invoice_service or InvoiceService()
        self.notification_service = notification_service or NotificationService()

    def mark_order_status(self, order, status):
        order.status = status
        logger.info(
            "order_status_changed order_id=%s status=%s",
            order.order_id,
            status,
        )

    def fail_order(self, order, failure_step, failure_reason):
        order.status = "FAILED"
        order.failure_step = failure_step
        order.failure_reason = failure_reason
        logger.warning(
            "order_failed order_id=%s failure_step=%s failure_reason=%s",
            order.order_id,
            failure_step,
            failure_reason,
        )

    def clear_active_failure(self, order):
        if order.failure_step is not None:
            order.last_failure_step = order.failure_step
            order.failure_step = None

        if order.failure_reason is not None:
            order.last_error = order.failure_reason
            order.failure_reason = None

    def reserve_inventory_step(self, order, order_id):
        if order.steps.reserve_inventory == "RESERVED":
            logger.info("inventory_already_reserved order_id=%s", order_id)
            return order
        if order.steps.reserve_inventory == "RELEASED":
            logger.info("inventory_already_released order_id=%s", order_id)
            return order

        logger.info("inventory_reservation_started order_id=%s", order_id)

        self.inventory_service.reserve_inventory(order)

        if order.steps.reserve_inventory == "FAILED":
            self.fail_order(
                order,
                FailureStep.RESERVE_INVENTORY,
                order.failure_reason or "Inventory reservation failed",
            )
            self.order_service.save_order(order)
            self.order_service.log_order_state(order)
            logger.warning("inventory_reservation_failed order_id=%s", order_id)
            return order

        self.order_service.save_order(order)
        self.order_service.log_order_state(order)

        return order

    def capture_payment_step(self, order, order_id):
        if order.steps.capture_payment == "CAPTURED":
            logger.info("payment_already_captured order_id=%s", order_id)
            return order

        logger.info("payment_capture_started order_id=%s", order_id)

        try:
            self.payment_service.capture_payment_mock(order)

        except PaymentCaptureError:
            logger.warning("payment_capture_failed order_id=%s", order_id)
            self.fail_order(
                order, FailureStep.CAPTURE_PAYMENT, "Payment capture failed"
            )

            if order.attempt_count == self.settings.max_processing_attempts:
                if order.steps.reserve_inventory == "RELEASED":
                    logger.info("inventory_already_released order_id=%s", order_id)
                else:
                    self.inventory_service.release_order_inventory(order)

            self.order_service.save_order(order)
            self.order_service.log_order_state(order)
            return order

        self.order_service.save_order(order)
        self.order_service.log_order_state(order)
        return order

    def finalize_inventory_sale_step(self, order, order_id):
        if order.steps.finalize_inventory_sale == "FINALIZED":
            logger.info("inventory_sale_already_finalized order_id=%s", order_id)
            return order

        logger.info("inventory_sale_finalization_started order_id=%s", order_id)

        try:
            self.inventory_service.finalize_inventory_sale(order)
        except Exception:  # catches everything here for now
            self.fail_order(
                order,
                FailureStep.FINALIZE_INVENTORY_SALE,
                "Inventory finalization failed",
            )
            self.order_service.save_order(order)
            self.order_service.log_order_state(order)
            logger.warning("inventory_sale_finalization_failed order_id=%s", order_id)
            return order

        self.order_service.save_order(order)
        self.order_service.log_order_state(order)
        return order

    def create_invoice_step(self, order, order_id):
        if order.steps.create_invoice == "CREATED":
            logger.info("invoice_already_created order_id=%s", order_id)
            return order

        logger.info("invoice_creation_started order_id=%s", order_id)

        try:
            self.invoice_service.create_invoice(order)
        except Exception:  # catches everything here for now
            self.fail_order(
                order, FailureStep.CREATE_INVOICE, "Invoice creation failed"
            )
            self.order_service.save_order(order)
            self.order_service.log_order_state(order)
            logger.warning("invoice_creation_failed order_id=%s", order_id)
            return order

        self.order_service.save_order(order)
        self.order_service.log_order_state(order)
        return order

    def send_notification_step(self, order, order_id):
        if order.steps.send_notification == "SENT":
            logger.info("notification_already_sent order_id=%s", order_id)
            return order

        logger.info("notification_send_started order_id=%s", order_id)

        try:
            self.notification_service.send_notification(order)

        except NotificationSendError:
            self.fail_order(
                order, FailureStep.SEND_NOTIFICATION, "Notification sending failed"
            )

            self.order_service.save_order(order)
            self.order_service.log_order_state(order)

            logger.warning("notification_send_failed order_id=%s", order_id)
            return order

        self.order_service.save_order(order)
        self.order_service.log_order_state(order)
        return order

    def get_start_step(self, order):
        if (
            order.status == "FAILED"
            and order.failure_step in self.settings.retryable_failure_steps
        ):
            return order.failure_step

        return PIPELINE_STEPS[0]

    def get_steps_from(self, start_step):
        start_step_index = PIPELINE_STEPS.index(start_step)
        return PIPELINE_STEPS[start_step_index:]

    def process_order(self, order_id):

        step_handlers = {
            FailureStep.RESERVE_INVENTORY: self.reserve_inventory_step,
            FailureStep.CAPTURE_PAYMENT: self.capture_payment_step,
            FailureStep.FINALIZE_INVENTORY_SALE: self.finalize_inventory_sale_step,
            FailureStep.CREATE_INVOICE: self.create_invoice_step,
            FailureStep.SEND_NOTIFICATION: self.send_notification_step,
        }

        logger.info("order_processing_pipeline_started order_id=%s", order_id)

        order = self.order_service.get_order(order_id)

        if order is None:
            logger.warning("queued_order_not_found order_id=%s", order_id)
            return None

        if self.order_service.order_being_processed(order):
            logger.info("order_already_being_processed order_id=%s", order_id)
            return order

        if self.order_service.order_is_completed(order):
            logger.info("order_already_completed order_id=%s", order_id)
            return order

        if self.order_service.order_failed(order):
            if order.failure_step not in self.settings.retryable_failure_steps:
                logger.info("order_already_failed order_id=%s", order_id)
                return order

            logger.info(
                "retryable_failed_order_reprocessing order_id=%s failure_step=%s",
                order_id,
                order.failure_step,
            )

        start_step = self.get_start_step(order)

        order.attempt_count += 1
        self.mark_order_status(order, "PROCESSING")
        self.order_service.save_order(order)
        self.order_service.log_order_state(order)

        for step in self.get_steps_from(start_step):
            order = step_handlers[step](order, order_id)
            if order.status == "FAILED":
                return order

        self.clear_active_failure(order)

        self.mark_order_status(order, "COMPLETED")
        self.order_service.save_order(order)
        logger.info(
            "order_processing_pipeline_finished order_id=%s status=COMPLETED", order_id
        )
        self.order_service.log_order_state(order)

        return order
