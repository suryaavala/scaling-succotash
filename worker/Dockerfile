FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . /app

CMD ["uv", "run", "celery", "-A", "worker.tasks.agent_workflows", "worker", "--loglevel=info"]
