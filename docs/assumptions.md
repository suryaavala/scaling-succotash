# Technical Assumptions

To successfully run this robust engine locally, the following architectural shortcuts and constraints were enacted based on the system spec:

1. **System Memory Constraint**:
   To prevent Out-Of-Memory (OOM) failures while running simultaneously with OpenSearch and Machine Learning inference, OpenSearch is capped within `docker-compose.yml` to strict 512mb/1GB thresholds using JVM `-Xms` and `-Xmx` variables.
   
2. **Library Versions**:
   In order to allow PyTorch to execute `sentence-transformers` inference locally across multiple processor architectures (Apple Silicon M-series or Intel), the environment requires strict usage of `numpy<2.0.0` and `transformers<4.39` to avoid binary incompatibility errors in the open source ecosystem.

3. **Agent Implementation**:
   While production systems would utilize tools like SerpAPI or custom RAG pipelines to find "Recent News", this project implements a mocked static function that uniformly returns a simulated funding insight to demonstrate the autonomous context synthesis pattern without massive cost.
   
4. **Data Deduplication**:
   User tagging uses basic `contains()` rules in the Painless script to avoid exact duplicates (case-insensitive string matching logic occurs in the python router boundary).

5. **LLM Pricing Efficiency**:
   We leverage `gemini-3.1-flash-lite-preview` via LiteLLM to maintain blindingly fast intent extraction at the absolute lowest cost, meeting the required scalability of 30 RPS for intelligent tasks.
