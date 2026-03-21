FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src /app/src

CMD ["uv", "run", "celery", "-A", "src.worker.agent_workflows", "worker", "--loglevel=info"]
