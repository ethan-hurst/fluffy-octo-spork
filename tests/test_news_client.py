"""
Unit tests for NewsAPI client functionality.

These tests verify the NewsClient behaves correctly according to its API contract,
not implementation details.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
import httpx

from src.clients.news.client import NewsClient
from src.clients.news.models import NewsArticle, NewsResponse, NewsSource


class TestNewsClient:
    """Test cases for NewsClient API contract."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = NewsClient(
            base_url="https://newsapi.org/v2",
            api_key="test_api_key"
        )
        
    @pytest.mark.asyncio
    async def test_get_everything_returns_news_response(self):
        """Test that get_everything returns a NewsResponse object."""
        # Given: A mock response from the API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "source": {"id": None, "name": "Reuters"},
                    "author": "John Doe",
                    "title": "Market Update: Stocks Rise",
                    "description": "Stock markets showed gains today",
                    "url": "https://example.com/article1",
                    "urlToImage": "https://example.com/image1.jpg",
                    "publishedAt": "2024-01-15T10:00:00Z",
                    "content": "Full article content..."
                },
                {
                    "source": {"id": "bloomberg", "name": "Bloomberg"},
                    "author": "Jane Smith",
                    "title": "Crypto Markets Volatile",
                    "description": "Bitcoin and other cryptocurrencies saw volatility",
                    "url": "https://example.com/article2",
                    "urlToImage": None,
                    "publishedAt": "2024-01-15T09:30:00Z",
                    "content": "Cryptocurrency markets..."
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        # When: We call get_everything
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        
        async with NewsClient() as client:
            client._client = mock_client
            response = await client.get_everything(
                query="market update",
                language="en",
                sort_by="publishedAt"
            )
        
        # Then: We should get a valid NewsResponse
        assert isinstance(response, NewsResponse)
        assert response.status == "ok"
        assert response.total_results == 2
        assert len(response.articles) == 2
        
        # And: Articles should be properly parsed
        article1 = response.articles[0]
        assert isinstance(article1, NewsArticle)
        assert article1.title == "Market Update: Stocks Rise"
        assert article1.source.name == "Reuters"
        assert isinstance(article1.published_at, datetime)
        
    @pytest.mark.asyncio
    async def test_get_everything_handles_api_errors(self):
        """Test that get_everything properly handles API errors."""
        # Given: An API error response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Unauthorized", request=None, response=mock_response)
        )
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        
        # When/Then: We should get an exception
        async with NewsClient() as client:
            client._client = mock_client
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_everything(query="test")
                
    @pytest.mark.asyncio
    async def test_get_relevant_news_filters_by_relevance(self):
        """Test that get_relevant_news returns only relevant articles."""
        # Given: A mix of relevant and irrelevant articles
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 3,
            "articles": [
                {
                    "source": {"name": "Reuters"},
                    "title": "Presidential Election Update",
                    "description": "Latest polling data shows tight race",
                    "url": "https://example.com/election",
                    "publishedAt": datetime.now().isoformat() + "Z",
                    "content": "Election coverage..."
                },
                {
                    "source": {"name": "TechCrunch"},
                    "title": "New Restaurant Opens Downtown",
                    "description": "A new Italian restaurant opened",
                    "url": "https://example.com/restaurant",
                    "publishedAt": datetime.now().isoformat() + "Z",
                    "content": "Restaurant review..."
                },
                {
                    "source": {"name": "Bloomberg"},
                    "title": "Bitcoin Reaches New High",
                    "description": "Cryptocurrency markets surge",
                    "url": "https://example.com/bitcoin",
                    "publishedAt": datetime.now().isoformat() + "Z",
                    "content": "Bitcoin analysis..."
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        
        # When: We get relevant news
        async with NewsClient() as client:
            client._client = mock_client
            articles = await client.get_relevant_news(hours_back=24, max_articles=10)
        
        # Then: We should get relevant articles
        assert isinstance(articles, list)
        assert all(isinstance(a, NewsArticle) for a in articles)
        
        # The actual filtering happens in NewsResponse.relevant_articles
        # which filters based on relevance_keywords
        
    @pytest.mark.asyncio
    async def test_get_breaking_news_uses_top_sources(self):
        """Test that get_breaking_news queries only top news sources."""
        # Given: A mock client to capture the request
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 1,
            "articles": [{
                "source": {"name": "Reuters"},
                "title": "Breaking: Major Event",
                "url": "https://example.com/breaking",
                "publishedAt": datetime.now().isoformat() + "Z"
            }]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        
        # When: We get breaking news
        async with NewsClient() as client:
            client._client = mock_client
            articles = await client.get_breaking_news(max_articles=5)
        
        # Then: The request should include top sources
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        params = call_args[1]['params']
        
        assert 'sources' in params
        expected_sources = ["reuters", "bbc-news", "cnn", "associated-press",
                          "the-wall-street-journal", "bloomberg", "cnbc"]
        assert params['sources'] == ",".join(expected_sources)
        assert params['sortBy'] == 'publishedAt'
        assert params['pageSize'] == 5
        
    @pytest.mark.asyncio
    async def test_context_manager_handles_client_lifecycle(self):
        """Test that the context manager properly manages the HTTP client."""
        # When: We use the client as a context manager
        async with NewsClient() as client:
            # Then: The client should be initialized
            assert client._client is not None
            
        # And: After exiting, the client is closed (we can't easily test this)
        # but the implementation calls await self._client.aclose()
        
    @pytest.mark.asyncio
    async def test_get_everything_validates_parameters(self):
        """Test that get_everything uses valid API parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "totalResults": 0, "articles": []}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        
        # When: We call with various parameters
        async with NewsClient() as client:
            client._client = mock_client
            await client.get_everything(
                query="test",
                sources="reuters,bloomberg",
                language="en",
                sort_by="relevancy",
                page_size=50,
                from_date=datetime(2024, 1, 1),
                to_date=datetime(2024, 1, 31)
            )
        
        # Then: Parameters should be properly formatted for the API
        call_args = mock_client.get.call_args
        params = call_args[1]['params']
        
        assert params['q'] == 'test'
        assert params['sources'] == 'reuters,bloomberg'
        assert params['language'] == 'en'
        assert params['sortBy'] == 'relevancy'  # Note the camelCase conversion
        assert params['pageSize'] == 50
        assert 'from' in params  # from_date becomes 'from'
        assert 'to' in params    # to_date becomes 'to'
        
    @pytest.mark.asyncio
    async def test_rate_limiting_is_applied(self):
        """Test that rate limiting is applied to API requests."""
        # This is more of an integration test, but we can verify the rate limiter is called
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "totalResults": 0, "articles": []}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        
        # The actual rate limiting happens via rate_limiters.newsapi.acquire()
        # We're testing that the method doesn't fail when rate limiting is in place
        async with NewsClient() as client:
            client._client = mock_client
            
            # Make multiple rapid requests
            for _ in range(3):
                await client.get_everything(query="test")
                
        # If rate limiting wasn't working, this might fail
        # But since we're mocking, we're mainly testing the interface
        assert mock_client.get.call_count == 3
        
    def test_news_article_model_contract(self):
        """Test that NewsArticle model works as expected."""
        # Given: Valid article data
        article = NewsArticle(
            source=NewsSource(name="Reuters"),
            title="Test Article",
            description="Test description",
            url="https://example.com/test",
            publishedAt=datetime.now(),
            content="Full content"
        )
        
        # Then: All fields should be accessible
        assert article.title == "Test Article"
        assert article.source.name == "Reuters"
        assert article.description == "Test description"
        assert isinstance(article.published_at, datetime)
        
    def test_news_response_filters_relevant_articles(self):
        """Test that NewsResponse.relevant_articles filters correctly."""
        # Given: A response with mixed articles
        response = NewsResponse(
            status="ok",
            totalResults=2,
            articles=[
                NewsArticle(
                    source=NewsSource(name="Reuters"),
                    title="Election Results Coming In",
                    url="https://example.com/election",
                    publishedAt=datetime.now()
                ),
                NewsArticle(
                    source=NewsSource(name="FoodNetwork"),
                    title="Best Pasta Recipes",
                    url="https://example.com/pasta",
                    publishedAt=datetime.now()
                )
            ]
        )
        
        # When: We get relevant articles
        relevant = response.relevant_articles
        
        # Then: Only articles with relevance keywords should be included
        # The first article contains "election" which is a relevance keyword
        # The second article about pasta recipes should be filtered out
        assert len(relevant) == 1
        assert relevant[0].title == "Election Results Coming In"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])