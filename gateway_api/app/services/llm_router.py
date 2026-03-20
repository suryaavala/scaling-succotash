"""Module docstring mapped natively."""
import logging
from typing import Optional

from app.core.redis_cache import get_cached_intent, set_cached_intent
from litellm import completion
from pydantic import BaseModel

logger = logging.getLogger("llm_router")

class IntentSchema(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    size_range: Optional[str] = None
    country: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    requires_agent: bool = False

def extract_intent(query: str) -> dict:
    cached = get_cached_intent(query)
    if cached is not None:
        logger.info("Found intent in Redis cache. Bypassing LLM execution natively.")
        return cached

    try:
        response = completion(
            model="gemini/gemini-3.1-flash-lite-preview",
            messages=[
                {"role": "system", "content": "Extract filtering criteria from the user query. Set requires_agent=True if it asks for news or external data."},
                {"role": "user", "content": query}
            ],
            response_format=IntentSchema
        )
        content = response.choices[0].message.content
        if isinstance(content, str):
            intent = IntentSchema.model_validate_json(content).model_dump()
        else:
            intent = IntentSchema.model_validate(content).model_dump()
            
        set_cached_intent(query, intent)
        return intent
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return IntentSchema().model_dump()
