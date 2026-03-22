export VIRTUAL_ENV=
.PHONY: setup install format lint typecheck test test-fast test-e2e test-all run-gateway run-inference run-worker clean up down restart logs ingest all install-hooks

# Environment Setup
setup:
	@echo "Setting up uv virtual environment and syncing dependencies..."
	uv venv
	uv sync

install:
	uv sync

all: install format lint typecheck test

# Code Quality & Formatting
format:
	uv run ruff check --fix . || true
	uv run ruff format .

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy src/ tests/

# Testing
test:
	uv run pytest -v

test-fast:
	uv run pytest -m "not e2e" -v

test-e2e:
	uv run pytest -m e2e -v

test-all:
	uv run pytest -v

# Pre-commit Hooks
install-hooks:
	uv run pre-commit install

# Service Execution
run-gateway:
	uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

run-inference:
	uv run uvicorn src.inference.main:app --host 0.0.0.0 --port 8001 --reload

run-worker:
	uv run celery -A src.worker.agent_workflows worker --loglevel=info

run-frontend:
	uv run streamlit run src/frontend/app.py

clean:
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .uv_cache
	rm -rf .sandbox_venv
	rm -rf .tmp
	rm -rf archive
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

# Data Management
download-data:
	uv run python scripts/download_dataset.py

generate-data:
	uv run python scripts/generate_mock_data.py --rows 100000

ingest-sample:
	DATA_FILE=mock_companies.csv LIMIT=100000 docker compose run --rm data_ingester

ingest-full:
	DATA_FILE=companies.csv LIMIT=7000000 docker compose run --rm data_ingester

ingest:
	uv run python scripts/ingest_data.py
