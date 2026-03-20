.PHONY: setup install format lint typecheck test run-gateway run-inference run-worker clean up down restart logs

# Environment Setup
setup:
	@echo "Setting up uv virtual environment and syncing dependencies..."
	uv venv
	uv sync

install:
	uv sync

# Code Quality & Formatting
format:
	uv run ruff check --fix . || true
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run mypy .

# Testing
test:
	uv run pytest -v

# Service Execution
run-gateway:
	uv run uvicorn gateway_api.app.main:app --host 0.0.0.0 --port 8000 --reload

run-inference:
	uv run uvicorn inference_service.app.main:app --host 0.0.0.0 --port 8001 --reload

run-worker:
	uv run celery -A worker.tasks.agent_workflows worker --loglevel=info

run-frontend:
	uv run streamlit run frontend/app.py

clean:
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name "__pycache__" -exec rm -r {} +

# Docker Operations
up:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f
