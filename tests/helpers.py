import contextlib
import io

from app.models.enums import Currency
from app.models.order import OrderItem
from scripts.reset_json_data import storage_reset


def silent_storage_reset():  # for hidden output
    with contextlib.redirect_stdout(io.StringIO()):
        storage_reset()


def create_default_test_order(order_service, order_id):
    order_service.create_order(
        order_id=order_id,
        customer_id="cust_123",
        items=[
            OrderItem(sku="SKU-001", quantity=2),
            OrderItem(sku="SKU-002", quantity=1),
        ],
        currency=Currency.EUR,
    )
