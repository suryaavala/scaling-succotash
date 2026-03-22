export VIRTUAL_ENV=
.PHONY: help setup install install-all format lint typecheck test test-fast test-e2e test-all ci ci-all run-gateway run-inference run-worker clean up down restart logs ingest all install-hooks

# Default target
help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║        Enterprise B2B Company Search — Make Targets             ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  \033[1;36mSetup & Install\033[0m"
	@echo "    setup           Create a uv virtual environment and sync all dependencies"
	@echo "    install         Sync dependencies into the existing virtual environment"
	@echo "    install-all     Sync all dependencies into the existing virtual environment"
	@echo "    install-hooks   Install pre-commit hooks (ruff, mypy, whitespace fixers)"
	@echo ""
	@echo "  \033[1;36mCode Quality\033[0m"
	@echo "    format          Auto-fix lint issues and reformat code with ruff"
	@echo "    lint            Check for lint errors and verify formatting (no writes)"
	@echo "    typecheck       Run mypy strict type checking on src/ and tests/"
	@echo ""
	@echo "  \033[1;36mTesting\033[0m"
	@echo "    test            Run the full test suite (unit + e2e) with verbose output"
	@echo "    test-fast       Run only unit tests (excludes e2e), enforces 85% coverage"
	@echo "    test-e2e        Run only end-to-end tests (requires running Docker services)"
	@echo "    test-all        Run every test (alias for test)"
	@echo ""
	@echo "  \033[1;36mCI Pipelines\033[0m"
	@echo "    ci              Fast local CI: lint → typecheck → test-fast"
	@echo "    ci-all          Full local CI: lint → format → typecheck → test-all"
	@echo "    all             Full pipeline: install → format → lint → typecheck → test"
	@echo ""
	@echo "  \033[1;36mServices (Local)\033[0m"
	@echo "    run-gateway     Start the FastAPI gateway on :8000 with hot-reload"
	@echo "    run-inference   Start the inference server on :8001 with hot-reload"
	@echo "    run-worker      Start the Celery worker for agentic search workflows"
	@echo "    run-frontend    Start the Streamlit frontend UI"
	@echo ""
	@echo "  \033[1;36mDocker\033[0m"
	@echo "    up              Build and start all Docker Compose services (detached)"
	@echo "    down            Stop and remove all Docker Compose services"
	@echo "    restart         Restart all Docker Compose services"
	@echo "    logs            Tail logs from all Docker Compose services"
	@echo ""
	@echo "  \033[1;36mData Management\033[0m"
	@echo "    download-data   Download the 7M-row Kaggle company dataset"
	@echo "    generate-data   Generate 100k synthetic mock company rows via Faker"
	@echo "    ingest-sample   Ingest 100k mock rows via containerized data_ingester"
	@echo "    ingest-full     Ingest full 7M Kaggle dataset via containerized ingester"
	@echo "    ingest          Run the ingestion script directly (non-containerized)"
	@echo ""
	@echo "  \033[1;36mHousekeeping\033[0m"
	@echo "    clean           Remove .venv, caches, __pycache__, and temp files"
	@echo ""


# Environment Setup
setup:
	@echo "Setting up uv virtual environment and syncing dependencies..."
	uv venv
	uv sync

install:
	uv sync

install-all:
	uv sync --all-extras --dev

all: install format lint typecheck test

# Code Quality & Formatting
format:
	uv run ruff check --fix . || true
	uv run ruff format .

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy src/

# Full local CI pipeline
ci: lint typecheck test-fast

# Full CI pipeline
ci-all: lint format typecheck test-all

# Testing
test:
	uv run pytest -v

test-fast:
	uv run pytest -m "not e2e" -v

test-e2e:
	uv run pytest -m e2e -v --no-cov

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
	rm -rf .coverage
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
