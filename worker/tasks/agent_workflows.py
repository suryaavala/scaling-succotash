import os
import logging
from celery import Celery
from litellm import completion

logger = logging.getLogger("worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "agent_workflows",
    broker=REDIS_URL,
    backend=REDIS_URL
)

def search_recent_news(company_domain: str | None) -> str:
    if not company_domain:
        return "No recent news available."
    return f"Recent news for {company_domain}: Announced $10M Series A funding last month."

@celery_app.task
def synthesize_agent_response(query: str, candidates: list[dict]) -> str:
    if not candidates:
        return "No relevant companies found to perform external search on."
        
    context = ""
    for c in candidates[:5]:
        domain = c.get("domain")
        news = search_recent_news(domain)
        context += f"Company: {c.get('name')}\nDomain: {domain}\nNews: {news}\n\n"
        
    prompt = f"User query: {query}\n\nSearch Results & Context:\n{context}\n\nPlease provide a helpful natural language summary answering the user's query using only the provided context."
    
    try:
        response = completion(
            model="gemini/gemini-3.1-flash-lite-preview",
            messages=[
                {"role": "system", "content": "You are a helpful B2B company research assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content or "No summary generated."
    except Exception as e:
        logger.error(f"Agent synthesis failed: {e}")
        return "Error synthesizing agent response."
