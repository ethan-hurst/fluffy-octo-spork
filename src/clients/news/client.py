"""
NewsAPI client for fetching current events.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import hashlib
import json

import httpx
from httpx import AsyncClient

from src.config.settings import settings
from src.clients.news.models import NewsArticle, NewsResponse
from src.utils.rate_limiter import rate_limiters

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
        # Simple in-memory cache with TTL
        self._cache: Dict[str, Tuple[NewsResponse, datetime]] = {}
        self._cache_ttl = timedelta(minutes=15)  # Cache for 15 minutes
        
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
        
        # Create cache key from params
        cache_key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        
        # Check cache first
        if cache_key in self._cache:
            cached_response, cache_time = self._cache[cache_key]
            if datetime.now() - cache_time < self._cache_ttl:
                logger.debug(f"Returning cached news response for key {cache_key}")
                return cached_response
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
            
        try:
            # Apply rate limiting
            await rate_limiters.newsapi.acquire()
            
            response = await self._client.get("/everything", params=params)
            response.raise_for_status()
            data = response.json()
            news_response = NewsResponse(**data)
            
            # Cache successful response
            self._cache[cache_key] = (news_response, datetime.now())
            
            return news_response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"NewsAPI rate limit exceeded. Consider upgrading API plan or reducing request frequency.")
                # Return empty response instead of failing
                return NewsResponse(
                    status="error",
                    total_results=0,
                    articles=[]
                )
            else:
                logger.error(f"HTTP status error getting news: {e}")
                raise
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
        
        # Reduced queries to avoid rate limiting
        queries = [
            "election OR vote OR poll OR candidate OR president",
            "cryptocurrency OR bitcoin OR crypto OR economy", 
            "AI OR technology OR policy OR regulation"
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
                
                # Longer delay to respect rate limits
                await asyncio.sleep(1.0)
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit hit for query '{query}'. Skipping remaining queries.")
                    break  # Stop trying more queries
                else:
                    logger.error(f"HTTP error fetching news for query '{query}': {e}")
                    continue
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
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit hit fetching breaking news. Returning empty list.")
            else:
                logger.error(f"HTTP error fetching breaking news: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching breaking news: {e}")
            return []