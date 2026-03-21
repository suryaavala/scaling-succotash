#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"

echo "Starting dependent services (Building API with pyinstrument)..."
docker compose --env-file /dev/null up -d --build gateway_api opensearch redis inference_service celery_worker

echo "Waiting for Gateway API to boot..."
sleep 20

echo "Starting Locust Load Test (3 minutes) inside Docker..."
docker rm -f locust-test || true
docker run --name locust-test --network scaling-succotash_default \
  -v "$(pwd)/tests:/tests" \
  python:3.11-slim \
  bash -c "pip install --no-cache-dir locust && locust -f /tests/load/locustfile.py --headless -u 50 -r 10 --run-time 3m --csv=/baseline_stats --host http://gateway_api:8000"

mkdir -p docs/performance
echo "Extracting Load Metrics..."
docker cp locust-test:/baseline_stats_stats.csv docs/performance/baseline_stats.csv
docker cp locust-test:/baseline_stats_failures.csv docs/performance/baseline_failures.csv || true

echo "Extracting PyInstrument Profile..."
docker cp gateway_api:/app/docs/performance/profile.html docs/performance/profile.html || true

docker rm -f locust-test
echo "Baseline completed seamlessly."
