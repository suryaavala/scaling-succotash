import logging
from litellm import completion
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from app.core.opensearch_client import get_opensearch_client, INDEX_NAME
from app.models.schemas import SearchResponse, Company

logger = logging.getLogger("intelligence")

_embed_model = None
def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model

class IntentSchema(BaseModel):
    name: str | None = None
    industry: str | None = None
    size_range: str | None = None
    country: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    requires_agent: bool = False

def extract_intent(query: str) -> IntentSchema:
    try:
        response = completion(
            model="gemini/gemini-3.1-flash-lite-preview",
            messages=[
                {"role": "system", "content": "Extract filtering criteria from the following user query. If the query requires recent news or external data, set requires_agent=True."},
                {"role": "user", "content": query}
            ],
            response_format=IntentSchema
        )
        content = response.choices[0].message.content
        if isinstance(content, str):
            return IntentSchema.model_validate_json(content)
        return IntentSchema.model_validate(content)
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return IntentSchema()

def hybrid_search(query: str, intent: IntentSchema) -> SearchResponse:
    client = get_opensearch_client()
    model = get_embed_model()
    
    query_vector = model.encode(query).tolist()
    
    bool_query = {
        "should": [
            {"match": {"name": {"query": query, "boost": 1.0}}},
            {"match": {"industry": {"query": query, "boost": 0.5}}},
            {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": 20
                    }
                }
            }
        ],
        "minimum_should_match": 1,
        "filter": []
    }
    
    if intent.industry:
        bool_query["filter"].append({"term": {"industry": intent.industry.lower()}})
    if intent.country:
        bool_query["filter"].append({"term": {"country": intent.country.lower()}})
        
    dsl = {
        "size": 20,
        "query": {"bool": bool_query}
    }
    
    response = client.search(index=INDEX_NAME, body=dsl)
    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"] if isinstance(response["hits"]["total"], dict) else response["hits"]["total"]
    
    results = []
    for hit in hits:
        source = hit["_source"]
        company = Company(
            id=hit["_id"],
            name=source.get("name", ""),
            domain=source.get("domain"),
            industry=source.get("industry"),
            locality=source.get("locality"),
            country=source.get("country"),
            size_range=source.get("size_range"),
            year_founded=source.get("year_founded"),
            tags=source.get("tags", [])
        )
        results.append(company)
        
    return SearchResponse(total=total, page=1, size=20, results=results)
