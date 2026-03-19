.PHONY: up down test ingest build

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down -v

test:
	PYTHONPATH=. pytest tests/

ingest:
	docker compose exec gateway_api python -c "print('Ingestion execution command here')"
