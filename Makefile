.PHONY: check format lint run api

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