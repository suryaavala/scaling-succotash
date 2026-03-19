import os
from opensearchpy import OpenSearch
from dotenv import load_dotenv

load_dotenv()

OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))

def get_opensearch_client() -> OpenSearch:
    """Returns an OpenSearch client instance."""
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_compress=True,
    )
    return client

INDEX_NAME = "companies"

def create_index(client: OpenSearch):
    """Creates the explicit mapping for companies if it doesn't exist."""
    if not client.indices.exists(index=INDEX_NAME):
        mapping = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            },
            "mappings": {
                "properties": {
                    "name": {"type": "text"},
                    "domain": {"type": "keyword"},
                    "industry": {"type": "keyword"},
                    "locality": {"type": "keyword"},
                    "country": {"type": "keyword"},
                    "size_range": {"type": "keyword"},
                    "year_founded": {"type": "integer"},
                    "tags": {"type": "keyword"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 384,
                        "method": {
                            "name": "hnsw",
                            "engine": "nmslib",
                            "space_type": "cosinesimil"
                        }
                    }
                }
            }
        }
        client.indices.create(index=INDEX_NAME, body=mapping)
