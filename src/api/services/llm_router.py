"""LLM Client Dependency Injection wrapper mapping routing logic."""

import json
import logging
from typing import Any, Dict, Optional, cast

from litellm import completion
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


class LLMClient:
    """Injected Singleton evaluating LLM completion queries securely."""

    def extract_intent(self, query: str) -> Dict[str, Any]:
        """Resolves JSON intelligence parameters synchronously."""
        cached = get_cached_intent(query)
        if cached is not None:
            logger.info(
                "Found intent in Redis cache. Bypassing LLM execution natively."
            )
            return cached

        try:
            response = completion(
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

            set_cached_intent(query, intent)
            return cast(Dict[str, Any], json.loads(content))
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return IntentSchema().model_dump()


def get_llm_client() -> LLMClient:
    """Dependency Injection provider for LLM integrations."""
    return LLMClient()
