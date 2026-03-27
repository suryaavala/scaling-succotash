import httpx
import logging
from src.api.core.config import get_settings

logger = logging.getLogger(__name__)

async def fetch_recent_company_news(company_name: str, domain: str, timeframe: str = "last 2 months") -> str:
    """
    Fetches structured, LLM-optimized news context from an external search API.
    """
    settings = get_settings()
    query = f"{company_name} ({domain}) recent news funding acquisitions {timeframe}"
    
    try:
        # Example using a generic HTTP client to an LLM-friendly Search API
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.search_api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": False,
                    "include_raw_content": False,
                    "max_results": 3
                }
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            
            if not results:
                return "No recent significant news found."
                
            # Compile the snippets into a dense context block for the LLM
            context = "\n\n".join([f"Source: {r['url']}\nSnippet: {r['content']}" for r in results])
            return context
            
    except httpx.HTTPError as e:
        logger.error(f"External search failed for {company_name}: {e}")
        return "External search temporarily unavailable."
