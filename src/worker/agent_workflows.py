"""Worker background tasks mapping agent workflows natively."""

import json
import logging
import os
from typing import Any, Dict

import redis
from celery import Celery, Task
from litellm import completion

logger = logging.getLogger("worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("agent_workflows", broker=REDIS_URL, backend=REDIS_URL)


def search_recent_news(company_domain: str | None) -> str:
    """Invokes simulated external intelligence retrieval."""
    if not company_domain:
        return "No recent news available."
    return f"Recent news for {company_domain}: Announced $10M Series A funding last month."


class DLQTask(Task):  # type: ignore[misc]
    """Custom celery task that triggers native Redis DLQ on failure."""

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple[Any, ...], kwargs: dict[str, Any], einfo: Any
    ) -> None:
        """Route failed parameters to the native Redis DLQ namespace."""
        try:
            r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            payload = {
                "task_id": task_id,
                "task_name": self.name,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
                "traceback": str(einfo.traceback) if einfo else None,
            }
            r.lpush("celery:dlq", json.dumps(payload))
            logger.error(f"Task {task_id} failed permanently. Routed inputs to celery:dlq.")
        except Exception as dlq_err:
            logger.error(f"Failed to route task {task_id} to DLQ: {dlq_err}")

        super().on_failure(exc, task_id, args, kwargs, einfo)


# Celery's task decorator lacks proper type hints
@celery_app.task(bind=True, base=DLQTask, max_retries=3, name="tasks.agent_workflows.synthesize_agent_response")  # type: ignore[untyped-decorator]
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
        raise self.retry(exc=e, countdown=1)
