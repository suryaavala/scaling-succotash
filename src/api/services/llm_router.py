"""LLM Client Dependency Injection wrapper mapping routing logic."""

import json
import logging
from typing import Any, Dict, Optional, cast

from litellm import acompletion
from pydantic import BaseModel

from src.api.core.redis_cache import get_cached_intent, set_cached_intent

logger = logging.getLogger("llm_router")


class IntentSchema(BaseModel):
    """Schema binding intelligence routing layouts correctly."""

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
    """Injected Singleton evaluating LLM completion queries securely."""

    async def extract_intent(self, query: str) -> tuple[Dict[str, Any], bool]:
        """Resolves JSON intelligence parameters securely."""
        query_lower = query.lower().strip()

        # Heuristic fast-path bypass
        for path, intent in FAST_PATH_HEURISTICS.items():
            if path in query_lower:
                logger.info("Fast-Path Heuristic triggered. Bypassing LLM execution natively.")
                return intent, True

        cached = await get_cached_intent(query)
        if cached is not None:
            logger.info("Found intent in Redis cache. Bypassing LLM execution natively.")
            return cached, True

        import os

        if os.getenv("MOCK_LLM_LATENCY"):
            import asyncio

            await asyncio.sleep(float(os.getenv("MOCK_LLM_LATENCY", "1.0")))
            requires_agent = "recent" in query.lower() or "who" in query.lower()
            return {"industry": "Software", "requires_agent": requires_agent}, False

        try:
            response = await acompletion(
                model="gemini/gemini-3.1-flash-lite-preview",
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
    """Dependency Injection provider for LLM integrations."""
    return LLMClient()
