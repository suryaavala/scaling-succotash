import logging
from litellm import completion
from app.models.schemas import Company
from typing import List

logger = logging.getLogger("agent")

def search_recent_news(company_domain: str | None) -> str:
    """Mock external tool to search recent news for a company."""
    if not company_domain:
        return "No recent news available."
    return f"Recent news for {company_domain}: Announced $10M Series A funding last month."

def synthesize_agent_response(query: str, candidates: List[Company]) -> str:
    """Uses LLM to synthesize final output combining OpenSearch hits and mock news."""
    if not candidates:
        return "No relevant companies found to perform external search on."
        
    context = ""
    for c in candidates[:5]:
        news = search_recent_news(c.domain)
        context += f"Company: {c.name}\nDomain: {c.domain}\nNews: {news}\n\n"
        
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
