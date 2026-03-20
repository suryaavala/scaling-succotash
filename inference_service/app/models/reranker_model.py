"""Reranking Cross-Encoder singleton manager."""
from sentence_transformers import CrossEncoder

_model = None

def get_reranker_model() -> CrossEncoder:
    """Instantiates or safely fetches the globally cached MS-Marco model."""
    global _model
    if _model is None:
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _model
