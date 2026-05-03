.PHONY: check format lint run api api-create-order-1 api-create-order-2 api-get-orders api-get-idem-keys api-get-inventory

check:
	uv run ruff check .

format:
	uv run ruff format .

lint:
	uv run ruff check . --fix
	uv run ruff format .

run:
	uv run python app/main.py

api:
	uv run uvicorn app.main:app --reload

api-create-order-1:
	curl -X POST http://127.0.0.1:8000/v1/orders \
	-H "Content-Type: application/json" \
	-H "Idempotency-Key: demo-key-123" \
	-d @examples/requests/create_order.json

api-create-order-2:
	curl -X POST http://127.0.0.1:8000/v1/orders \
	-H "Content-Type: application/json" \
	-H "Idempotency-Key: demo-key-456" \
	-d @examples/requests/create_order.json

api-get-idem-keys:
	curl http://127.0.0.1:8000/v1/debug/idempotency-keys | jq

api-get-inventory:
	curl http://127.0.0.1:8000/v1/debug/inventory | jq

api-get-orders:
	curl http://127.0.0.1:8000/v1/orders | jq

