from fastapi import FastAPI, HTTPException

from app.models.orders import CreateOrderRequest
from app.services.order_service import (
    create_order,
    generate_order_id,
    get_all_orders,
    get_order,
)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "root"}


@app.post("/v1/orders", status_code=201)
def create_new_order(request: CreateOrderRequest):
    order_id = generate_order_id()

    create_order(
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
