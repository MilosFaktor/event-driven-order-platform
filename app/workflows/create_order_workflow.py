from dataclasses import dataclass

from app.core.logging_config import get_logger
from app.exceptions import InconsistentIdempotencyState
from app.models.order import OrderItem
from app.services.idempotency_service import IdempotencyKeysService
from app.services.order_service import OrderService
from app.services.queue_service import ProcessingQueueService

logger = get_logger("create_order.workflow")


@dataclass
class CreateOrderResult:
    order_id: str
    status: str
    created: bool


class CreateOrderWorkflow:
    def __init__(
        self,
        order_service: OrderService | None = None,
        idempotency_service: IdempotencyKeysService | None = None,
        queue_service: ProcessingQueueService | None = None,
    ):

        self.order_service = order_service or OrderService()
        self.idempotency_service = idempotency_service or IdempotencyKeysService()
        self.queue_service = queue_service or ProcessingQueueService()

    def execute(self, request, idempotency_key):

        existing_order_id = self.idempotency_service.get_order_id_by_idempotency_key(
            idempotency_key
        )

        # idempotency check
        if existing_order_id is not None:
            logger.info(
                "idempotent_order_request_matched order_id=%s", existing_order_id
            )
            existing_order = self.order_service.get_order(existing_order_id)

            if existing_order is None:
                logger.error(
                    "inconsistent_idempotency_state order_id=%s",
                    existing_order_id,
                )
                raise InconsistentIdempotencyState("Inconsistent idempotency state")

            logger.info(
                "idempotent_order_result_returned order_id=%s status=%s",
                existing_order.order_id,
                existing_order.status,
            )

            return CreateOrderResult(
                order_id=existing_order.order_id,
                status=existing_order.status,
                created=False,
            )

        order_id = self.order_service.generate_order_id()
        self.order_service.create_order(
            order_id=order_id,
            customer_id=request.customer_id,
            items=[
                OrderItem(sku=item.sku, quantity=item.quantity)
                for item in request.items
            ],
            currency=request.currency,
        )
        self.idempotency_service.save_idempotency_key(idempotency_key, order_id)
        self.queue_service.enqueue_order(order_id)
        logger.info("order_created_and_enqueued order_id=%s", order_id)

        return CreateOrderResult(
            order_id=order_id,
            status="PENDING",
            created=True,
        )
