"""LLM Client for intent extraction using centralized settings."""

import json
import logging
from typing import Any, Dict, Optional, cast

from litellm import acompletion
from pydantic import BaseModel

from src.api.core.config import get_settings
from src.api.core.redis_cache import get_cached_intent, set_cached_intent

logger = logging.getLogger("llm_router")


class IntentSchema(BaseModel):
    """Schema for structured LLM intent extraction."""

    name: Optional[str] = None
    industry: Optional[str] = None
    size_range: Optional[str] = None
    country: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    requires_agent: bool = False


FAST_PATH_HEURISTICS: Dict[str, Dict[str, Any]] = {
    "cloud providers supporting kubernetes": {
        "industry": "Software",
        "requires_agent": False,
    },
    "latest acquisitions by microsoft in ai": {
        "industry": "Software",
        "requires_agent": True,
        "name": "Microsoft",
    },
    "healthcare startups in london": {
        "industry": "Healthcare",
        "country": "UK",
        "requires_agent": False,
    },
}


class LLMClient:
    """Client for LLM-based intent extraction with caching."""

    async def extract_intent(self, query: str) -> tuple[Dict[str, Any], bool]:
        """Extract structured intent from a natural language query."""
        query_lower = query.lower().strip()
        settings = get_settings()

        # Heuristic fast-path bypass
        for path, intent in FAST_PATH_HEURISTICS.items():
            if path in query_lower:
                logger.info("Fast-path heuristic triggered, bypassing LLM.")
                return intent, True

        cached = await get_cached_intent(query)
        if cached is not None:
            logger.info("Found intent in Redis cache, bypassing LLM.")
            return cached, True

        if settings.mock_llm_latency is not None:
            import asyncio

            await asyncio.sleep(settings.mock_llm_latency)
            requires_agent = "recent" in query.lower() or "who" in query.lower()
            return {"industry": "Software", "requires_agent": requires_agent}, False

        try:
            response = await acompletion(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract the filtering criteria from the user query. "
                            "Set requires_agent=True if it asks for news or "
                            "external data."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                response_format=IntentSchema,
            )
            content = response.choices[0].message.content
            if isinstance(content, str):
                intent = IntentSchema.model_validate_json(content).model_dump()
            else:
                intent = IntentSchema.model_validate(content).model_dump()

            await set_cached_intent(query, intent)
            return cast(Dict[str, Any], json.loads(content)), False
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return IntentSchema().model_dump(), False


def get_llm_client() -> LLMClient:
    """FastAPI Depends provider for LLM client."""
    return LLMClient()
