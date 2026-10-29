from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str


class SearchRequest(BaseModel):
    query: str = Field(..., description="Web search query string")
    max_results: int = Field(5, ge=1, le=10, description="Maximum number of search results to retrieve")


class SearchResponse(BaseModel):
    query: str
    summary: str
    results: List[SearchResultItem] = []
