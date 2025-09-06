from fastapi import APIRouter, HTTPException
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/tavily", tags=["tavily"])


class TavilyService:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, max_results: int = 5):
        """Search using Tavily API"""
        try:
            response = self.client.search(
                query=query, search_depth="basic", max_results=max_results
            )
            return response
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Tavily search failed: {str(e)}"
            )

    def get_search_context(self, query: str, max_results: int = 3):
        """Get search context for chatbot responses"""
        try:
            response = self.client.get_search_context(
                query=query,
                search_depth="basic",
                max_tokens=1000,
                max_results=max_results,
            )
            return response
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Tavily context search failed: {str(e)}"
            )


tavily_service = TavilyService()


@router.post("/search")
def search_tavily(query: str, max_results: int = 5):
    """Search using Tavily API"""
    return tavily_service.search(query, max_results)


@router.post("/context")
def get_search_context(query: str, max_results: int = 3):
    """Get search context for chatbot"""
    return tavily_service.get_search_context(query, max_results)
