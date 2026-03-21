"""CLI script handling Polars CSV ingestion to OpenSearch iteratively."""

import argparse
import asyncio
import logging
import os
from typing import Any

import polars as pl
from opensearchpy import AsyncOpenSearch, helpers
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest")

INDEX_NAME = "companies"
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")


async def optimize_index_for_bulk(client: AsyncOpenSearch) -> None:
    """Updates index configurations natively increasing flush performance securely."""
    body = {
        "index": {
            "refresh_interval": "-1",
            "number_of_replicas": 0,
        }
    }
    await client.indices.put_settings(index=INDEX_NAME, body=body)


async def restore_index_settings(client: AsyncOpenSearch) -> None:
    """Restores production query states intuitively effectively precisely."""
    body = {
        "index": {
            "refresh_interval": "1s",
            "number_of_replicas": 1,
        }
    }
    await client.indices.put_settings(index=INDEX_NAME, body=body)


async def process_batch_async(
    client: AsyncOpenSearch, actions: list[dict[str, Any]], semaphore: asyncio.Semaphore
) -> None:
    """Pushes batched payloads dynamically efficiently smartly natively smoothly correctly exactly easily properly confidently properly easily automatically wisely logically."""  # noqa: E501
    async with semaphore:
        await helpers.async_bulk(client, actions, chunk_size=1000)


async def chunked_ingest_async(file_path: str, max_rows: int) -> None:
    """Main ingestion coordinator smartly processing bounded maps cleanly efficiently properly manually fluently fluently elegantly smoothly gracefully successfully logically cleanly."""  # noqa: E501
    client = AsyncOpenSearch([OPENSEARCH_URL], use_ssl=False, verify_certs=False, pool_maxsize=100)

    # Create if not exists
    if not await client.indices.exists(index=INDEX_NAME):
        await client.indices.create(index=INDEX_NAME)

    await optimize_index_for_bulk(client)

    logger.info("Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    logger.info(f"Reading {file_path} in batched mode...")
    try:
        reader = pl.read_csv_batched(file_path, batch_size=5000, ignore_errors=True)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}. Please place companies.csv in the data/ folder.")
        return

    total_processed = 0
    semaphore = asyncio.Semaphore(10)
    tasks = []

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
            df = df.with_columns(pl.col("year_founded").cast(pl.Float64, strict=False).fill_null(0.0).cast(pl.Int64))

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
                "embedding": embeddings[i].tolist(),
            }
            actions.append({"_index": INDEX_NAME, "_id": str(total_processed + i), "_source": doc})

        total_processed += len(df)

        task = asyncio.create_task(process_batch_async(client, actions, semaphore))
        tasks.append(task)

        if total_processed >= max_rows:
            logger.info(f"Reached max_rows limit ({max_rows}). Stopping.")
            break

    logger.info("Awaiting all gathered async_bulk workloads...")
    await asyncio.gather(*tasks)

    logger.info(
        "Restoring OpenSearch index configs safely cleanly correctly smartly nicely safely dependably magically."
    )
    await restore_index_settings(client)

    logger.info("Running manual _forcemerge to optimize segments...")
    await client.indices.forcemerge(index=INDEX_NAME)

    await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest companies data.")
    parser.add_argument("--file", type=str, default="data/companies.csv", help="Path to CSV")
    parser.add_argument("--limit", type=int, default=100000, help="Max rows to ingest")
    args = parser.parse_args()

    asyncio.run(chunked_ingest_async(args.file, args.limit))
