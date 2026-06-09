import contextlib
import io

from fastapi.testclient import TestClient

from app.api.main import app
from scripts.reset_json_data import storage_reset


def silent_storage_reset():  # for hidden output
    with contextlib.redirect_stdout(io.StringIO()):
        storage_reset()


client = TestClient(app)


def test_missing_idempotency_key_rejected():
    silent_storage_reset()

    try:
        response = client.post(
            "/v1/orders",
            json={
                "customer_id": "cust_123",
                "items": [
                    {"sku": "SKU-001", "quantity": 2},
                    {"sku": "SKU-002", "quantity": 1},
                ],
                "currency": "EUR",
            },
        )
        data = response.json()

        assert response.status_code == 422
        assert data["detail"][0]["loc"] == ["header", "Idempotency-Key"]

    finally:
        silent_storage_reset()


def test_create_order_rejects_invalid_body():
    silent_storage_reset()

    try:
        response = client.post(
            "/v1/orders",
            json={"invalid": "body"},
            headers={"Idempotency-Key": "test-key-123"},
        )
        data = response.json()

        assert response.status_code == 422
        assert data["detail"][0]["loc"][0] == "body"

    finally:
        silent_storage_reset()


def test_create_order_returns_pending_saved_order():
    silent_storage_reset()

    try:
        response = client.post(
            "/v1/orders",
            json={
                "customer_id": "cust_123",
                "items": [
                    {"sku": "SKU-001", "quantity": 2},
                    {"sku": "SKU-002", "quantity": 1},
                ],
                "currency": "EUR",
            },
            headers={"Idempotency-Key": "test-key-123"},
        )
        data = response.json()

        assert response.status_code == 201
        assert "order_id" in data
        assert "status" in data
        assert data["status"] == "PENDING"

        order_id = data["order_id"]
        order = client.get(f"/v1/orders/{order_id}")
        saved_order = order.json()

        assert order.status_code == 200
        assert saved_order["order_id"] == order_id
        assert saved_order["customer_id"] == "cust_123"
        assert saved_order["status"] == "PENDING"

    finally:
        silent_storage_reset()


def test_create_order_enqueues_order_id():
    silent_storage_reset()

    try:
        response = client.post(
            "/v1/orders",
            json={
                "customer_id": "cust_123",
                "items": [
                    {"sku": "SKU-001", "quantity": 2},
                    {"sku": "SKU-002", "quantity": 1},
                ],
                "currency": "EUR",
            },
            headers={"Idempotency-Key": "test-key-123"},
        )
        data = response.json()

        assert response.status_code == 201
        assert "order_id" in data
        assert "status" in data
        assert data["status"] == "PENDING"

        order_id = data["order_id"]
        queue = client.get("/v1/debug/processing-queue")
        saved_queue = queue.json()

        assert queue.status_code == 200
        assert saved_queue == [order_id]

    finally:
        silent_storage_reset()


def test_duplicate_idempotency_key_returns_existing_order_without_duplicate_queue_item():
    silent_storage_reset()

    try:
        response_1 = client.post(
            "/v1/orders",
            json={
                "customer_id": "cust_123",
                "items": [
                    {"sku": "SKU-001", "quantity": 2},
                    {"sku": "SKU-002", "quantity": 1},
                ],
                "currency": "EUR",
            },
            headers={"Idempotency-Key": "test-key-123"},
        )
        data_1 = response_1.json()

        assert response_1.status_code == 201
        assert "order_id" in data_1
        assert "status" in data_1
        assert data_1["status"] == "PENDING"

        order_id_1 = data_1["order_id"]

        # duplicate idempotency_key request returns the same order
        response_2 = client.post(
            "/v1/orders",
            json={
                "customer_id": "cust_123",
                "items": [
                    {"sku": "SKU-001", "quantity": 2},
                    {"sku": "SKU-002", "quantity": 1},
                ],
                "currency": "EUR",
            },
            headers={"Idempotency-Key": "test-key-123"},
        )
        data_2 = response_2.json()

        assert response_2.status_code == 200
        assert order_id_1 == data_2["order_id"]

        # duplicate idempotency key does not enqueue twice
        queue = client.get("/v1/debug/processing-queue")
        saved_queue = queue.json()

        assert queue.status_code == 200
        assert saved_queue == [order_id_1]

    finally:
        silent_storage_reset()
