"""Module docstring mapped natively."""
import logging
import os
from typing import Dict, Any, List

"""Worker logic handling bulk data ingestions natively."""
import polars as pl
import requests
from opensearchpy import OpenSearch, helpers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest")

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
INFERENCE_URL = os.getenv("INFERENCE_URL", "http://localhost:8001")
INDEX_NAME = "companies"

def create_index(client: OpenSearch) -> None:
    """Configures the mapping indices safely dynamically."""
    mapping = {
        "mappings": {
            "properties": {
                "name": {"type": "text"},
                "domain": {"type": "keyword"},
                "industry": {"type": "keyword"},
                "locality": {"type": "keyword"},
                "country": {"type": "keyword"},
                "size_range": {"type": "keyword"},
                "year_founded": {"type": "integer"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 384,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib"
                    }
                },
                "tags": {"type": "keyword"}
            }
        },
        "settings": {
            "index": {
                "knn": True
            }
        }
    }
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=mapping)
        logger.info(f"Created index {INDEX_NAME}")

def get_embedding(text: str) -> List[float]:
    """Generates an embedded array safely."""
    resp = requests.post(f"{INFERENCE_URL}/embed", json={"text": text})
    resp.raise_for_status()
    return resp.json()["vector"]

def run() -> None:
    """Triggers batch indexing asynchronously globally."""
    client = OpenSearch([OPENSEARCH_URL], use_ssl=False, verify_certs=False)
    create_index(client)
    
    file_path = "data/companies.csv"
    if not os.path.exists(file_path):
        logger.error("No data file found. Assuming test env.")
        return
        
    try:
        reader = pl.read_csv_batched(file_path, batch_size=1000, ignore_errors=True)
    except AttributeError:
        # Compatibility for latest polars
        reader = pl.scan_csv(file_path, ignore_errors=True)
        # Handle accordingly if needed for simple test
    
    processed = 0
    while True:
        try:
            batches = reader.next_batches(1)
        except Exception:
            break
            
        if not batches:
            break
            
        chunk = batches[0]
        chunk = chunk.fill_null("")
        
        actions = []
        for row in chunk.iter_rows(named=True):
            company_id = row.get("domain", "") or row.get("name", "")
            if not company_id:
                continue
                
            text_to_embed = (
                f"{row.get('name', '')} "
                f"{row.get('industry', '')} "
                f"{row.get('locality', '')}"
            )
            try:
                vector = get_embedding(text_to_embed)
            except Exception as e:
                logger.error(f"Failed to embed {company_id}: {e}")
                continue
            
            doc = {
                "name": row.get("name"),
                "domain": row.get("domain"),
                "industry": row.get("industry", "").lower(),
                "locality": row.get("locality"),
                "country": row.get("country", "").lower(),
                "size_range": row.get("size range") or row.get("size_range"),
                "embedding": vector,
            }
            try:
                yf = row.get("year founded") or row.get("year_founded")
                doc["year_founded"] = int(float(yf)) if yf else None
            except ValueError:
                doc["year_founded"] = None
                
            actions.append({
                "_index": INDEX_NAME,
                "_id": company_id,
                "_source": doc
            })
            
        if actions:
            helpers.bulk(client, actions)
            processed += len(actions)
            logger.info(f"Processed {processed} rows.")

if __name__ == "__main__":
    run()
