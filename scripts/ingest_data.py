"""CLI script handling Polars CSV ingestion to OpenSearch."""
import argparse
import logging
import os
import sys
from typing import Any

import polars as pl
from opensearchpy import helpers
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.opensearch_client import INDEX_NAME, create_index, get_opensearch_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest")

def chunked_ingest(file_path: str, max_rows: int) -> None:
    """Batches CSV reads pushing indexed aggregations into memory maps."""
    client = get_opensearch_client()
    create_index(client)
    
    logger.info("Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    logger.info(f"Reading {file_path} in batched mode...")
    try:
        reader = pl.read_csv_batched(file_path, batch_size=5000, ignore_errors=True)
    except FileNotFoundError:
        logger.error(
            f"File not found: {file_path}. "
            "Please place companies.csv in the data/ folder."
        )
        return
        
    total_processed = 0
    while True:
        batches = reader.next_batches(1)
        if not batches:
            break
            
        df = batches[0]
        logger.info(f"Processing chunk of {len(df)} rows. Total processed so far: {total_processed}")
        
        str_cols = [col for col in df.columns if df[col].dtype == pl.String]
        for col in str_cols:
            df = df.with_columns(pl.col(col).str.to_lowercase().fill_null(""))
            
        if "year founded" in df.columns:
            df = df.rename({"year founded": "year_founded"})
        if "size range" in df.columns:
            df = df.rename({"size range": "size_range"})
            
        if "year_founded" in df.columns:
            df = df.with_columns(
                pl.col("year_founded")
                .cast(pl.Float64, strict=False)
                .fill_null(0.0)
                .cast(pl.Int64)
            )
        
        texts_to_embed = []
        rows = df.to_dicts()
        for row in rows:
            name = str(row.get("name", ""))
            industry = str(row.get("industry", ""))
            locality = str(row.get("locality", ""))
            text = f"{name} {industry} {locality}".strip()
            texts_to_embed.append(text)
            
        embeddings = model.encode(texts_to_embed, show_progress_bar=False)
        
        actions = []
        for i, row in enumerate(rows):
            doc = {
                "name": row.get("name", ""),
                "domain": row.get("domain", ""),
                "industry": row.get("industry", ""),
                "locality": row.get("locality", ""),
                "country": row.get("country", ""),
                "size_range": row.get("size_range", ""),
                "year_founded": int(row.get("year_founded", 0)),
                "tags": [],
                "embedding": embeddings[i].tolist()
            }
            actions.append({
                "_index": INDEX_NAME,
                "_source": doc
            })
            
        helpers.bulk(client, actions, chunk_size=1000)
        total_processed += len(df)
        
        if total_processed >= max_rows:
            logger.info(f"Reached max_rows limit ({max_rows}). Stopping.")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest companies data.")
    parser.add_argument(
        "--file", type=str, default="data/companies.csv", help="Path to CSV"
    )
    parser.add_argument(
        "--limit", type=int, default=100000, help="Max rows to ingest"
    )
    args = parser.parse_args()
    
    chunked_ingest(args.file, args.limit)
