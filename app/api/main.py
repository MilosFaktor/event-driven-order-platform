from fastapi import FastAPI, Header, HTTPException, Response

from app.core.logging_config import configure_logging_api, get_logger
from app.models.order import OrderItem
from app.models.orders_request import CreateOrderRequest
from app.services.idempotency_service import (
    get_idempotency_keys,
    get_order_id_by_idempotency_key,
)
from app.services.inventory_service import InventoryService
from app.services.invoice_service import get_invoices
from app.services.notification_service import get_notifications
from app.services.order_service import OrderService
from app.services.queue_service import ProcessingQueueService
from app.services.worker_service import process_next_order

app = FastAPI()
order_service = OrderService()
inventory_service = InventoryService()
queue_service = ProcessingQueueService()

configure_logging_api()
logger = get_logger("api")


@app.get("/")
def read_root():
    return {"message": "root"}


# ======= orders section ========


@app.post("/v1/orders", status_code=201)
def create_new_order(
    request: CreateOrderRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    logger.info(
        "create_order_request_received customer_id=%s item_count=%s currency=%s",
        request.customer_id,
        len(request.items),
        request.currency,
    )
    existing_order_id = get_order_id_by_idempotency_key(idempotency_key)

    # idempotency check
    if existing_order_id is not None:
        logger.info("idempotent_order_request_matched order_id=%s", existing_order_id)
        existing_order = order_service.get_order(existing_order_id)

        if existing_order is None:
            logger.error(
                "inconsistent_idempotency_state order_id=%s",
                existing_order_id,
            )
            raise HTTPException(
                status_code=500, detail="Inconsistent idempotency state"
            )
        response.status_code = 200
        logger.info(
            "create_order_response_returned order_id=%s status=%s http_status=200",
            existing_order.order_id,
            existing_order.status,
        )
        return {
            "order_id": existing_order.order_id,
            "status": existing_order.status,
        }

    order_id = order_service.generate_order_id()
    order_service.create_order(
        idempotency_key=idempotency_key,
        order_id=order_id,
        customer_id=request.customer_id,
        items=[
            OrderItem(sku=item.sku, quantity=item.quantity) for item in request.items
        ],
        currency=request.currency,
    )
    queue_service.enqueue_order(order_id)
    logger.info("order_created_and_enqueued order_id=%s", order_id)
    logger.info(
        "create_order_response_returned order_id=%s status=PENDING http_status=201",
        order_id,
    )

    return {"order_id": order_id, "status": "PENDING"}


@app.get("/v1/orders")
def read_orders():
    return order_service.list_orders()


@app.get("/v1/orders/{order_id}")
def read_order(order_id: str):
    logger.info("read_order_request_received order_id=%s", order_id)
    order = order_service.get_order(order_id)
    if order is None:
        logger.warning("read_order_not_found order_id=%s", order_id)
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ========= worker section =========


@app.post("/v1/worker/process-next-order")
def worker_process_next_order():
    logger.info("manual_worker_process_next_requested")
    result = process_next_order()
    if result is None:
        logger.info("manual_worker_process_next_empty_queue")
        raise HTTPException(status_code=200, detail="No orders to process")
    logger.info(
        "manual_worker_process_next_finished order_id=%s status=%s",
        result.order_id,
        result.status,
    )
    return result


# ======== debug section ========


@app.get("/v1/debug/idempotency-keys")
def read_idempotency_keys():
    return get_idempotency_keys()


@app.get("/v1/debug/inventory")
def read_inventory():
    return inventory_service.list_inventory()


@app.get("/v1/debug/processing-queue")
def read_processing_queue():
    return queue_service.list_processing_queue()


@app.get("/v1/debug/invoices")
def read_invoices():
    return get_invoices()


@app.get("/v1/debug/notifications")
def read_notifications():
    return get_notifications()
