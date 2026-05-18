from app.core.logging_config import get_logger
from app.services.inventory_service import InventoryService
from app.services.invoice_service import InvoiceService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

logger = get_logger("orders.pipeline")


class OrderPipelineService:
    def __init__(
        self,
        order_service: OrderService | None = None,
        inventory_service: InventoryService | None = None,
        payment_service: PaymentService | None = None,
        invoice_service: InvoiceService | None = None,
        notification_service: NotificationService | None = None,
    ):

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

    def mark_notification_sent(self, order):
        order.steps.notification = "SENT"
        logger.debug(
            "order_notification_step_updated order_id=%s",
            order.order_id,
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

    def process_order(self, order_id):
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

        self.mark_order_status(order, "PROCESSING")
        self.order_service.save_order(order)
        self.order_service.log_order_state(order)

        logger.info("inventory_reservation_started order_id=%s", order_id)
        self.inventory_service.reserve_inventory(order)
        self.order_service.save_order(order)
        self.order_service.log_order_state(order)

        if self.order_service.order_failed(order):
            logger.warning("inventory_reservation_failed order_id=%s", order_id)
            return order

        logger.info("payment_capture_started order_id=%s", order_id)
        self.payment_service.capture_payment_mock(order)
        self.order_service.save_order(order)
        self.order_service.log_order_state(order)

        # PAYMENT
        if self.payment_service.is_payment_captured(order):
            logger.info("inventory_sale_finalization_started order_id=%s", order_id)
            self.inventory_service.finalize_inventory_sale(order)

            self.order_service.save_order(order)
            self.order_service.log_order_state(order)
        else:
            logger.warning("payment_capture_failed order_id=%s", order_id)
            self.fail_order(order, "PAYMENT", "Payment capture failed")

            logger.info("inventory_release_started order_id=%s", order_id)
            self.inventory_service.release_order_inventory(order)

            self.order_service.save_order(order)
            self.order_service.log_order_state(order)

            return order

        if self.order_service.order_failed(order):
            logger.warning("inventory_sale_finalization_failed order_id=%s", order_id)
            return order

        # INVOICE
        logger.info("invoice_creation_started order_id=%s", order_id)

        try:
            self.invoice_service.create_invoice(order)
        except Exception:  # catches everything here for now
            self.fail_order(order, "INVOICE", "Invoice creation failed")
            self.order_service.save_order(order)
            self.order_service.log_order_state(order)
            logger.warning("invoice_creation_failed order_id=%s", order_id)
            return order

        self.order_service.save_order(order)
        self.order_service.log_order_state(order)

        # what happens if invoice hasn't been created / solution retry logic

        # NOTIFICATION
        logger.info("notification_send_started order_id=%s", order_id)
        self.notification_service.send_notification(order)
        self.mark_notification_sent(order)
        self.order_service.save_order(order)
        self.order_service.log_order_state(order)
        # what happens if notification hasn't been sent / solution retry logic

        self.mark_order_status(order, "COMPLETED")
        self.order_service.save_order(order)
        logger.info(
            "order_processing_pipeline_finished order_id=%s status=COMPLETED", order_id
        )
        self.order_service.log_order_state(order)

        return order
