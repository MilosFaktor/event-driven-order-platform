import contextlib
import io

from app.core.config import Settings
from app.models.inventory import Inventory
from app.models.order import OrderItem
from app.models.types import FailureStep
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.workflows.order_pipeline_service import OrderPipelineService
from scripts.reset_json_data import storage_reset


def silent_storage_reset():  # for hidden output
    with contextlib.redirect_stdout(io.StringIO()):
        storage_reset()


def test_inventory_reservation_failure_fails_order_without_running_later_steps():
    silent_storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=3,
            retry_base_delay_seconds=1,
            retry_backoff_multiplier=2,
        )

        order_id = "ord_123"

        order_service = OrderService()
        inventory_service = InventoryService()
        pipeline = OrderPipelineService(
            settings=settings,
            order_service=order_service,
            inventory_service=inventory_service,
        )

        inventory = {
            "SKU-001": {
                "name": "Laptop",
                "price": 950.5,
                "available_stock": 10,
                "reserved_stock": 0,
                "sold_stock": 0,
            },
            "SKU-002": {
                "name": "Mouse",
                "price": 30,
                "available_stock": 10,
                "reserved_stock": 0,
                "sold_stock": 0,
            },
        }
        inventory_service.save_inventory(Inventory(root=inventory))

        order_service.create_order(
            order_id=order_id,
            customer_id="cust_123",
            items=[
                OrderItem(sku="SKU-001", quantity=20),
                OrderItem(sku="SKU-002", quantity=10),
            ],
            currency="EUR",
        )

        processed_order = pipeline.process_order(order_id)

        assert processed_order.status == "FAILED"
        assert processed_order.failure_step == FailureStep.RESERVE_INVENTORY
        assert processed_order.failure_reason == "Insufficient stock for Laptop"
        assert processed_order.steps.reserve_inventory == "FAILED"
        assert processed_order.steps.capture_payment == "PENDING"
        assert processed_order.steps.finalize_inventory_sale == "PENDING"
        assert processed_order.steps.create_invoice == "PENDING"
        assert processed_order.steps.send_notification == "PENDING"

    finally:
        silent_storage_reset()


def test_inventory_reservation_failure_does_not_partially_reserve_stock():
    silent_storage_reset()

    try:
        settings = Settings(
            max_processing_attempts=3,
            retry_base_delay_seconds=1,
            retry_backoff_multiplier=2,
        )

        order_id = "ord_123"

        order_service = OrderService()
        inventory_service = InventoryService()
        pipeline = OrderPipelineService(
            settings=settings,
            order_service=order_service,
            inventory_service=inventory_service,
        )

        inventory = {
            "SKU-001": {
                "name": "Laptop",
                "price": 950.5,
                "available_stock": 10,
                "reserved_stock": 0,
                "sold_stock": 0,
            },
            "SKU-002": {
                "name": "Mouse",
                "price": 30,
                "available_stock": 10,
                "reserved_stock": 0,
                "sold_stock": 0,
            },
        }
        inventory_service.save_inventory(Inventory(root=inventory))

        order_service.create_order(
            order_id=order_id,
            customer_id="cust_123",
            items=[
                OrderItem(sku="SKU-001", quantity=5),
                OrderItem(sku="SKU-002", quantity=20),
            ],
            currency="EUR",
        )

        processed_order = pipeline.process_order(order_id)

        assert processed_order.status == "FAILED"
        assert processed_order.failure_step == FailureStep.RESERVE_INVENTORY
        assert processed_order.failure_reason == "Insufficient stock for Mouse"
        assert processed_order.steps.reserve_inventory == "FAILED"

        assert inventory_service.list_inventory().model_dump() == {
            "SKU-001": {
                "name": "Laptop",
                "price": 950.5,
                "available_stock": 10,
                "reserved_stock": 0,
                "sold_stock": 0,
            },
            "SKU-002": {
                "name": "Mouse",
                "price": 30.0,
                "available_stock": 10,
                "reserved_stock": 0,
                "sold_stock": 0,
            },
        }

    finally:
        silent_storage_reset()
