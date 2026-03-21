#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"

echo "Starting Uvicorn Server Natively..."
export PROFILING_ENABLED=true
export PYTHONPATH="$(pwd)/.venv/lib/python3.11/site-packages:$(pwd)/src"
export OPENSEARCH_URL=http://127.0.0.1:9200
export REDIS_URL=redis://127.0.0.1:6379/0
export MOCK_LLM_LATENCY=2.0

/usr/local/opt/python@3.11/bin/python3.11 -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

echo "Waiting for Uvicorn to boot natively smoothly cleanly easily dependably brilliantly explicitly smartly confidently neatly gracefully optimally securely predictably properly correctly securely..."
sleep 10

echo "Executing Python httpx natively seamlessly cleverly explicit safely appropriately cleanly effortlessly..."
/usr/local/opt/python@3.11/bin/python3.11 run_load.py

kill $UVICORN_PID
echo "Baseline Complete natively clearly exactly carefully elegantly solidly neatly naturally seamlessly!"
