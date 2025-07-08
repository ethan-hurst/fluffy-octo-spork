"""
Unit tests for SimplePatternAnalyzer.
"""

import pytest
from datetime import datetime, timedelta, timezone
from src.analyzers.simple_pattern_analyzer import SimplePatternAnalyzer, SimpleOpportunity
from src.clients.polymarket.models import Market, MarketPrice, Token
from src.clients.news.models import NewsArticle


class TestSimplePatternAnalyzer:
    """Test the simple pattern analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return SimplePatternAnalyzer()
    
    @pytest.fixture
    def base_market(self):
        """Create a base market for testing."""
        return Market(
            condition_id="0x123",
            question="Will the Rangers beat the Angels?",
            market_slug="rangers-vs-angels",
            end_date_iso=datetime.now(timezone.utc) + timedelta(days=5),
            volume=15000,
            liquidity=5000,
            description="Baseball game",
            active=True,
            closed=False,
            tokens=[
                Token(token_id="token1", outcome="YES", price=0.25),
                Token(token_id="token2", outcome="NO", price=0.75)
            ],
            minimum_order_size=0.01
        )
    
    @pytest.fixture
    def base_price(self):
        """Create a base market price."""
        return MarketPrice(
            condition_id="0x123",
            yes_price=0.25,
            no_price=0.75,
            spread=0.02
        )
    
    def test_time_decay_opportunity_low_price(self, analyzer, base_market, base_price):
        """Test time decay pattern with low price."""
        # Market ending in 5 days with price at 25%
        opportunity = analyzer.analyze_market(base_market, base_price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "TIME_DECAY"
        assert opportunity.recommended_action == "BUY_YES"
        assert opportunity.confidence == 0.7
        assert "5 days left" in opportunity.reason
        
    def test_time_decay_opportunity_high_price(self, analyzer, base_market):
        """Test time decay pattern with high price."""
        # High price near end
        price = MarketPrice(condition_id="0x123", yes_price=0.75, no_price=0.25, spread=0.02)
        
        opportunity = analyzer.analyze_market(base_market, price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "TIME_DECAY"
        assert opportunity.recommended_action == "BUY_NO"
        assert opportunity.confidence == 0.7
        
    def test_no_opportunity_middle_price(self, analyzer, base_market):
        """Test no opportunity for middle prices."""
        # Price at 50/50
        price = MarketPrice(condition_id="0x123", yes_price=0.50, no_price=0.50, spread=0.02)
        
        opportunity = analyzer.analyze_market(base_market, price)
        
        assert opportunity is None
        
    def test_no_opportunity_too_far_out(self, analyzer, base_market, base_price):
        """Test no opportunity for markets too far in future."""
        # Market ending in 30 days
        base_market.end_date_iso = datetime.now(timezone.utc) + timedelta(days=30)
        
        opportunity = analyzer.analyze_market(base_market, base_price)
        
        assert opportunity is None
        
    def test_extreme_pricing_longshot(self, analyzer):
        """Test extreme pricing pattern for longshots."""
        market = Market(
            condition_id="0x456",
            question="Will Bitcoin reach $1 million by end of year?",
            market_slug="btc-million",
            end_date_iso=datetime.now(timezone.utc) + timedelta(days=30),
            volume=20000,
            active=True,
            closed=False,
            tokens=[
                Token(token_id="token1", outcome="YES", price=0.25),
                Token(token_id="token2", outcome="NO", price=0.75)
            ],
            minimum_order_size=0.01
        )
        price = MarketPrice(condition_id="0x456", yes_price=0.25, no_price=0.75, spread=0.02)
        
        opportunity = analyzer.analyze_market(market, price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "EXTREME_PRICE"
        assert opportunity.recommended_action == "BUY_NO"
        assert opportunity.confidence == 0.6
        
    def test_extreme_pricing_certainty(self, analyzer):
        """Test extreme pricing for near certainties."""
        market = Market(
            condition_id="0x789",
            question="Will the president complete their term?",
            market_slug="complete-term",
            end_date_iso=datetime.now(timezone.utc) + timedelta(days=100),
            volume=50000,
            active=True,
            closed=False,
            tokens=[
                Token(token_id="token1", outcome="YES", price=0.80),
                Token(token_id="token2", outcome="NO", price=0.20)
            ],
            minimum_order_size=0.01
        )
        price = MarketPrice(condition_id="0x789", yes_price=0.80, no_price=0.20, spread=0.02)
        
        opportunity = analyzer.analyze_market(market, price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "EXTREME_PRICE"
        assert opportunity.recommended_action == "BUY_YES"
        
    def test_structural_inefficiency_binary(self, analyzer):
        """Test structural inefficiency for true binary events."""
        market = Market(
            condition_id="0xabc",
            question="Will the coin flip result in heads?",
            market_slug="coin-flip",
            end_date_iso=datetime.now(timezone.utc) + timedelta(days=1),
            volume=10000,
            active=True,
            closed=False,
            tokens=[
                Token(token_id="token1", outcome="YES", price=0.70),
                Token(token_id="token2", outcome="NO", price=0.30)
            ],
            minimum_order_size=0.01
        )
        price = MarketPrice(condition_id="0xabc", yes_price=0.70, no_price=0.30, spread=0.02)
        
        opportunity = analyzer.analyze_market(market, price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "STRUCTURAL"
        assert opportunity.recommended_action == "BUY_NO"
        assert opportunity.confidence == 0.8
        
    def test_constitutional_impossibility(self, analyzer):
        """Test constitutional impossibility pattern."""
        market = Market(
            condition_id="0xdef",
            question="Will there be a constitutional amendment this week?",
            market_slug="constitutional",
            end_date_iso=datetime.now(timezone.utc) + timedelta(days=7),
            volume=15000,
            active=True,
            closed=False,
            tokens=[
                Token(token_id="token1", outcome="YES", price=0.15),
                Token(token_id="token2", outcome="NO", price=0.85)
            ],
            minimum_order_size=0.01
        )
        price = MarketPrice(condition_id="0xdef", yes_price=0.15, no_price=0.85, spread=0.02)
        
        opportunity = analyzer.analyze_market(market, price)
        
        assert opportunity is not None
        assert opportunity.pattern_type == "STRUCTURAL"
        assert opportunity.recommended_action == "BUY_NO"
        assert opportunity.confidence > 0.8
        
    def test_news_overreaction_high_price(self, analyzer, base_market):
        """Test news overreaction pattern."""
        price = MarketPrice(condition_id="0x123", yes_price=0.80, no_price=0.20, spread=0.02)
        
        # Create many relevant news articles
        news_articles = []
        for i in range(10):
            news_articles.append(NewsArticle(
                title=f"Rangers dominate in game {i}",
                description="Rangers showing strong performance",
                url=f"https://news.com/{i}",
                published_at=datetime.now(timezone.utc),
                source="Sports News"
            ))
        
        opportunity = analyzer._check_news_overreaction(
            base_market, price, news_articles
        )
        
        assert opportunity is not None
        assert opportunity.pattern_type == "NEWS_OVERREACTION"
        assert opportunity.recommended_action == "BUY_NO"
        assert opportunity.confidence == 0.5
        
    def test_calculate_fair_value_buy_yes(self, analyzer):
        """Test fair value calculation for buy yes."""
        opportunity = SimpleOpportunity(
            market=None,
            current_price=0.30,
            recommended_action="BUY_YES",
            edge=0.20,
            confidence=0.7,
            reason="Test",
            pattern_type="TEST"
        )
        
        fair_yes, fair_no = analyzer.calculate_fair_value(opportunity)
        
        assert fair_yes == 0.50  # 0.30 + 0.20
        assert fair_no == 0.50  # 1.0 - 0.50
        
    def test_calculate_fair_value_buy_no(self, analyzer):
        """Test fair value calculation for buy no."""
        opportunity = SimpleOpportunity(
            market=None,
            current_price=0.70,
            recommended_action="BUY_NO",
            edge=0.15,
            confidence=0.8,
            reason="Test",
            pattern_type="TEST"
        )
        
        fair_yes, fair_no = analyzer.calculate_fair_value(opportunity)
        
        assert abs(fair_yes - 0.55) < 0.001  # 0.70 - 0.15
        assert abs(fair_no - 0.45) < 0.001  # 1.0 - 0.55
        
    def test_low_volume_filter(self, analyzer, base_market, base_price):
        """Test that low volume markets are filtered."""
        base_market.volume = 1000  # Below threshold
        
        opportunity = analyzer.analyze_market(base_market, base_price)
        
        assert opportunity is None
        
    def test_extreme_price_filter(self, analyzer, base_market):
        """Test that extreme prices are filtered."""
        price = MarketPrice(condition_id="0x123", yes_price=0.99, no_price=0.01, spread=0.02)
        
        opportunity = analyzer.analyze_market(base_market, price)
        
        assert opportunity is None