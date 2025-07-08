"""
Unit tests for RefinedSimpleAnalyzer.
"""

import pytest
from datetime import datetime, timedelta, timezone
from src.analyzers.refined_simple_analyzer import RefinedSimpleAnalyzer
from src.analyzers.simple_pattern_analyzer import SimpleOpportunity
from src.clients.polymarket.models import Market, MarketPrice, Token


class TestRefinedSimpleAnalyzer:
    """Test the refined simple analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return RefinedSimpleAnalyzer()
    
    @pytest.fixture
    def stable_market(self):
        """Create a stable market for testing."""
        return Market(
            condition_id="0x123",
            question="Will Team A beat Team B in the championship?",
            market_slug="team-a-vs-b",
            end_date_iso=datetime.now(timezone.utc) + timedelta(days=3),
            volume=25000,
            active=True,
            closed=False,
            tokens=[
                Token(token_id="token1", outcome="YES", price=0.50),
                Token(token_id="token2", outcome="NO", price=0.50)
            ],
            minimum_order_size=0.01
        )
    
    @pytest.fixture
    def volatile_market(self):
        """Create a volatile market for testing."""
        return Market(
            condition_id="0x456",
            question="Will Bitcoin reach $100k this week?",
            market_slug="btc-100k",
            end_date_iso=datetime.now(timezone.utc) + timedelta(days=4),
            volume=30000,
            active=True,
            closed=False,
            tokens=[
                Token(token_id="token1", outcome="YES", price=0.25),
                Token(token_id="token2", outcome="NO", price=0.75)
            ],
            minimum_order_size=0.01
        )
    
    def test_stable_time_decay_low_price(self, analyzer, stable_market):
        """Test stable time decay with low price."""
        price = MarketPrice(condition_id="0x123", yes_price=0.25, no_price=0.75, spread=0.02)
        
        opportunity = analyzer.analyze_market(stable_market, price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "STABLE_TIME_DECAY"
        assert opportunity.recommended_action == "SELL_YES"
        assert opportunity.confidence == 0.7
        assert "25%" in opportunity.reason
        assert "3 days left" in opportunity.reason
        
    def test_stable_time_decay_high_price(self, analyzer, stable_market):
        """Test stable time decay with high price."""
        price = MarketPrice(condition_id="0x123", yes_price=0.75, no_price=0.25, spread=0.02)
        
        opportunity = analyzer.analyze_market(stable_market, price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "STABLE_TIME_DECAY"
        assert opportunity.recommended_action == "SELL_NO"
        assert opportunity.confidence == 0.7
        
    def test_volatile_market_filtered(self, analyzer, volatile_market):
        """Test that volatile markets are filtered out."""
        price = MarketPrice(condition_id="0x456", yes_price=0.25, no_price=0.75, spread=0.02)
        
        opportunity = analyzer.analyze_market(volatile_market, price)
        
        assert opportunity is None  # Bitcoin markets should be filtered
        
    def test_crypto_keywords_filtered(self, analyzer):
        """Test various crypto keywords are filtered."""
        crypto_markets = [
            "Will Ethereum hit $5000?",
            "Will BTC break resistance?",
            "Will crypto market cap double?",
            "Will meme stocks moon?",
            "Will this go viral on TikTok?"
        ]
        
        for question in crypto_markets:
            market = Market(
                condition_id="0x789",
                question=question,
                market_slug="test",
                end_date_iso=datetime.now(timezone.utc) + timedelta(days=3),
                volume=20000,
                active=True,
                closed=False,
                tokens=[
                    Token(token_id="token1", outcome="YES", price=0.25),
                    Token(token_id="token2", outcome="NO", price=0.75)
                ],
                minimum_order_size=0.01
            )
            price = MarketPrice(condition_id="0x789", yes_price=0.25, no_price=0.75, spread=0.02)
            
            opportunity = analyzer.analyze_market(market, price)
            assert opportunity is None
            
    def test_stable_keywords_accepted(self, analyzer):
        """Test stable event keywords are accepted."""
        stable_questions = [
            "Will Lakers beat Celtics?",
            "Who will win the election?",
            "Will Team A win the championship?",
            "Rangers vs Angels game outcome"
        ]
        
        for question in stable_questions:
            market = Market(
                condition_id="0xabc",
                question=question,
                market_slug="test",
                end_date_iso=datetime.now(timezone.utc) + timedelta(days=3),
                volume=20000,
                active=True,
                closed=False,
                tokens=[
                    Token(token_id="token1", outcome="YES", price=0.25),
                    Token(token_id="token2", outcome="NO", price=0.75)
                ],
                minimum_order_size=0.01
            )
            price = MarketPrice(condition_id="0xabc", yes_price=0.25, no_price=0.75, spread=0.02)
            
            opportunity = analyzer.analyze_market(market, price)
            assert opportunity is not None  # Should find opportunity
            
    def test_extreme_mispricing_constitutional(self, analyzer):
        """Test extreme mispricing for constitutional changes."""
        market = Market(
            condition_id="0xdef",
            question="Will there be a constitutional amendment passed this month?",
            market_slug="constitutional",
            end_date_iso=datetime.now(timezone.utc) + timedelta(days=20),
            volume=15000,
            active=True,
            closed=False,
            tokens=[
                Token(token_id="token1", outcome="YES", price=0.20),
                Token(token_id="token2", outcome="NO", price=0.80)
            ],
            minimum_order_size=0.01
        )
        price = MarketPrice(condition_id="0xdef", yes_price=0.20, no_price=0.80, spread=0.02)
        
        opportunity = analyzer.analyze_market(market, price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "EXTREME_MISPRICING"
        assert opportunity.recommended_action == "BUY_NO"
        assert opportunity.confidence == 0.9
        assert abs(opportunity.edge - 0.15) < 0.001  # 0.20 - 0.05
        
    def test_low_volume_filtered(self, analyzer, stable_market):
        """Test low volume markets are filtered."""
        stable_market.volume = 5000  # Below threshold
        price = MarketPrice(condition_id="0x123", yes_price=0.25, no_price=0.75, spread=0.02)
        
        opportunity = analyzer.analyze_market(stable_market, price)
        
        assert opportunity is None
        
    def test_days_left_boundary_conditions(self, analyzer, stable_market):
        """Test boundary conditions for days left."""
        price = MarketPrice(condition_id="0x123", yes_price=0.25, no_price=0.75, spread=0.02)
        
        # 0 days left - should not find opportunity
        stable_market.end_date_iso = datetime.now(timezone.utc) + timedelta(hours=12)
        opportunity = analyzer.analyze_market(stable_market, price)
        assert opportunity is None
        
        # 1 day left - should find opportunity
        stable_market.end_date_iso = datetime.now(timezone.utc) + timedelta(days=1)
        opportunity = analyzer.analyze_market(stable_market, price)
        assert opportunity is not None
        
        # 7 days left - should find opportunity
        stable_market.end_date_iso = datetime.now(timezone.utc) + timedelta(days=7)
        opportunity = analyzer.analyze_market(stable_market, price)
        assert opportunity is not None
        
        # 8 days left - should not find opportunity
        stable_market.end_date_iso = datetime.now(timezone.utc) + timedelta(days=8)
        opportunity = analyzer.analyze_market(stable_market, price)
        assert opportunity is None
        
    def test_price_boundaries(self, analyzer, stable_market):
        """Test price boundary conditions."""
        # Price too close to extreme (< 0.15)
        price = MarketPrice(condition_id="0x123", yes_price=0.10, no_price=0.90, spread=0.02)
        opportunity = analyzer.analyze_market(stable_market, price)
        assert opportunity is None
        
        # Price at lower boundary (0.15)
        price = MarketPrice(condition_id="0x123", yes_price=0.15, no_price=0.85, spread=0.02)
        opportunity = analyzer.analyze_market(stable_market, price)
        assert opportunity is None  # Just outside range
        
        # Price just inside range (0.16)
        price = MarketPrice(condition_id="0x123", yes_price=0.16, no_price=0.84, spread=0.02)
        opportunity = analyzer.analyze_market(stable_market, price)
        assert opportunity is not None
        
    def test_edge_calculation(self, analyzer, stable_market):
        """Test edge calculation accuracy."""
        # Low price case
        price = MarketPrice(condition_id="0x123", yes_price=0.20, no_price=0.80, spread=0.02)
        opportunity = analyzer.analyze_market(stable_market, price)
        
        assert opportunity is not None
        expected_edge = (0.35 - 0.20) * 0.5  # (0.35 - price) * 0.5
        assert abs(opportunity.edge - expected_edge) < 0.001
        
        # High price case
        price = MarketPrice(condition_id="0x123", yes_price=0.70, no_price=0.30, spread=0.02)
        opportunity = analyzer.analyze_market(stable_market, price)
        
        assert opportunity is not None
        expected_edge = (0.70 - 0.65) * 0.5  # (price - 0.65) * 0.5
        assert abs(opportunity.edge - expected_edge) < 0.001