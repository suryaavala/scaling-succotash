.PHONY: up down test ingest build

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down -v

test:
	PYTHONPATH=. pytest tests/test_gateway.py tests/test_search.py tests/test_intelligence.py
	PYTHONPATH=. pytest tests/test_inference.py

ingest:
	docker compose exec gateway_api python -c "print('Ingestion execution command here')"
