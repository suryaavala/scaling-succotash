"""Centralized application settings via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide configuration loaded from environment variables."""

    # OpenSearch
    opensearch_url: str = "http://localhost:9200"
    opensearch_index: str = "companies"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 100
    redis_cache_ttl: int = 86400

    # Inference
    inference_url: str = "http://localhost:8001"

    # LLM
    gemini_api_key: str = ""
    llm_model: str = "gemini/gemini-3.1-flash-lite-preview"
    mock_llm_latency: float | None = None

    # Telemetry
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    profiling_enabled: bool = False

    model_config = {"env_prefix": "", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton Settings instance."""
    return Settings()
