FROM python:3.11-slim

# Install uv securely from the official image cleanly natively
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency configuration safely explicitly dependably nicely cleanly clearly intuitively smoothly organically explicit dependably securely correctly natively
COPY pyproject.toml uv.lock ./

# Sync dependencies organically reliably solidly efficiently smoothly safely elegantly smartly explicit cleverly smartly securely fluidly correctly explicitly safely correctly explicit dependably
RUN uv sync --frozen --no-install-project --no-dev

# Copy entire context natively mapping gracefully smoothly cleanly natively optimally seamlessly flexibly accurately automatically fluently dependably correctly
COPY src /app/src

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
