"""Worker background tasks mapping agent workflows natively."""

import logging
import os
from typing import Any, Dict

from celery import Celery
from litellm import completion

logger = logging.getLogger("worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("agent_workflows", broker=REDIS_URL, backend=REDIS_URL)


def search_recent_news(company_domain: str | None) -> str:
    """Invokes simulated external intelligence retrieval."""
    if not company_domain:
        return "No recent news available."
    return f"Recent news for {company_domain}: Announced $10M Series A funding last month."


# Celery's task decorator lacks proper type hints
@celery_app.task(bind=True, max_retries=3, name="tasks.agent_workflows.synthesize_agent_response")  # type: ignore[untyped-decorator]
def synthesize_agent_response(self: Any, query: str, candidates: list[Dict[str, Any]]) -> Dict[str, Any]:
    """Coordinates nested search synthesis natively evaluating models."""

    if not candidates:
        return {"summary": "No relevant companies found to perform external search on."}

    context = ""
    for c in candidates:
        domain = c.get("website")
        news = search_recent_news(domain)
        context += f"Company: {c.get('name')} | Industry: {c.get('industry')} | News: {news}\n\n"

    prompt = (
        f"Context:\n{context}\n\n"
        f"Query: {query}\n\n"
        "Please provide a helpful natural language summary "
        "answering the user's query using only the provided context."
    )

    try:
        response = completion(
            model="gemini/gemini-3.1-flash-lite-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful B2B company research assistant.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        summary = response.choices[0].message.content or "No summary generated."
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Agent synthesis failed: {e}")
        return {"summary": "Error synthesizing agent response."}
