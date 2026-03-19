# Architecture

## Overview
The Enterprise B2B Company Search & Intelligence API relies on FastAPI as the core web server and OpenSearch as the primary datastore and vector database.

## Components
1. **API Gateway (FastAPI)**: Routes standard search and intelligent search requests. Includes latency metrics via middleware.
2. **Datastore (OpenSearch)**: Stores structured entity properties alongside 384-dimensional dense vectors generated from company text representations.
3. **Intelligence Layer (LiteLLM + Gemini)**: Acts as an orchestrator for intent parsing. If standard search parameters are insufficient, it formulates vector search queries or calls external agentic APIs.
4. **Data Ingestion Pipeline**: Built on Polars to stream large dataset sizes (7M rows) directly into OpenSearch, generating inline local embeddings using `sentence-transformers`.
