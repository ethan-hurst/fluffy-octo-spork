"""
Unit tests for Polymarket CLOB API client functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
import json

from src.clients.polymarket.client import PolymarketClient
from src.clients.polymarket.models import Market, Token, MarketPrice, MarketsResponse


class TestPolymarketClient:
    """Test cases for PolymarketClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = PolymarketClient()
        
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
            "end_date_iso": (now + timedelta(days=300)).isoformat()
        }
        
        self.test_markets_response = [
            self.test_market_data,
            {
                "condition_id": "test_condition_456",
                "question": "Will Bitcoin reach $100,000 by end of 2024?",
                "description": "Bitcoin price prediction",
                "category": "Cryptocurrency",
                "active": True,
                "closed": False,
                "volume": "875000.25",
                "end_date_iso": (now + timedelta(days=60)).isoformat()
            }
        ]
        
        self.test_orderbook_data = {
            "market": "test_condition_123",
            "asset_id": "asset_123",
            "bids": [
                {"price": "0.48", "size": "1000.0"},
                {"price": "0.47", "size": "2500.0"},
                {"price": "0.46", "size": "1800.0"}
            ],
            "asks": [
                {"price": "0.52", "size": "1200.0"},
                {"price": "0.53", "size": "2000.0"},
                {"price": "0.54", "size": "1500.0"}
            ]
        }
        
        self.test_stats_data = {
            "condition_id": "test_condition_123",
            "volume_24h": "125000.75",
            "price_change_24h": "0.025",
            "last_trade_price": "0.485",
            "bid": "0.48",
            "ask": "0.52",
            "trades_24h": 1250
        }
        
    @pytest.mark.asyncio
    async def test_get_markets_success(self):
        """Test successful market data retrieval."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_markets_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            markets = await self.client.get_markets()
            
            assert len(markets) == 2
            assert isinstance(markets[0], Market)
            assert markets[0].condition_id == "test_condition_123"
            assert markets[0].question == "Will Donald Trump win the 2024 presidential election?"
            assert markets[0].volume == 1250000.50
            assert markets[0].active is True
            
    @pytest.mark.asyncio
    async def test_get_markets_api_error(self):
        """Test market data retrieval with API error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock API error response
            mock_response = MagicMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            markets = await self.client.get_markets()
            
            assert markets == []  # Should return empty list on error
            
    @pytest.mark.asyncio
    async def test_get_markets_network_error(self):
        """Test market data retrieval with network error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock network error
            mock_get.side_effect = aiohttp.ClientError("Network error")
            
            markets = await self.client.get_markets()
            
            assert markets == []  # Should return empty list on error
            
    @pytest.mark.asyncio
    async def test_get_markets_with_filters(self):
        """Test market data retrieval with filters."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[self.test_markets_response[0]])
            mock_get.return_value.__aenter__.return_value = mock_response
            
            markets = await self.client.get_markets(
                category="Politics",
                active_only=True,
                min_volume=1000000.0
            )
            
            # Verify the request was made with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "category=Politics" in str(call_args) or "Politics" in str(call_args)
            
            assert len(markets) == 1
            assert markets[0].category == "Politics"
            
    @pytest.mark.asyncio
    async def test_get_market_by_id_success(self):
        """Test successful single market retrieval."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_market_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            market = await self.client.get_market_by_id("test_condition_123")
            
            assert isinstance(market, Market)
            assert market.condition_id == "test_condition_123"
            assert market.question == "Will Donald Trump win the 2024 presidential election?"
            
    @pytest.mark.asyncio
    async def test_get_market_by_id_not_found(self):
        """Test single market retrieval when market not found."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Not Found")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            market = await self.client.get_market_by_id("nonexistent_id")
            
            assert market is None
            
    @pytest.mark.asyncio
    async def test_get_orderbook_success(self):
        """Test successful orderbook retrieval."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_orderbook_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            orderbook = await self.client.get_orderbook("test_condition_123")
            
            assert isinstance(orderbook, OrderBook)
            assert orderbook.market == "test_condition_123"
            assert len(orderbook.bids) == 3
            assert len(orderbook.asks) == 3
            
            # Check bid/ask ordering and structure
            assert orderbook.bids[0].price == 0.48  # Highest bid first
            assert orderbook.asks[0].price == 0.52  # Lowest ask first
            assert orderbook.bids[0].size == 1000.0
            
    @pytest.mark.asyncio
    async def test_get_orderbook_error(self):
        """Test orderbook retrieval with error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Bad Request")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            orderbook = await self.client.get_orderbook("invalid_market")
            
            assert orderbook is None
            
    @pytest.mark.asyncio
    async def test_get_market_stats_success(self):
        """Test successful market statistics retrieval."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=self.test_stats_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            stats = await self.client.get_market_stats("test_condition_123")
            
            assert isinstance(stats, MarketStats)
            assert stats.condition_id == "test_condition_123"
            assert stats.volume_24h == 125000.75
            assert stats.price_change_24h == 0.025
            assert stats.last_trade_price == 0.485
            assert stats.trades_24h == 1250
            
    @pytest.mark.asyncio
    async def test_get_market_stats_error(self):
        """Test market statistics retrieval with error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Connection failed")
            
            stats = await self.client.get_market_stats("test_condition_123")
            
            assert stats is None
            
    def test_build_markets_url_no_params(self):
        """Test URL building without parameters."""
        url = self.client._build_markets_url()
        assert url == f"{self.client.base_url}/markets"
        
    def test_build_markets_url_with_params(self):
        """Test URL building with parameters."""
        url = self.client._build_markets_url(
            category="Politics",
            active_only=True,
            min_volume=1000000.0
        )
        
        assert self.client.base_url in url
        assert "category=Politics" in url
        assert "active_only=true" in url or "active=true" in url
        assert "min_volume=1000000.0" in url or "1000000" in url
        
    def test_parse_market_data_valid(self):
        """Test parsing valid market data."""
        market = self.client._parse_market_data(self.test_market_data)
        
        assert isinstance(market, Market)
        assert market.condition_id == "test_condition_123"
        assert market.question == "Will Donald Trump win the 2024 presidential election?"
        assert market.category == "Politics"
        assert market.active is True
        assert market.volume == 1250000.50
        
    def test_parse_market_data_invalid(self):
        """Test parsing invalid market data."""
        invalid_data = {
            "condition_id": "test_123",
            # Missing required fields
        }
        
        market = self.client._parse_market_data(invalid_data)
        assert market is None
        
    def test_parse_market_data_type_conversion_error(self):
        """Test parsing market data with type conversion errors."""
        invalid_data = {
            "condition_id": "test_123",
            "question": "Test question",
            "volume": "invalid_number",  # Should cause conversion error
            "active": True,
            "closed": False
        }
        
        market = self.client._parse_market_data(invalid_data)
        assert market is None
        
    def test_parse_orderbook_data_valid(self):
        """Test parsing valid orderbook data."""
        orderbook = self.client._parse_orderbook_data(self.test_orderbook_data)
        
        assert isinstance(orderbook, OrderBook)
        assert orderbook.market == "test_condition_123"
        assert len(orderbook.bids) == 3
        assert len(orderbook.asks) == 3
        
        # Verify order structure
        assert all(isinstance(bid, Order) for bid in orderbook.bids)
        assert all(isinstance(ask, Order) for ask in orderbook.asks)
        assert all(bid.side == OrderSide.BID for bid in orderbook.bids)
        assert all(ask.side == OrderSide.ASK for ask in orderbook.asks)
        
    def test_parse_orderbook_data_invalid(self):
        """Test parsing invalid orderbook data."""
        invalid_data = {
            "market": "test_market",
            "bids": "invalid_format",  # Should be list
            "asks": []
        }
        
        orderbook = self.client._parse_orderbook_data(invalid_data)
        assert orderbook is None
        
    def test_parse_order_valid(self):
        """Test parsing valid order data."""
        order_data = {"price": "0.48", "size": "1000.0"}
        order = self.client._parse_order(order_data, OrderSide.BID)
        
        assert isinstance(order, Order)
        assert order.price == 0.48
        assert order.size == 1000.0
        assert order.side == OrderSide.BID
        
    def test_parse_order_invalid(self):
        """Test parsing invalid order data."""
        invalid_order = {"price": "invalid", "size": "1000.0"}
        order = self.client._parse_order(invalid_order, OrderSide.BID)
        
        assert order is None
        
    def test_parse_market_stats_valid(self):
        """Test parsing valid market statistics."""
        stats = self.client._parse_market_stats(self.test_stats_data)
        
        assert isinstance(stats, MarketStats)
        assert stats.condition_id == "test_condition_123"
        assert stats.volume_24h == 125000.75
        assert stats.price_change_24h == 0.025
        assert stats.last_trade_price == 0.485
        assert stats.bid == 0.48
        assert stats.ask == 0.52
        assert stats.trades_24h == 1250
        
    def test_parse_market_stats_invalid(self):
        """Test parsing invalid market statistics."""
        invalid_stats = {
            "condition_id": "test_123",
            "volume_24h": "invalid_number"
        }
        
        stats = self.client._parse_market_stats(invalid_stats)
        assert stats is None
        
    def test_market_model_creation(self):
        """Test Market model creation and validation."""
        now = datetime.now()
        market = Market(
            condition_id="test_id",
            question="Test question?",
            description="Test description",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=now
        )
        
        assert market.condition_id == "test_id"
        assert market.question == "Test question?"
        assert market.volume == 1000.0
        assert market.active is True
        assert isinstance(market.end_date_iso, datetime)
        
    def test_order_model_creation(self):
        """Test Order model creation and validation."""
        order = Order(
            price=0.75,
            size=1500.0,
            side=OrderSide.ASK
        )
        
        assert order.price == 0.75
        assert order.size == 1500.0
        assert order.side == OrderSide.ASK
        
    def test_orderbook_model_creation(self):
        """Test OrderBook model creation and validation."""
        bids = [
            Order(price=0.48, size=1000.0, side=OrderSide.BID),
            Order(price=0.47, size=2000.0, side=OrderSide.BID)
        ]
        asks = [
            Order(price=0.52, size=1200.0, side=OrderSide.ASK),
            Order(price=0.53, size=1800.0, side=OrderSide.ASK)
        ]
        
        orderbook = OrderBook(
            market="test_market",
            asset_id="test_asset",
            bids=bids,
            asks=asks
        )
        
        assert orderbook.market == "test_market"
        assert len(orderbook.bids) == 2
        assert len(orderbook.asks) == 2
        assert orderbook.spread == 0.04  # 0.52 - 0.48
        assert orderbook.mid_price == 0.50  # (0.48 + 0.52) / 2
        
    def test_market_stats_model_creation(self):
        """Test MarketStats model creation and validation."""
        stats = MarketStats(
            condition_id="test_condition",
            volume_24h=50000.0,
            price_change_24h=0.02,
            last_trade_price=0.65,
            bid=0.64,
            ask=0.66,
            trades_24h=150
        )
        
        assert stats.condition_id == "test_condition"
        assert stats.volume_24h == 50000.0
        assert stats.price_change_24h == 0.02
        assert stats.spread == 0.02  # 0.66 - 0.64
        assert stats.trades_24h == 150
        
    def test_order_side_enum(self):
        """Test OrderSide enum values."""
        assert OrderSide.BID.value == "bid"
        assert OrderSide.ASK.value == "ask"
        
    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test proper session management."""
        # Test that session is created when needed
        assert self.client.session is None
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[])
            mock_get.return_value.__aenter__.return_value = mock_response
            
            await self.client.get_markets()
            
            # Session should be created
            assert self.client.session is not None
            
        # Test session cleanup
        await self.client.close()
        
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        # This test verifies that rate limiting doesn't break normal operation
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[])
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Make multiple requests rapidly
            tasks = [self.client.get_markets() for _ in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed (rate limiter should handle the timing)
            assert all(isinstance(result, list) for result in results)
            
    def test_error_handling_consistency(self):
        """Test consistent error handling across methods."""
        # All methods should handle errors gracefully and return appropriate defaults
        test_cases = [
            (self.client._parse_market_data, {}),
            (self.client._parse_orderbook_data, {}),
            (self.client._parse_market_stats, {}),
        ]
        
        for parse_method, invalid_data in test_cases:
            result = parse_method(invalid_data)
            assert result is None  # Should return None for invalid data


if __name__ == "__main__":
    import asyncio
    pytest.main([__file__])