import random

from locust import HttpUser, between, task


class SearchUser(HttpUser):
    """Load testing user for search API."""

    wait_time = between(1, 3)  # type: ignore[no-untyped-call]

    @task(6)
    def standard_search(self) -> None:
        """Standard Exact Filtering (60%)."""
        industry = random.choice(["Technology", "Healthcare", "Finance"])
        self.client.post("/api/v2/search", json={"industry": industry, "size": 10, "page": 1})

    @task(3)
    def semantic_search(self) -> None:
        """Semantic Concept Search (30%)."""
        query = random.choice(
            [
                "Provide AI solutions",
                "Cloud computing providers",
                "Medical device manufacturers",
            ]
        )
        self.client.post("/api/v2/search/intelligent", json={"query": query})

    @task(1)
    def agentic_search(self) -> None:
        """Complex Agentic Orchestration Search (10%)."""
        query = random.choice(
            [
                "Find companies recently acquiring startups in AI space and summarize their strategies",
                "Who is the CEO of OpenAI and what are their latest products?",
            ]
        )
        self.client.post("/api/v2/search/intelligent", json={"query": query})
