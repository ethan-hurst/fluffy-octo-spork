"""
NewsAPI client for fetching current events.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from httpx import AsyncClient

from src.config.settings import settings
from src.clients.news.models import NewsArticle, NewsResponse

logger = logging.getLogger(__name__)


class NewsClient:
    """
    Client for interacting with NewsAPI.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize NewsAPI client.
        
        Args:
            base_url: API base URL (defaults to settings)
            api_key: API key (defaults to settings)
        """
        self.base_url = base_url or settings.news_api_url
        self.api_key = api_key or settings.news_api_key
        self._client: Optional[AsyncClient] = None
        
    async def __aenter__(self) -> "NewsClient":
        """Async context manager entry."""
        self._client = AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=30.0
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            
    def _get_headers(self) -> dict:
        """
        Get request headers.
        
        Returns:
            dict: Request headers
        """
        return {
            "Accept": "application/json",
            "X-API-Key": self.api_key,
        }
        
    async def get_everything(
        self,
        query: Optional[str] = None,
        sources: Optional[str] = None,
        domains: Optional[str] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 100,
        page: int = 1,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> NewsResponse:
        """
        Get news articles from NewsAPI everything endpoint.
        
        Args:
            query: Keywords to search for
            sources: Comma-separated source IDs
            domains: Comma-separated domain names
            language: Language code (default: en)
            sort_by: Sort order (publishedAt, relevancy, popularity)
            page_size: Number of results per page
            page: Page number
            from_date: Articles published after this date
            to_date: Articles published before this date
            
        Returns:
            NewsResponse: News articles response
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
            
        params = {
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
            "page": page,
        }
        
        if query:
            params["q"] = query
        if sources:
            params["sources"] = sources
        if domains:
            params["domains"] = domains
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
            
        try:
            response = await self._client.get("/everything", params=params)
            response.raise_for_status()
            data = response.json()
            return NewsResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting news: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            raise
            
    async def get_relevant_news(
        self,
        hours_back: int = 24,
        max_articles: int = 100
    ) -> List[NewsArticle]:
        """
        Get recent news articles relevant to prediction markets.
        
        Args:
            hours_back: How many hours back to search
            max_articles: Maximum number of articles to return
            
        Returns:
            List[NewsArticle]: Relevant news articles
        """
        from_date = datetime.now() - timedelta(hours=hours_back)
        
        # Search for prediction market relevant topics
        queries = [
            "election OR vote OR poll OR candidate OR president",
            "cryptocurrency OR bitcoin OR crypto OR blockchain",
            "stock market OR economy OR recession OR inflation",
            "climate OR weather OR hurricane OR earthquake",
            "sports championship OR tournament OR olympics",
            "AI OR artificial intelligence OR technology",
            "policy OR regulation OR law OR legislation"
        ]
        
        all_articles = []
        
        for query in queries:
            if len(all_articles) >= max_articles:
                break
                
            try:
                response = await self.get_everything(
                    query=query,
                    from_date=from_date,
                    sort_by="publishedAt",
                    page_size=min(50, max_articles - len(all_articles))
                )
                
                # Filter for relevant articles
                relevant_articles = response.relevant_articles
                all_articles.extend(relevant_articles)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching news for query '{query}': {e}")
                continue
                
        # Remove duplicates by URL and sort by publication date
        seen_urls = set()
        unique_articles = []
        
        for article in all_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
                
        # Sort by publication date (newest first)
        unique_articles.sort(key=lambda x: x.published_at, reverse=True)
        
        return unique_articles[:max_articles]
        
    async def get_breaking_news(self, max_articles: int = 20) -> List[NewsArticle]:
        """
        Get breaking news from top sources.
        
        Args:
            max_articles: Maximum number of articles to return
            
        Returns:
            List[NewsArticle]: Breaking news articles
        """
        # Top news sources for breaking news
        top_sources = [
            "reuters", "bbc-news", "cnn", "associated-press",
            "the-wall-street-journal", "bloomberg", "cnbc"
        ]
        
        try:
            response = await self.get_everything(
                sources=",".join(top_sources),
                sort_by="publishedAt",
                page_size=max_articles,
                from_date=datetime.now() - timedelta(hours=6)
            )
            
            return response.relevant_articles[:max_articles]
            
        except Exception as e:
            logger.error(f"Error fetching breaking news: {e}")
            return []