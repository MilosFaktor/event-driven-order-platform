from uuid import uuid4

from app.core.logging_config import get_logger
from app.models.order import Order, OrderItem, Orders, OrderSteps
from app.models.types import Currency
from app.repositories.order_repository import OrderRepository

logger = get_logger("order.service")


def build_pending_order(
    order_id: str,
    customer_id: str,
    items: list[OrderItem],
    currency: Currency,
) -> Order:
    return Order(
        order_id=order_id,
        customer_id=customer_id,
        items=items,
        currency=currency,
        status="PENDING",
        steps=OrderSteps(),
        failure_reason=None,
        failure_step=None,
    )


class OrderService:
    def __init__(self, repo: OrderRepository | None = None):
        if repo is None:
            self.repo = OrderRepository()
        else:
            self.repo = repo

    def log_order_state(self, order: Order) -> None:
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

    def generate_order_id(self) -> str:
        orders = self.repo.list_orders()
        while True:
            order_id = f"ord_{uuid4().hex[:8]}"
            if order_id not in orders.root:
                logger.info("order_id_generated order_id=%s", order_id)
                return order_id

    def order_is_completed(self, order: Order) -> bool:
        return order.status == "COMPLETED"

    def order_failed(self, order: Order) -> bool:
        return order.status == "FAILED"

    def order_being_processed(self, order: Order) -> bool:
        return order.status == "PROCESSING"

    def create_order(
        self,
        order_id: str,
        customer_id: str,
        items: list[OrderItem],
        currency: Currency,
    ) -> None:
        logger.info(
            "order_creation_started order_id=%s customer_id=%s item_count=%s",
            order_id,
            customer_id,
            len(items),
        )

        order = build_pending_order(order_id, customer_id, items, currency)

        self.repo.save_order(order)

        logger.info(
            "order_created order_id=%s customer_id=%s status=PENDING",
            order_id,
            customer_id,
        )

    def list_orders(self) -> Orders:
        return self.repo.list_orders()

    def get_order(self, order_id: str) -> Order | None:
        return self.repo.get_order(order_id)

    def save_order(self, order: Order) -> None:
        self.repo.save_order(order)
