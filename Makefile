.PHONY: check format lint run api api-create-order-1 api-create-order-2 \
	api-get-orders api-get-idem-keys api-get-inventory worker api-get-q \
	worker-process-next sandbox api-get-ntfs api-get-invoices storage-reset \
	api-local api-prod worker-local worker-prod loc-app

check:
	uv run ruff check .

format:
	uv run ruff format .

lint:
	uv run ruff check . --fix
	uv run ruff format .

loc-app:
	npx cloc app

run:
	uv run python -m app.main

sandbox:
	uv run python -m experiments.order_pipeline_sandbox

worker:
	uv run python -m app.workers.order_worker

api:
	uv run uvicorn app.api.main:app --reload

api-local:
	ENV_FILE=.env.local uv run uvicorn app.api.main:app --reload

api-prod:
	ENV_FILE=.env.prod uv run uvicorn app.api.main:app

worker-local:
	ENV_FILE=.env.local uv run python -m app.workers.order_worker

worker-prod:
	ENV_FILE=.env.prod uv run python -m app.workers.order_worker

api-create-order-1:
	curl -X POST http://127.0.0.1:8000/v1/orders \
	-H "Content-Type: application/json" \
	-H "Idempotency-Key: demo-key-123" \
	-d @examples/requests/create_order_1.json

api-create-order-2:
	curl -X POST http://127.0.0.1:8000/v1/orders \
	-H "Content-Type: application/json" \
	-H "Idempotency-Key: demo-key-456" \
	-d @examples/requests/create_order_2.json

api-get-orders:
	curl http://127.0.0.1:8000/v1/orders | jq

worker-process-next:
	curl -X POST http://127.0.0.1:8000/v1/worker/process-next-order


# ========== debug =============

api-get-q:
	curl http://127.0.0.1:8000/v1/debug/processing-queue | jq

api-get-ntfs:
	curl http://127.0.0.1:8000/v1/debug/notifications | jq

api-get-invoices:
	curl http://127.0.0.1:8000/v1/debug/invoices | jq

api-get-idem-keys:
	curl http://127.0.0.1:8000/v1/debug/idempotency-keys | jq

api-get-inventory:
	curl http://127.0.0.1:8000/v1/debug/inventory | jq


# ============ storage =============

storage-reset:
	uv run python -m scripts.reset_json_data
