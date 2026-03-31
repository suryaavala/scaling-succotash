"""Worker background tasks mapping agent workflows natively."""

import asyncio
import json
import logging
import os
from typing import Any, Dict

import redis
from celery import Celery, Task
from litellm import completion

from src.worker.tools.search import fetch_recent_company_news

logger = logging.getLogger("worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("agent_workflows", broker=REDIS_URL, backend=REDIS_URL)


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

    # Fetch news concurrently for top 5 candidates
    async def fetch_all_news(query: str) -> list[str]:
        tasks = []
        for c in candidates[:5]:
            domain = c.get("website") or ""
            company_name = c.get("name") or "Unknown"
            tasks.append(fetch_recent_company_news(company_name, domain, query))
        return await asyncio.gather(*tasks)  # type: ignore[no-any-return]

    try:
        news_results = asyncio.run(fetch_all_news(query))
    except Exception as e:
        logger.error(f"External search failed: {e}")
        news_results = ["External search temporarily unavailable."] * len(candidates[:5])

    context = ""
    for c, news in zip(candidates[:5], news_results):
        context += f"Company: {c.get('name')} | Industry: {c.get('industry')} | News: {news}\n\n"

    prompt = (
        f"Context:\n{context}\n\n"
        f"Query: {query}\n\n"
        "You are an Information Retrieval expert. Using ONLY the provided context below, summarize "
        "recent announcements for these companies. Do not hallucinate. If the context "
        "does not contain funding news, state that explicitly. Provide citations using URLs."
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
        return {"summary": summary, "raw_markdown": context}
    except Exception as e:
        logger.error(f"Agent synthesis failed: {e}")
        raise self.retry(exc=e, countdown=1)
