# Assumptions

1. **Local Constraints**: Due to hardware limitations on a local laptop, OpenSearch JVM memory is capped at 1GB, and ingestion pipelines process 5000 rows per batch. The full 7 million row dataset will not fit entirely in memory during processing.
2. **Embedding Model**: `all-MiniLM-L6-v2` runs locally because offloading 7M embeddings to commercial APIs would be prohibitively slow and expensive for a local development assessment.
3. **Data Availability**: Based on Kaggle's open 7M parameter dataset, we assume fields like `name`, `industry`, `locality`, and `domain` are primary identifiers. Missing years or integer attributes default to `0`.
