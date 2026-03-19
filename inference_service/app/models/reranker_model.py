from sentence_transformers import CrossEncoder

_model = None

def get_reranker_model():
    global _model
    if _model is None:
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _model
