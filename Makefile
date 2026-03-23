export VIRTUAL_ENV=
.PHONY: help setup install install-all archive format lint typecheck test test-fast test-e2e ci ci-all run-gateway run-inference run-worker clean up down restart logs ingest all install-hooks

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
	@echo "	   archive		   Archive repo for notebooklm"
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
	@echo ""
	@echo "  \033[1;36mCI Pipelines\033[0m"
	@echo "    ci              Fast local CI: lint → typecheck → test-fast"
	@echo "    ci-all          Full local CI: lint → format → typecheck → test"
	@echo "    all             Full pipeline: install → format → lint → typecheck → test"
	@echo ""
	@echo "  \033[1;36mServices (Local)\033[0m"
	@echo "    run-gateway     Start the FastAPI gateway on :8000 with hot-reload"
	@echo "    run-inference   Start the inference server on :8001 with hot-reload"
	@echo "    run-worker      Start the Celery worker for agentic search workflows"
	@echo "    run-frontend    Start the Streamlit frontend UI"
	@echo ""
	@echo "  \033[1;36mKubernetes (Local kind)\033[0m"
	@echo "    cluster-up      Provision local kind cluster and NGINX Ingress"
	@echo "    cluster-down    Destroy local kind cluster"
	@echo "    docker-build-local Build images and load into kind cluster"
	@echo "    deploy          Deploy Kubernetes manifests via Kustomize"
	@echo "    port-forward    Forward localhost:8000 to Gateway API"
	@echo "    logs            Tail K8s logs of the Gateway API pod"
	@echo "    k9s             Open k9s terminal UI for local cluster"
	@echo ""
	@echo "  \033[1;36mDocker Compose (Legacy)\033[0m"
	@echo "    up              Build and start all Docker Compose services"
	@echo "    down            Stop and remove all Docker Compose services"
	@echo "    restart         Restart all Docker Compose services"
	@echo "    logs-compose    Tail logs from all Docker Compose services"
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

archive:
	uv run python3 scripts/archive_repo.py

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
ci-all: lint format typecheck test

# Testing
test:
	uv run --all-extras pytest -v

test-fast:
	uv run --all-extras pytest -m "not e2e" -v

test-e2e: up
	uv run --all-extras pytest -m e2e -v --no-cov

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

# Kubernetes Operations (kind)
cluster-up:
	@echo "Provisioning local kind cluster..."
	kind create cluster --config k8s/kind-config.yaml
	@echo "Installing NGINX Ingress controller..."
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
	kubectl wait --namespace ingress-nginx \
	  --for=condition=ready pod \
	  --selector=app.kubernetes.io/component=controller \
	  --timeout=90s

cluster-down:
	kind delete cluster

docker-build-local:
	@echo "Building local Docker images..."
	docker build -t scaling-succotash-gateway_api:latest -f src/api/Dockerfile .
	docker build -t scaling-succotash-inference_service:latest -f src/inference/Dockerfile .
	docker build -t scaling-succotash-celery_worker:latest -f src/worker/Dockerfile .
	@echo "Loading images into kind cluster..."
	kind load docker-image scaling-succotash-gateway_api:latest
	kind load docker-image scaling-succotash-inference_service:latest
	kind load docker-image scaling-succotash-celery_worker:latest

deploy:
	kubectl apply -k k8s/base

port-forward:
	kubectl port-forward svc/gateway-api 8000:8000

logs:
	kubectl logs -l app=gateway-api -f

k9s:
	k9s

# Docker Compose Operations (Legacy)
up:
	docker compose up --build -d --wait --wait-timeout 360

down:
	docker compose down

restart:
	docker compose restart

logs-compose:
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
