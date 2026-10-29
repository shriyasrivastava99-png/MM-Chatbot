import logging
from typing import List, Optional
from backend.core.config import get_settings
from backend.schemas.search import SearchRequest, SearchResponse, SearchResultItem

logger = logging.getLogger("uvicorn.error")
settings = get_settings()


class SearchService:
    """
    Provides real-time web search integration using DuckDuckGo
    (or Tavily if configured) with fallback handling.
    """

    def __init__(self):
        self.provider = settings.WEB_SEARCH_PROVIDER.lower()
        self.tavily_key = settings.TAVILY_API_KEY

    def search(self, query: str, max_results: int = 5) -> SearchResponse:
        """
        Executes a web search query and returns structured results with a summary.
        """
        query = query.strip()
        if not query:
            return SearchResponse(query="", summary="No search query provided.", results=[])

        results: List[SearchResultItem] = []

        # 1. Try DuckDuckGo
        if self.provider == "duckduckgo" or not self.tavily_key:
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query, max_results=max_results))
                    for item in raw_results:
                        results.append(
                            SearchResultItem(
                                title=item.get("title", "Untitled"),
                                url=item.get("href", item.get("link", "")),
                                snippet=item.get("body", item.get("snippet", ""))
                            )
                        )
            except Exception as e:
                logger.warning(f"DuckDuckGo search error: {e}")

        # 2. Try Tavily if configured and DDG had no results
        if not results and self.tavily_key:
            try:
                import httpx
                resp = httpx.post(
                    "https://api.tavily.com/search",
                    json={"api_key": self.tavily_key, "query": query, "max_results": max_results},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for r in data.get("results", []):
                        results.append(
                            SearchResultItem(
                                title=r.get("title", "Untitled"),
                                url=r.get("url", ""),
                                snippet=r.get("content", "")
                            )
                        )
            except Exception as e:
                logger.warning(f"Tavily search error: {e}")

        # Build summary
        if results:
            summary = f"Found {len(results)} search results for '{query}'."
        else:
            summary = f"No live web search results found for '{query}'."

        return SearchResponse(
            query=query,
            summary=summary,
            results=results
        )


search_service = SearchService()

