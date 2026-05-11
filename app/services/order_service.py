from uuid import uuid4

from app.core.logging_config import get_logger
from app.models.order import Order, OrderSteps
from app.repositories.order_repository import OrderRepository
from app.services.idempotency_service import store_idempotency_key

logger = get_logger("order.service")

repo = OrderRepository()


class OrderService:
    def log_order_state(self, order):
        steps = order.steps
        logger.debug(
            "order_saved order_id=%s status=%s steps=(inventory=%s payment=%s invoice=%s notification=%s)",
            order.order_id,
            order.status,
            steps.inventory,
            steps.payment,
            steps.invoice,
            steps.notification,
        )

    def generate_order_id(self):
        orders = repo.get_orders()
        while True:
            order_id = f"ord_{uuid4().hex[:8]}"
            if order_id not in orders.root:
                logger.info("order_id_generated order_id=%s", order_id)
                return order_id

    def order_is_completed(self, order):
        return order.status == "COMPLETED"

    def order_failed(self, order):
        return order.status == "FAILED"

    def order_being_processed(self, order):
        return order.status == "PROCESSING"

    def create_order(self, idempotency_key, order_id, customer_id, items, currency):
        logger.info(
            "order_creation_started order_id=%s customer_id=%s item_count=%s",
            order_id,
            customer_id,
            len(items),
        )

        store_idempotency_key(idempotency_key, order_id)

        orders = repo.get_orders()

        order = Order(
            order_id=order_id,
            customer_id=customer_id,
            items=items,
            currency=currency,
            status="PENDING",
            steps=OrderSteps(
                inventory="PENDING",
                payment="PENDING",
                invoice="PENDING",
                notification="PENDING",
            ),
            failure_reason=None,
        )
        orders.root[order_id] = order
        repo.save_orders(orders)

        logger.info(
            "order_created order_id=%s customer_id=%s status=PENDING",
            order_id,
            customer_id,
        )

    def get_orders(self):
        return repo.get_orders()

    def get_order(self, order_id):
        return repo.get_order(order_id)

    def save_order(self, order):
        repo.save_order(order)
