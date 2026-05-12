from app.adapters.json_order_adapter import JsonOrderAdapter
from app.core.logging_config import get_logger
from app.models.order import Order, Orders

logger = get_logger("order.repo")


class OrderRepository:
    def __init__(self, adapter: JsonOrderAdapter | None = None):
        if adapter is None:
            self.adapter = JsonOrderAdapter()
        else:
            self.adapter = adapter

    def list_orders(self) -> Orders:
        orders = self.adapter.load_orders()
        logger.debug("orders_loaded count=%s", len(orders.root))

        return orders

    def get_order(self, order_id: str) -> Order | None:
        orders = self.list_orders()
        order = orders.root.get(order_id)

        if order is None:
            logger.warning("order_not_found order_id=%s", order_id)
        else:
            logger.info(
                "order_loaded order_id=%s status=%s",
                order_id,
                order.status,
            )

        return order

    def save_orders(self, orders: Orders) -> None:
        self.adapter.save_orders(orders)
        logger.debug("orders_saved count=%s", len(orders.root))

    def save_order(self, order: Order) -> None:
        orders = self.list_orders()
        orders.root[order.order_id] = order

        self.save_orders(orders)
        logger.debug(
            "order_saved order_id=%s status=%s",
            order.order_id,
            order.status,
        )
