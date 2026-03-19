from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from app.models.embedding_model import get_embedding_model
from app.models.reranker_model import get_reranker_model

app = FastAPI(title="Inference Service")

from app.telemetry import setup_telemetry
setup_telemetry(app, "inference_service")

class EmbedRequest(BaseModel):
    text: str

class EmbedResponse(BaseModel):
    vector: List[float]

class RerankRequest(BaseModel):
    query: str
    candidates: List[str]

class RerankResponse(BaseModel):
    scores: List[float]

@app.on_event("startup")
async def startup_event():
    # Load models into memory permanently on container boot
    get_embedding_model()
    get_reranker_model()

@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    model = get_embedding_model()
    vector = model.encode(request.text).tolist()
    return EmbedResponse(vector=vector)

@app.post("/rerank", response_model=RerankResponse)
async def rerank(request: RerankRequest):
    model = get_reranker_model()
    # Format required by CrossEncoder is [[query, candidate1], [query, candidate2]]
    pairs = [[request.query, doc] for doc in request.candidates]
    scores = model.predict(pairs).tolist()
    return RerankResponse(scores=scores)
