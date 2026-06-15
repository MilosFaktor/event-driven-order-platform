from fastapi import FastAPI, Header, HTTPException, Response

from app.core.dependencies import app_dependencies as deps
from app.core.logging_config import configure_logging_api, get_logger
from app.exceptions import InconsistentIdempotencyState
from app.models.orders_request import CreateOrderRequest, CreateOrderResponse
from app.workflows.create_order_workflow import CreateOrderResult

app = FastAPI()

order_service = deps.order_service()
inventory_service = deps.inventory_service()
queue_service = deps.queue_service()
idempotency_service = deps.idempotency_service()
invoice_service = deps.invoice_service()
notification_service = deps.notification_service()
worker_service = deps.worker_service()
create_order_workflow = deps.create_order_workflow()


configure_logging_api()
logger = get_logger("api")


@app.get("/")
def read_root():
    return {"message": "root"}


# ======= orders section ========


@app.post("/v1/orders", status_code=201, response_model=CreateOrderResponse)
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
    try:
        result: CreateOrderResult = create_order_workflow.execute(
            request, idempotency_key
        )
        if result.created is False:
            response.status_code = 200
            logger.info(
                "create_order_idempotent_response_returned order_id=%s status=%s http_status=200",
                result.order_id,
                result.status,
            )

        if result.created is True:
            logger.info(
                "create_order_successful order_id=%s status=%s http_status=201",
                result.order_id,
                result.status,
            )

        return CreateOrderResponse(
            order_id=result.order_id,
            status=result.status,
        )

    except InconsistentIdempotencyState:
        raise HTTPException(status_code=500, detail="Inconsistent idempotency state")


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
    result = worker_service.process_next_order()
    if result is None:
        logger.info("manual_worker_process_next_empty_queue")
        raise HTTPException(status_code=200, detail="No orders to process")

    elif result == "stale_queue_discarded":
        logger.warning("manual_worker_process_next_stale_queue_discarded")
        raise HTTPException(status_code=200, detail="Stale queue discarded")

    logger.info(
        "manual_worker_process_next_finished order_id=%s status=%s",
        result.order_id,
        result.status,
    )
    return result


# ======== debug section ========


@app.get("/v1/debug/idempotency-keys")
def read_idempotency_keys():
    return idempotency_service.list_idempotency_keys()


@app.get("/v1/debug/inventory")
def read_inventory():
    return inventory_service.list_inventory()


@app.get("/v1/debug/processing-queue")
def read_processing_queue():
    return queue_service.list_processing_queue()


@app.get("/v1/debug/invoices")
def read_invoices():
    return invoice_service.list_invoices()


@app.get("/v1/debug/notifications")
def read_notifications():
    return notification_service.list_notifications()
