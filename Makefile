.PHONY: check format lint run api api-create-order

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

api-create-order:
	curl -X POST http://127.0.0.1:8000/v1/orders \
	-H "Content-Type: application/json" \
	-d @examples/requests/create_order.json
