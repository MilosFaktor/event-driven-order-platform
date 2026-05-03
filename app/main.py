from fastapi import FastAPI

from app.services.order_service import (
    create_order,
    get_all_orders,
    get_order,
    process_order,
)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "root"}


@app.post("/v1/orders")
def create_new_order():
    order_id = "order_001"
    create_order(order_id)
    return process_order(order_id)


@app.get("/v1/orders")
def read_orders():
    return get_all_orders()


@app.get("/v1/orders/{order_id}")
def read_order(order_id: str):
    return get_order(order_id)
