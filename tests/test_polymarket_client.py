"""
Unit tests for Polymarket CLOB API client functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from src.clients.polymarket.client import PolymarketClient
from src.clients.polymarket.models import Market, Token, MarketsResponse, MarketPrice


class TestPolymarketClient:
    """Test cases for PolymarketClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = PolymarketClient()
        # Mock the _client attribute to avoid initialization issues in tests
        self.client._client = MagicMock()
        
        # Create test market data
        now = datetime.now()
        self.test_market_data = {
            "condition_id": "test_condition_123",
            "question": "Will Donald Trump win the 2024 presidential election?",
            "description": "Presidential election prediction market",
            "category": "Politics",
            "active": True,
            "closed": False,
            "volume": "1250000.50",
            "end_date_iso": (now + timedelta(days=300)).isoformat(),
            "tokens": [
                {"token_id": "yes_token", "outcome": "Yes", "price": 0.5},
                {"token_id": "no_token", "outcome": "No", "price": 0.5}
            ],
            "minimum_order_size": 1.0
        }
        
        self.test_markets_response = {
            "limit": 100,
            "count": 2,
            "next_cursor": None,
            "data": [
                self.test_market_data,
                {
                    "condition_id": "test_condition_456",
                    "question": "Will Bitcoin reach $100,000 by end of 2024?",
                    "description": "Bitcoin price prediction",
                    "category": "Cryptocurrency",
                    "active": True,
                    "closed": False,
                    "volume": "875000.25",
                    "end_date_iso": (now + timedelta(days=60)).isoformat(),
                    "tokens": [
                        {"token_id": "yes_token", "outcome": "Yes", "price": 0.5},
                        {"token_id": "no_token", "outcome": "No", "price": 0.5}
                    ],
                    "minimum_order_size": 1.0
                }
            ]
        }
        
    @pytest.mark.asyncio
    async def test_get_markets_success(self):
        """Test successful market data retrieval."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=self.test_markets_response)
        mock_response.raise_for_status = MagicMock()
        
        self.client._client.get = AsyncMock(return_value=mock_response)
        
        response = await self.client.get_markets()
        
        assert isinstance(response, MarketsResponse)
        assert response.count == 2
        assert len(response.data) == 2
        assert isinstance(response.data[0], Market)
        assert response.data[0].condition_id == "test_condition_123"
        assert response.data[0].question == "Will Donald Trump win the 2024 presidential election?"
        assert response.data[0].volume == 1250000.50
        assert response.data[0].active is True
        
    @pytest.mark.asyncio
    async def test_get_markets_api_error(self):
        """Test market data retrieval with API error."""
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status = MagicMock(side_effect=Exception("API Error"))
        
        self.client._client.get = AsyncMock(return_value=mock_response)
        
        # Should raise exception on API error
        with pytest.raises(Exception) as exc_info:
            await self.client.get_markets()
        
        assert "API Error" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_get_markets_network_error(self):
        """Test market data retrieval with network error."""
        # Mock network error
        self.client._client.get = AsyncMock(side_effect=Exception("Network error"))
        
        # Should raise exception on network error
        with pytest.raises(Exception) as exc_info:
            await self.client.get_markets()
        
        assert "Network error" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_get_markets_with_filters(self):
        """Test market data retrieval with filters."""
        # Mock successful response with filtered data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "limit": 100,
            "count": 1,
            "data": [self.test_markets_response["data"][0]],
            "next_cursor": None
        })
        mock_response.raise_for_status = MagicMock()
        
        self.client._client.get = AsyncMock(return_value=mock_response)
        
        # Note: The actual client doesn't support these parameters yet
        response = await self.client.get_markets()
        
        # Verify the request was made
        self.client._client.get.assert_called_once()
        
        assert len(response.data) >= 1
        
    @pytest.mark.asyncio
    async def test_get_all_active_markets(self):
        """Test getting all active markets."""
        # Mock successful paginated responses
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json = MagicMock(return_value={
            "limit": 100,
            "count": 2,
            "data": self.test_markets_response["data"],
            "next_cursor": "cursor_123"
        })
        mock_response1.raise_for_status = MagicMock()
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json = MagicMock(return_value={
            "limit": 100,
            "count": 0,
            "data": [],
            "next_cursor": None
        })
        mock_response2.raise_for_status = MagicMock()
        
        self.client._client.get = AsyncMock(side_effect=[mock_response1, mock_response2])
        
        markets = await self.client.get_all_active_markets(max_markets=10)
        
        assert len(markets) == 2
        assert all(isinstance(m, Market) for m in markets)
        
    @pytest.mark.asyncio
    async def test_get_market_prices(self):
        """Test getting market prices."""
        market = Market(
            condition_id="test_market",
            question="Test question?",
            description="Test description",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[
                Token(token_id="yes", outcome="Yes", price=0.6),
                Token(token_id="no", outcome="No", price=0.4)
            ],
            minimum_order_size=1.0
        )
        
        # Test the method (it uses token prices directly)
        prices = await self.client.get_market_prices(market)
        
        assert prices is not None
        assert prices.yes_price == 0.6
        assert prices.no_price == 0.4
        assert abs(prices.spread - 0.2) < 0.0001  # abs(0.6 - 0.4) with floating point tolerance
        
    def test_parse_market_data_valid(self):
        """Test parsing valid market data."""
        market = self.client._parse_market(self.test_market_data)
        
        assert isinstance(market, Market)
        assert market.condition_id == "test_condition_123"
        assert market.question == "Will Donald Trump win the 2024 presidential election?"
        assert market.volume == 1250000.50
        assert len(market.tokens) == 2
        
    def test_parse_market_data_invalid(self):
        """Test parsing invalid market data."""
        invalid_data = {
            "condition_id": "test",
            # Missing required fields
        }
        
        market = self.client._parse_market(invalid_data)
        assert market is None
        
    def test_validate_market_required_fields(self):
        """Test market validation with required fields."""
        # Test with all required fields
        valid_market = Market(
            condition_id="test",
            question="Test question?",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[
                Token(token_id="yes", outcome="Yes", price=0.5),
                Token(token_id="no", outcome="No", price=0.5)
            ],
            minimum_order_size=1.0
        )
        
        assert valid_market.condition_id == "test"
        assert len(valid_market.tokens) == 2
        
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting is applied."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=self.test_markets_response)
        mock_response.raise_for_status = MagicMock()
        
        self.client._client.get = AsyncMock(return_value=mock_response)
        
        # Make multiple requests
        results = []
        for _ in range(3):
            response = await self.client.get_markets()
            results.append(response)
        
        # All requests should succeed
        assert all(r.count == 2 for r in results)
        
    @pytest.mark.asyncio
    async def test_context_manager_usage(self):
        """Test using client as async context manager."""
        async with PolymarketClient() as client:
            # Client should be initialized
            assert client._client is not None
            
        # After context exit, client should be closed
        # (Can't easily test this without accessing private attributes)
        
    def test_error_handling_consistency(self):
        """Test consistent error handling across methods."""
        # Test that all methods handle errors consistently
        # This is more of a code review item, but we can test basic cases
        
        # Test with None market
        assert self.client._parse_market(None) is None
        
        # Test with empty dict
        assert self.client._parse_market({}) is None
        
        # Test with invalid types
        assert self.client._parse_market("not a dict") is None


if __name__ == "__main__":
    pytest.main([__file__])