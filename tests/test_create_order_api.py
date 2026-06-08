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

        assert response.status_code == 422
        data = response.json()
        assert data["detail"][0]["loc"] == ["header", "Idempotency-Key"]

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

        assert response.status_code == 201

        data = response.json()

        assert "order_id" in data
        assert "status" in data
        assert data["status"] == "PENDING"

        order_id = data["order_id"]
        order = client.get(f"/v1/orders/{order_id}")

        assert order.status_code == 200

        saved_order = order.json()
        assert saved_order["order_id"] == order_id
        assert saved_order["customer_id"] == "cust_123"
        assert saved_order["status"] == "PENDING"

    finally:
        silent_storage_reset()


if __name__ == "__main__":
    test_create_order_returns_pending_saved_order()
