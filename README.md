# Enterprise B2B Company Search & Intelligence API

## Overview
This repository contains a full-stack, production-grade search system for B2B company data. It includes a high-throughput deterministic search API, an intelligent agentic routing layer leveraging Gemini models, dynamic tagging, and a Streamlit dashboard.

## Features
- **Deterministic Search**: Fast, filter-based OpenSearch boolean DSL queries capable of processing 60 RPS.
- **Intelligent Query Understanding**: Extracts complex intent from natural language (e.g., "tech companies in California") using structured LLM outputs (`gemini-3.1-flash-lite-preview`).
- **Semantic Fallback**: Uses local sentence-transformers (`all-MiniLM-L6-v2`) to perform Hybrid vector search when keyword filtering fails to match concepts.
- **Mock Agentic Search**: Autonomously searches simulated external news data for complex queries.
- **Dynamic Tagging**: Persist custom organizational tags to companies using OpenSearch Painless scripting.
- **Streaming Ingestion**: Highly memory-efficient data chunking pipeline powered by Polars.

## Technical Stack
- **Backend Framework**: FastAPI, Pydantic, Uvicorn
- **Datastore**: OpenSearch 2.11 (Docker Compose)
- **Data Engineering**: Polars
- **Machine Learning**: `sentence-transformers`, `litellm` (Gemini)
- **Frontend**: Streamlit
- **Testing**: Pytest

## Setup & Running Locally

1. **Environment Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Environment Variables**
   Modify `.env` to include your valid `GEMINI_API_KEY`.
3. **Start Datastore**
   Spin up local OpenSearch:
   ```bash
   docker compose up -d
   ```
4. **Data Ingestion**
   Ingest the sample `data/companies.csv` data:
   ```bash
   python scripts/ingest_data.py --limit 1000
   ```
5. **Run Applications**
   Run the backend API:
   ```bash
   uvicorn app.main:app --port 8000
   ```
   Run the frontend UI (in a new terminal):
   ```bash
   source venv/bin/activate
   streamlit run frontend/app.py
   ```

## Documentation
- `docs/architecture.md`: Detail of the three retrieval paradigms and components.
- `docs/assumptions.md`: Core system constraints and design decisions.
- `docs/DEVELOPMENT.md`: Git etiquette, layout, and testing plan.
