"""
Unit tests for NewsAPI client functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp

from src.clients.news.client import NewsClient
from src.clients.news.models import NewsArticle


class TestNewsClient:
    """Test cases for NewsClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = NewsClient()
        
        # Create test news data
        now = datetime.now()
        self.test_news_data = {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "title": "Trump Leads in Latest Polling Data",
                    "description": "Former president shows strong support in key battleground states",
                    "url": "https://example.com/trump-polling",
                    "publishedAt": (now - timedelta(hours=2)).isoformat() + "Z",
                    "source": {
                        "name": "Reuters"
                    },
                    "content": "Full article content about Trump polling data..."
                },
                {
                    "title": "Bitcoin ETF Decision Expected Soon",
                    "description": "SEC chairman hints at upcoming decision on cryptocurrency ETF applications",
                    "url": "https://example.com/btc-etf",
                    "publishedAt": (now - timedelta(hours=1)).isoformat() + "Z",
                    "source": {
                        "name": "Bloomberg"
                    },
                    "content": "Article content about Bitcoin ETF decision..."
                }
            ]
        }
        
        self.test_empty_response = {
            "status": "ok",
            "totalResults": 0,
            "articles": []
        }
        
        self.test_error_response = {
            "status": "error",
            "code": "apiKeyInvalid",
            "message": "Your API key is invalid or incorrect."
        }
        
    @pytest.mark.asyncio
    async def test_search_news_success(self):
        """Test successful news search."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_news_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            articles = await self.client.search_news("Trump election")
            
            assert len(articles) == 2
            assert isinstance(articles[0], NewsArticle)
            assert articles[0].title == "Trump Leads in Latest Polling Data"
            assert articles[0].source == "Reuters"
            assert articles[0].url == "https://example.com/trump-polling"
            assert isinstance(articles[0].published_at, datetime)
            
    @pytest.mark.asyncio
    async def test_search_news_with_filters(self):
        """Test news search with additional filters."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_news_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            articles = await self.client.search_news(
                query="Bitcoin",
                sources=["bloomberg", "reuters"],
                language="en",
                sort_by="publishedAt",
                from_date=datetime.now() - timedelta(days=1),
                to_date=datetime.now(),
                page_size=20
            )
            
            # Verify the request was made with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            url = str(call_args[0][0]) if call_args[0] else str(call_args[1].get('url', ''))
            
            assert "q=Bitcoin" in url
            assert "sources=" in url
            assert "language=en" in url
            assert "sortBy=publishedAt" in url
            assert "pageSize=20" in url
            
            assert len(articles) == 2
            
    @pytest.mark.asyncio
    async def test_search_news_empty_results(self):
        """Test news search with no results."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_empty_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            articles = await self.client.search_news("very specific query with no results")
            
            assert articles == []
            
    @pytest.mark.asyncio
    async def test_search_news_api_error(self):
        """Test news search with API error response."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 400
            mock_response.json = AsyncMock(return_value=self.test_error_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            articles = await self.client.search_news("test query")
            
            assert articles == []  # Should return empty list on error
            
    @pytest.mark.asyncio
    async def test_search_news_network_error(self):
        """Test news search with network error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Network connection failed")
            
            articles = await self.client.search_news("test query")
            
            assert articles == []  # Should return empty list on network error
            
    @pytest.mark.asyncio
    async def test_search_news_timeout(self):
        """Test news search with timeout."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError("Request timed out")
            
            articles = await self.client.search_news("test query")
            
            assert articles == []  # Should return empty list on timeout
            
    @pytest.mark.asyncio
    async def test_get_top_headlines_success(self):
        """Test successful top headlines retrieval."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_news_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            articles = await self.client.get_top_headlines(category="business")
            
            assert len(articles) == 2
            assert isinstance(articles[0], NewsArticle)
            
            # Verify correct endpoint was called
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            url = str(call_args[0][0]) if call_args[0] else str(call_args[1].get('url', ''))
            assert "top-headlines" in url
            assert "category=business" in url
            
    @pytest.mark.asyncio
    async def test_get_top_headlines_with_country(self):
        """Test top headlines with country filter."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_news_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            articles = await self.client.get_top_headlines(
                country="us",
                category="politics",
                page_size=50
            )
            
            # Verify parameters
            call_args = mock_get.call_args
            url = str(call_args[0][0]) if call_args[0] else str(call_args[1].get('url', ''))
            assert "country=us" in url
            assert "category=politics" in url
            assert "pageSize=50" in url
            
            assert len(articles) == 2
            
    def test_build_search_url_basic(self):
        """Test search URL building with basic parameters."""
        url = self.client._build_search_url("test query")
        
        assert self.client.base_url in url
        assert "everything" in url
        assert "q=test%20query" in url or "q=test+query" in url
        assert f"apiKey={self.client.api_key}" in url
        
    def test_build_search_url_with_filters(self):
        """Test search URL building with all filters."""
        from_date = datetime(2024, 1, 1)
        to_date = datetime(2024, 1, 31)
        
        url = self.client._build_search_url(
            query="Bitcoin",
            sources=["reuters", "bloomberg"],
            language="en",
            sort_by="publishedAt",
            from_date=from_date,
            to_date=to_date,
            page_size=50
        )
        
        assert "q=Bitcoin" in url
        assert "sources=reuters,bloomberg" in url or "sources=reuters%2Cbloomberg" in url
        assert "language=en" in url
        assert "sortBy=publishedAt" in url
        assert "from=2024-01-01" in url
        assert "to=2024-01-31" in url
        assert "pageSize=50" in url
        
    def test_build_headlines_url_basic(self):
        """Test headlines URL building with basic parameters."""
        url = self.client._build_headlines_url()
        
        assert self.client.base_url in url
        assert "top-headlines" in url
        assert f"apiKey={self.client.api_key}" in url
        
    def test_build_headlines_url_with_filters(self):
        """Test headlines URL building with filters."""
        url = self.client._build_headlines_url(
            country="us",
            category="business",
            sources=["reuters"],
            page_size=25
        )
        
        assert "country=us" in url
        assert "category=business" in url
        assert "sources=reuters" in url
        assert "pageSize=25" in url
        
    def test_parse_article_valid(self):
        """Test parsing valid article data."""
        article_data = self.test_news_data["articles"][0]
        article = self.client._parse_article(article_data)
        
        assert isinstance(article, NewsArticle)
        assert article.title == "Trump Leads in Latest Polling Data"
        assert article.description == "Former president shows strong support in key battleground states"
        assert article.url == "https://example.com/trump-polling"
        assert article.source == "Reuters"
        assert isinstance(article.published_at, datetime)
        
    def test_parse_article_missing_fields(self):
        """Test parsing article with missing optional fields."""
        minimal_article = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "publishedAt": "2024-01-01T12:00:00Z",
            "source": {"name": "Test Source"}
        }
        
        article = self.client._parse_article(minimal_article)
        
        assert isinstance(article, NewsArticle)
        assert article.title == "Test Article"
        assert article.description is None  # Missing field should be None
        assert article.url == "https://example.com/test"
        assert article.source == "Test Source"
        
    def test_parse_article_invalid_date(self):
        """Test parsing article with invalid date format."""
        invalid_article = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "publishedAt": "invalid-date-format",
            "source": {"name": "Test Source"}
        }
        
        article = self.client._parse_article(invalid_article)
        assert article is None  # Should return None for invalid date
        
    def test_parse_article_missing_required_fields(self):
        """Test parsing article missing required fields."""
        incomplete_article = {
            "title": "Test Article",
            # Missing url, publishedAt, source
        }
        
        article = self.client._parse_article(incomplete_article)
        assert article is None  # Should return None for missing required fields
        
    def test_parse_article_invalid_source_format(self):
        """Test parsing article with invalid source format."""
        invalid_source_article = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "publishedAt": "2024-01-01T12:00:00Z",
            "source": "Invalid Source Format"  # Should be dict with 'name' key
        }
        
        article = self.client._parse_article(invalid_source_article)
        assert article is None  # Should return None for invalid source format
        
    def test_parse_datetime_valid_formats(self):
        """Test datetime parsing with valid formats."""
        # Test ISO format with Z
        dt1 = self.client._parse_datetime("2024-01-01T12:00:00Z")
        assert isinstance(dt1, datetime)
        assert dt1.year == 2024
        assert dt1.month == 1
        assert dt1.day == 1
        
        # Test ISO format with timezone offset
        dt2 = self.client._parse_datetime("2024-01-01T12:00:00+00:00")
        assert isinstance(dt2, datetime)
        
        # Test ISO format without timezone
        dt3 = self.client._parse_datetime("2024-01-01T12:00:00")
        assert isinstance(dt3, datetime)
        
    def test_parse_datetime_invalid_format(self):
        """Test datetime parsing with invalid format."""
        invalid_dt = self.client._parse_datetime("invalid-date-format")
        assert invalid_dt is None
        
    def test_parse_datetime_none_input(self):
        """Test datetime parsing with None input."""
        none_dt = self.client._parse_datetime(None)
        assert none_dt is None
        
    def test_format_date_for_api(self):
        """Test date formatting for API requests."""
        test_date = datetime(2024, 1, 15, 10, 30, 45)
        formatted = self.client._format_date_for_api(test_date)
        
        assert formatted == "2024-01-15"
        
    def test_format_date_for_api_none(self):
        """Test date formatting with None input."""
        formatted = self.client._format_date_for_api(None)
        assert formatted is None
        
    def test_validate_search_parameters_valid(self):
        """Test search parameter validation with valid inputs."""
        # Should not raise any exceptions
        self.client._validate_search_parameters(
            query="test",
            sources=["reuters"],
            language="en",
            sort_by="publishedAt",
            page_size=50
        )
        
    def test_validate_search_parameters_invalid_language(self):
        """Test search parameter validation with invalid language."""
        with pytest.raises(ValueError, match="language"):
            self.client._validate_search_parameters(
                query="test",
                language="invalid-lang"
            )
            
    def test_validate_search_parameters_invalid_sort_by(self):
        """Test search parameter validation with invalid sort_by."""
        with pytest.raises(ValueError, match="sort_by"):
            self.client._validate_search_parameters(
                query="test",
                sort_by="invalid-sort"
            )
            
    def test_validate_search_parameters_invalid_page_size(self):
        """Test search parameter validation with invalid page size."""
        with pytest.raises(ValueError, match="page_size"):
            self.client._validate_search_parameters(
                query="test",
                page_size=150  # Too large
            )
            
        with pytest.raises(ValueError, match="page_size"):
            self.client._validate_search_parameters(
                query="test",
                page_size=0  # Too small
            )
            
    def test_validate_headlines_parameters_valid(self):
        """Test headlines parameter validation with valid inputs."""
        # Should not raise any exceptions
        self.client._validate_headlines_parameters(
            country="us",
            category="business",
            sources=["reuters"],
            page_size=50
        )
        
    def test_validate_headlines_parameters_invalid_country(self):
        """Test headlines parameter validation with invalid country."""
        with pytest.raises(ValueError, match="country"):
            self.client._validate_headlines_parameters(
                country="invalid-country"
            )
            
    def test_validate_headlines_parameters_invalid_category(self):
        """Test headlines parameter validation with invalid category."""
        with pytest.raises(ValueError, match="category"):
            self.client._validate_headlines_parameters(
                category="invalid-category"
            )
            
    def test_news_article_model_creation(self):
        """Test NewsArticle model creation and validation."""
        now = datetime.now()
        article = NewsArticle(
            title="Test Article Title",
            description="Test article description",
            url="https://example.com/test-article",
            published_at=now,
            source="Test Source"
        )
        
        assert article.title == "Test Article Title"
        assert article.description == "Test article description"
        assert article.url == "https://example.com/test-article"
        assert article.published_at == now
        assert article.source == "Test Source"
        
    def test_news_article_model_optional_fields(self):
        """Test NewsArticle model with optional fields."""
        now = datetime.now()
        article = NewsArticle(
            title="Test Article",
            url="https://example.com/test",
            published_at=now,
            source="Test Source",
            description=None  # Optional field
        )
        
        assert article.title == "Test Article"
        assert article.description is None
        assert article.url == "https://example.com/test"
        assert article.source == "Test Source"
        
    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test proper session management."""
        # Test that session is created when needed
        assert self.client.session is None
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_empty_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            await self.client.search_news("test")
            
            # Session should be created
            assert self.client.session is not None
            
        # Test session cleanup
        await self.client.close()
        
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_empty_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Make multiple requests rapidly
            tasks = [self.client.search_news(f"query {i}") for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed (rate limiter should handle timing)
            assert all(isinstance(result, list) for result in results)
            
    def test_error_handling_consistency(self):
        """Test consistent error handling across methods."""
        # Test invalid article data handling
        invalid_articles = [
            {},  # Empty dict
            {"title": "Test"},  # Missing required fields
            {"title": "Test", "url": "invalid-url", "source": "invalid"},  # Invalid formats
        ]
        
        for invalid_article in invalid_articles:
            result = self.client._parse_article(invalid_article)
            assert result is None  # Should consistently return None for invalid data


if __name__ == "__main__":
    import asyncio
    pytest.main([__file__])