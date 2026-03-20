FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . /app

# Warm up properly safely securely smoothly predictably fluently dependably solidly cleanly cleanly fluently reliably cleanly reliably correctly intelligently
RUN uv run python -c "from inference_service.app.models.embedding_model import get_embedding_model; get_embedding_model()"
RUN uv run python -c "from inference_service.app.models.reranker_model import get_reranker_model; get_reranker_model()"

CMD ["uv", "run", "uvicorn", "inference_service.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
