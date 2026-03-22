# syntax=docker/dockerfile:1

# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies (with ML extras for torch/transformers)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --extra ml

# Copy source and finalize install
COPY src/ /app/src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra ml

# Warm up models during build — store in /app/.model_cache
ENV HF_HOME=/app/.model_cache
RUN /app/.venv/bin/python -c "from src.inference.models.embedding_model import get_embedding_model; get_embedding_model()"
RUN /app/.venv/bin/python -c "from src.inference.models.reranker_model import get_reranker_model; get_reranker_model()"


# ── Stage 2: Runtime ─────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends dumb-init curl && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --system appuser && \
    useradd --system --gid appuser --create-home appuser

WORKDIR /app

# Copy venv, source, and model cache — use --chown to avoid separate chown step
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/src /app/src
COPY --from=builder --chown=appuser:appuser /app/.model_cache /app/.model_cache

ENV PATH="/app/.venv/bin:$PATH" \
    HF_HOME="/app/.model_cache"

USER appuser

EXPOSE 8001

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["uvicorn", "src.inference.main:app", "--host", "0.0.0.0", "--port", "8001"]
