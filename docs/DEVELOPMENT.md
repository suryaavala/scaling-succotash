# Development Guide

## Environment Setup
Follow instructions in `README.md` to run `docker compose up -d` and set up the Python environment using `venv`. Ensure that `GEMINI_API_KEY` is set in the `.env` file.

## Phase Strategy
The repository is built iteratively following structured phases:
- **Phase 1**: Infrastructure (Docker, FastAPI skeleton)
- **Phase 2**: OpenSearch Schema & chunked Polars ingestion script
- **Phase 3**: Deterministic Search API (Standard DSL logic)
- **Phase 4**: Intelligence Layer (Agentic search using LiteLLM/Gemini)
- **Phase 5**: Tagging API
- **Phase 6**: Streamlit UI

All code should follow semantic commit guidelines (`feat:`, `chore:`, `fix:`).

## Testing
When adding new functionality, append test suites in `tests/`. Currently leveraging `pytest` and `httpx`.
