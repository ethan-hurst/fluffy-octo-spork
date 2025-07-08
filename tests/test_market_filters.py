"""
Unit tests for market filtering functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.utils.market_filters import MarketFilter
from src.clients.polymarket.models import Market, Token


class TestMarketFilter:
    """Test cases for MarketFilter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.filter = MarketFilter()
        
        # Create test markets
        now = datetime.now()
        self.markets = [
            Market(
                condition_id="market1",
                question="Will Trump win the 2024 election?",
                description="Political market about Trump election",
                category="Politics",
                active=True,
                closed=False,
                volume=50000.0,
                end_date_iso=now + timedelta(days=20),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            Market(
                condition_id="market2", 
                question="Will Bitcoin reach $100k by end of year?",
                description="Crypto market prediction",
                category="Cryptocurrency",
                active=True,
                closed=False,
                volume=25000.0,
                end_date_iso=now + timedelta(days=60),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            Market(
                condition_id="market3",
                question="Will the Lakers win the NBA championship?",
                description="Sports prediction market",
                category="Sports",
                active=True,
                closed=False,
                volume=75000.0,
                end_date_iso=now + timedelta(days=120),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            Market(
                condition_id="market4",
                question="Will global temperatures rise by 2°C by 2050?",
                description="Climate change prediction",
                category="Climate",
                active=True,
                closed=False,
                volume=15000.0,
                end_date_iso=now + timedelta(days=45),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            )
        ]
        
    def test_no_filters_returns_all_markets(self):
        """Test that no filters returns all markets."""
        # Clear all filters
        self.filter.categories = []
        self.filter.keywords = []
        self.filter.time_horizon_filter = None
        self.filter.max_days_to_resolution = None
        self.filter.min_days_to_resolution = None
        
        result = self.filter.filter_markets(self.markets)
        assert len(result) == 4
        
    def test_category_filter(self):
        """Test category filtering."""
        self.filter.categories = ["politics"]
        self.filter.keywords = []
        self.filter.time_horizon_filter = None
        
        result = self.filter.filter_markets(self.markets)
        assert len(result) == 1
        assert result[0].condition_id == "market1"
        
    def test_keyword_filter(self):
        """Test keyword filtering."""
        self.filter.categories = []
        self.filter.keywords = ["trump", "bitcoin"]
        self.filter.time_horizon_filter = None
        
        result = self.filter.filter_markets(self.markets)
        assert len(result) == 2
        condition_ids = [m.condition_id for m in result]
        assert "market1" in condition_ids  # Trump market
        assert "market2" in condition_ids  # Bitcoin market
        
    def test_closing_soon_filter(self):
        """Test closing soon time filter."""
        self.filter.categories = []
        self.filter.keywords = []
        self.filter.time_horizon_filter = "closing_soon"
        
        result = self.filter.filter_markets(self.markets)
        assert len(result) == 1
        assert result[0].condition_id == "market1"  # 20 days <= 30 days
        
    def test_medium_term_filter(self):
        """Test medium term time filter."""
        self.filter.categories = []
        self.filter.keywords = []
        self.filter.time_horizon_filter = "medium_term"
        
        result = self.filter.filter_markets(self.markets)
        assert len(result) == 2
        condition_ids = [m.condition_id for m in result]
        assert "market2" in condition_ids  # 60 days
        assert "market4" in condition_ids  # 45 days
        
    def test_long_term_filter(self):
        """Test long term time filter."""
        self.filter.categories = []
        self.filter.keywords = []
        self.filter.time_horizon_filter = "long_term"
        
        result = self.filter.filter_markets(self.markets)
        assert len(result) == 1
        assert result[0].condition_id == "market3"  # 120 days > 90 days
        
    def test_max_days_filter(self):
        """Test maximum days filter."""
        self.filter.categories = []
        self.filter.keywords = []
        self.filter.time_horizon_filter = None
        self.filter.max_days_to_resolution = 50
        
        result = self.filter.filter_markets(self.markets)
        assert len(result) == 2
        condition_ids = [m.condition_id for m in result]
        assert "market1" in condition_ids  # 20 days
        assert "market4" in condition_ids  # 45 days
        
    def test_combined_filters(self):
        """Test combination of multiple filters."""
        self.filter.categories = ["politics", "cryptocurrency"]
        self.filter.keywords = []
        self.filter.time_horizon_filter = None
        self.filter.max_days_to_resolution = 70
        
        result = self.filter.filter_markets(self.markets)
        assert len(result) == 2
        condition_ids = [m.condition_id for m in result]
        assert "market1" in condition_ids  # Politics + 20 days
        assert "market2" in condition_ids  # Crypto + 60 days
        
    def test_volume_sorting(self):
        """Test volume sorting."""
        self.filter.categories = []
        self.filter.keywords = []
        self.filter.time_horizon_filter = None
        self.filter.sort_by_volume = True
        
        result = self.filter.filter_markets(self.markets)
        
        # Should be sorted by volume (highest first)
        expected_order = ["market3", "market1", "market2", "market4"]  # 75k, 50k, 25k, 15k
        actual_order = [m.condition_id for m in result]
        assert actual_order == expected_order
        
    def test_parse_comma_separated(self):
        """Test comma-separated string parsing."""
        result = self.filter._parse_comma_separated("politics, crypto, sports")
        assert result == ["politics", "crypto", "sports"]
        
        result = self.filter._parse_comma_separated(None)
        assert result == []
        
        result = self.filter._parse_comma_separated("")
        assert result == []
        
    def test_filter_summary(self):
        """Test filter summary generation."""
        # No filters
        self.filter.categories = []
        self.filter.keywords = []
        self.filter.time_horizon_filter = None
        summary = self.filter.get_filter_summary()
        assert "No filters active" in summary
        
        # With filters
        self.filter.categories = ["politics"]
        self.filter.keywords = ["trump"]
        self.filter.time_horizon_filter = "closing_soon"
        summary = self.filter.get_filter_summary()
        assert "politics" in summary
        assert "trump" in summary
        assert "closing_soon" in summary


if __name__ == "__main__":
    pytest.main([__file__])