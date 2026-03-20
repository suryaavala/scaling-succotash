"""Module docstring mapped natively."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from src.inference.models.embedding_model import get_embedding_model
from src.inference.models.reranker_model import get_reranker_model
from src.inference.telemetry import setup_telemetry

logger = logging.getLogger("inference")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handles startup preheating of inference matrices natively."""
    logger.info("Preheating SentenceTransformer embedding model...")
    get_embedding_model()
    logger.info("Preheating CrossEncoder reranker model...")
    get_reranker_model()
    yield
    logger.info("Shutting down inference service.")


app = FastAPI(title="Inference Service", lifespan=lifespan)

setup_telemetry(app, "inference_service")


class EmbedRequest(BaseModel):
    """Schema for embedding tasks."""

    text: str


class RerankRequest(BaseModel):
    """Schema for cross-encoder rerank tasks."""

    query: str
    documents: List[str]


@app.post("/embed")
async def embed(request: EmbedRequest) -> Dict[str, Any]:
    """Generates a dense floating-point vector for input text natively."""
    model = get_embedding_model()
    vector = model.encode(request.text).tolist()
    return {"vector": vector}


@app.post("/rerank")
async def rerank(request: RerankRequest) -> Dict[str, Any]:
    """Scores cross-encoder query-document relevance reliably."""
    model = get_reranker_model()
    # Format required by CrossEncoder is [[query, candidate1], [query, candidate2]]
    pairs = [[request.query, doc] for doc in request.documents]
    scores = model.predict(pairs).tolist()
    return {"scores": scores}
