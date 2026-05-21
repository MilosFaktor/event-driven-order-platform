"""
Experimental order pipeline sandbox.

This file is for exploring workflow logic before moving it into app/services.
The production app should not import from this file.
"""

from app.core.config import Settings
from app.core.logging_config import get_logger
from app.models.order import OrderItem
from app.models.orders_request import CreateOrderRequest, OrderItemRequest
from app.models.types import FailureStep
from app.services.order_service import OrderService
from app.workflows.order_pipeline_service import OrderPipelineService
from scripts.reset_json_data import storage_reset

logger = get_logger("sandbox.pipeline")

PIPELINE_STEPS = [
    FailureStep.RESERVE_INVENTORY,
    FailureStep.CAPTURE_PAYMENT,
    FailureStep.FINALIZE_INVENTORY_SALE,
    FailureStep.CREATE_INVOICE,
    FailureStep.SEND_NOTIFICATION,
]


class Sandbox(OrderPipelineService):
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

        self.mark_order_status(order, "COMPLETED")
        self.order_service.save_order(order)
        logger.info(
            "order_processing_pipeline_finished order_id=%s status=COMPLETED", order_id
        )
        self.order_service.log_order_state(order)

        return order


def run_resumable_order_pipeline():
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

    order_pipeline = Sandbox(settings=settings)

    processed_order = order_pipeline.process_order("ord_123")
    print(processed_order)

    storage_reset()


run_resumable_order_pipeline()
