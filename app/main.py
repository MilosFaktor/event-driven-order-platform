from fastapi import FastAPI, Header, HTTPException, Response

from app.models.orders import CreateOrderRequest
from app.services.order_service import (
    create_order,
    generate_order_id,
    get_all_orders,
    get_idempotency_keys,
    get_inventory,
    get_order,
    get_order_id_by_idempotency_key,
)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "root"}


@app.post("/v1/orders", status_code=201)
def create_new_order(
    request: CreateOrderRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    existing_order_id = get_order_id_by_idempotency_key(idempotency_key)

    # idempotency check
    if existing_order_id is not None:
        existing_order = get_order(existing_order_id)

        if existing_order is None:
            raise HTTPException(
                status_code=500, detail="Inconsistent idempotency state"
            )
        response.status_code = 200
        return {
            "order_id": existing_order["order_id"],
            "status": existing_order["status"],
        }

    order_id = generate_order_id()
    create_order(
        idempotency_key=idempotency_key,
        order_id=order_id,
        customer_id=request.customer_id,
        items=[item.model_dump() for item in request.items],
        currency=request.currency,
    )

    return {"order_id": order_id, "status": "PENDING"}


@app.get("/v1/orders")
def read_orders():
    return get_all_orders()


@app.get("/v1/orders/{order_id}")
def read_order(order_id: str):
    order = get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/v1/debug/idempotency-keys")
def read_idempotency_keys():
    return get_idempotency_keys()


@app.get("/v1/debug/inventory")
def read_inventory():
    return get_inventory()
