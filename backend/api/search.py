from fastapi import APIRouter
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.search_service import search_service

router = APIRouter()


@router.post("", response_model=SearchResponse)
def execute_search(req: SearchRequest):
    """
    Executes live web search via DuckDuckGo (or Tavily) and returns structured results.
    """
    return search_service.search(query=req.query, max_results=req.max_results)

