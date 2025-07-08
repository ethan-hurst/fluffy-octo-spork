"""
Unit tests for fair value engine functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from src.analyzers.fair_value_engine import FairValueEngine, BaseRateData
from src.clients.polymarket.models import Market, Token
from src.clients.news.models import NewsArticle, NewsSource
from src.analyzers.bayesian_updater import ProbabilityDistribution
from src.analyzers.llm_news_analyzer import MarketNewsAnalysis


class TestFairValueEngine:
    """Test cases for FairValueEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = FairValueEngine()
        
        # Create test markets
        now = datetime.now()
        self.markets = {
            "trump_election": Market(
                condition_id="trump_2024",
                question="Will Donald Trump win the 2024 presidential election?",
                description="Presidential election prediction market",
                category="Politics",
                active=True,
                closed=False,
                volume=1000000.0,
                end_date_iso=now + timedelta(days=300),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            "btc_etf": Market(
                condition_id="btc_etf_2024", 
                question="Will a Bitcoin ETF be approved by the SEC in 2024?",
                description="Bitcoin ETF approval prediction",
                category="Cryptocurrency",
                active=True,
                closed=False,
                volume=500000.0,
                end_date_iso=now + timedelta(days=180),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            "constitutional_amendment": Market(
                condition_id="term_limits_2024",
                question="Will the 22nd Amendment be repealed before 2025?",
                description="Constitutional amendment to repeal presidential term limits",
                category="Politics",
                active=True,
                closed=False,
                volume=100000.0,
                end_date_iso=now + timedelta(days=365),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            "nfl_coaching": Market(
                condition_id="coach_fire_2024",
                question="Will the Jets fire their head coach this season?",
                description="NFL coaching change prediction",
                category="Sports",
                active=True,
                closed=False,
                volume=200000.0,
                end_date_iso=now + timedelta(days=120),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            "multi_party_election": Market(
                condition_id="japan_ldp_2024",
                question="Will the LDP win the most seats in Japan's next election?",
                description="Japanese multi-party election prediction",
                category="Politics",
                active=True,
                closed=False,
                volume=300000.0,
                end_date_iso=now + timedelta(days=200),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            )
        }
        
        # Create test news articles
        self.news_articles = [
            NewsArticle(
                title="Trump Leads in Battleground States",
                description="Former president showing strength in key swing states",
                url="https://example.com/trump-leads",
                published_at=now - timedelta(hours=2),
                source=NewsSource(name="Reuters")
            ),
            NewsArticle(
                title="SEC Chairman Signals ETF Openness",
                description="Regulatory head indicates willingness to approve crypto products",
                url="https://example.com/sec-etf",
                published_at=now - timedelta(hours=1),
                source=NewsSource(name="Bloomberg")
            )
        ]
        
    def test_base_rate_data_creation(self):
        """Test BaseRateData dataclass creation."""
        base_rate = BaseRateData(
            probability=0.45,
            confidence=0.8,
            sample_size=100,
            last_updated=datetime.now(),
            source="historical_data"
        )
        
        assert base_rate.probability == 0.45
        assert base_rate.confidence == 0.8
        assert base_rate.sample_size == 100
        assert base_rate.source == "historical_data"
        
    @pytest.mark.asyncio
    async def test_calculate_fair_value_political_market(self):
        """Test fair value calculation for political markets."""
        market = self.markets["trump_election"]
        
        with patch.object(self.engine.political_model, 'calculate_political_probability') as mock_political:
            mock_political.return_value = ProbabilityDistribution(
                mean=0.48, std_dev=0.1, confidence_interval=(0.38, 0.58), sample_size=1000
            )
            
            yes_price, no_price, reasoning = await self.engine.calculate_fair_value(
                market, self.news_articles
            )
            
            assert abs(yes_price - 0.48) < 0.01
            assert abs(no_price - 0.52) < 0.01
            assert "Advanced political model" in reasoning
            mock_political.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_calculate_fair_value_crypto_market(self):
        """Test fair value calculation for crypto markets."""
        market = self.markets["btc_etf"]
        
        with patch.object(self.engine.crypto_model, 'calculate_crypto_probability') as mock_crypto:
            mock_crypto.return_value = ProbabilityDistribution(
                mean=0.75, std_dev=0.08, confidence_interval=(0.67, 0.83), sample_size=500
            )
            
            yes_price, no_price, reasoning = await self.engine.calculate_fair_value(
                market, self.news_articles
            )
            
            assert abs(yes_price - 0.75) < 0.01
            assert abs(no_price - 0.25) < 0.01
            assert "Advanced crypto/financial model" in reasoning
            mock_crypto.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_calculate_fair_value_standard_approach(self):
        """Test fair value calculation using standard approach."""
        market = self.markets["constitutional_amendment"]
        
        with patch.object(self.engine, '_calculate_llm_news_adjustment', new_callable=AsyncMock) as mock_news:
            mock_news.return_value = (0.01, "Minimal news impact")
            
            yes_price, no_price, reasoning = await self.engine.calculate_fair_value(
                market, self.news_articles
            )
            
            # Constitutional amendments should have very low probability
            assert yes_price < 0.05
            assert no_price > 0.95
            assert "Bayesian Fair Value" in reasoning
            
    @pytest.mark.asyncio
    async def test_calculate_standard_fair_value_with_evidence(self):
        """Test standard fair value calculation with evidence."""
        market = self.markets["nfl_coaching"]
        
        with patch.object(self.engine, '_calculate_llm_news_adjustment', new_callable=AsyncMock) as mock_news:
            mock_news.return_value = (0.05, "Negative coaching sentiment")
            
            yes_price, no_price, reasoning = await self.engine._calculate_standard_fair_value(
                market, self.news_articles
            )
            
            assert 0.0 <= yes_price <= 1.0
            assert 0.0 <= no_price <= 1.0
            assert abs(yes_price + no_price - 1.0) < 0.01
            assert "Bayesian Fair Value" in reasoning
            
    def test_determine_market_type_political(self):
        """Test market type determination for political markets."""
        market_type = self.engine._determine_market_type(self.markets["trump_election"])
        assert market_type == "political"
        
    def test_determine_market_type_crypto(self):
        """Test market type determination for crypto markets."""
        market_type = self.engine._determine_market_type(self.markets["btc_etf"])
        assert market_type == "crypto"
        
    def test_determine_market_type_sports(self):
        """Test market type determination for sports markets."""
        market_type = self.engine._determine_market_type(self.markets["nfl_coaching"])
        assert market_type == "sports"
        
    def test_is_political_binary_true(self):
        """Test political binary market identification."""
        assert self.engine._is_political_binary(self.markets["trump_election"]) is True
        
    def test_is_political_binary_false(self):
        """Test non-political market identification."""
        assert self.engine._is_political_binary(self.markets["btc_etf"]) is False
        
    def test_is_crypto_financial_true(self):
        """Test crypto/financial market identification."""
        assert self.engine._is_crypto_financial(self.markets["btc_etf"]) is True
        
    def test_is_crypto_financial_false(self):
        """Test non-crypto market identification."""
        assert self.engine._is_crypto_financial(self.markets["trump_election"]) is False
        
    def test_is_sports_event_true(self):
        """Test sports event market identification."""
        assert self.engine._is_sports_event(self.markets["nfl_coaching"]) is True
        
    def test_is_sports_event_false(self):
        """Test non-sports market identification."""
        assert self.engine._is_sports_event(self.markets["trump_election"]) is False
        
    def test_is_constitutional_amendment_true(self):
        """Test constitutional amendment identification."""
        assert self.engine._is_constitutional_amendment(self.markets["constitutional_amendment"]) is True
        
    def test_is_constitutional_amendment_false(self):
        """Test non-constitutional market identification."""
        assert self.engine._is_constitutional_amendment(self.markets["trump_election"]) is False
        
    def test_is_multi_party_election_true(self):
        """Test multi-party election identification."""
        assert self.engine._is_multi_party_election(self.markets["multi_party_election"]) is True
        
    def test_is_multi_party_election_false(self):
        """Test non-multi-party election identification."""
        assert self.engine._is_multi_party_election(self.markets["trump_election"]) is False
        
    def test_get_base_probability_constitutional_amendment(self):
        """Test base probability for constitutional amendments."""
        market = self.markets["constitutional_amendment"]
        base_prob, reasoning = self.engine._get_base_probability(market)
        
        assert base_prob < 0.05  # Should be very low
        assert "Constitutional amendment" in reasoning or "22nd Amendment" in reasoning
        
    def test_get_base_probability_multi_party_ldp(self):
        """Test base probability for LDP in multi-party election."""
        market = self.markets["multi_party_election"]
        base_prob, reasoning = self.engine._get_base_probability(market)
        
        assert 0.3 < base_prob < 0.5  # LDP should have reasonable probability
        assert "LDP" in reasoning
        
    def test_get_base_probability_political_binary(self):
        """Test base probability for binary political events."""
        market = self.markets["trump_election"]
        base_prob, reasoning = self.engine._get_base_probability(market)
        
        assert 0.35 < base_prob < 0.55  # Should be competitive
        assert "Trump" in reasoning or "election" in reasoning
        
    def test_calculate_multi_party_probability_ldp(self):
        """Test multi-party probability calculation for LDP."""
        market = self.markets["multi_party_election"]
        prob, reasoning = self.engine._calculate_multi_party_probability(market)
        
        assert prob == 0.42  # LDP historical rate
        assert "LDP" in reasoning
        
    def test_calculate_multi_party_probability_minor_party(self):
        """Test multi-party probability for minor party."""
        minor_party_market = Market(
            condition_id="minor_party",
            question="Will the Green Party win the most seats?",
            description="Minor party election prediction",
            category="Politics",
            active=True,
            closed=False,
            volume=50000.0,
            end_date_iso=datetime.now() + timedelta(days=100)
        )
        
        prob, reasoning = self.engine._calculate_multi_party_probability(minor_party_market)
        
        assert prob < 0.1  # Should be low for minor parties
        assert "minor" in reasoning.lower() or "green" in reasoning.lower()
        
    def test_calculate_political_binary_probability_president(self):
        """Test political binary probability for presidential election."""
        market = self.markets["trump_election"]
        prob, reasoning = self.engine._calculate_political_binary_probability(market)
        
        assert 0.4 < prob < 0.5  # Should be competitive
        assert "Trump" in reasoning
        
    def test_calculate_constitutional_probability_short_timeframe(self):
        """Test constitutional probability with short timeframe."""
        # Create market with short timeframe
        short_term_market = Market(
            condition_id="short_amendment",
            question="Will the 22nd Amendment be repealed by next month?",
            description="Short-term constitutional amendment",
            category="Politics",
            active=True,
            closed=False,
            volume=50000.0,
            end_date_iso=datetime.now() + timedelta(days=30)
        )
        
        prob, reasoning = self.engine._calculate_constitutional_probability(short_term_market)
        
        assert prob < 0.01  # Should be extremely low for short timeframe
        assert "impossible" in reasoning.lower() or "extremely unlikely" in reasoning.lower()
        
    def test_get_days_remaining_with_timezone(self):
        """Test days remaining calculation with timezone-aware datetime."""
        import pytz
        future_date = datetime.now(pytz.UTC) + timedelta(days=30)
        
        market = Market(
            condition_id="tz_test",
            question="Test market with timezone",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=future_date
        )
        
        days = self.engine._get_days_remaining(market)
        assert 29 <= days <= 31  # Should be around 30 days
        
    def test_get_days_remaining_none(self):
        """Test days remaining calculation with no end date."""
        market = Market(
            condition_id="no_date",
            question="Market without end date",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=None
        )
        
        days = self.engine._get_days_remaining(market)
        assert days is None
        
    def test_calculate_time_adjustment_very_close(self):
        """Test time adjustment for markets very close to resolution."""
        # Create market ending in 3 days
        close_market = Market(
            condition_id="close_market",
            question="Market ending soon",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=3)
        )
        
        adjustment, reasoning = self.engine._calculate_time_adjustment(close_market)
        
        assert adjustment == 0.0  # No adjustment for very close markets
        assert "Very close to resolution" in reasoning
        
    def test_calculate_time_adjustment_long_term(self):
        """Test time adjustment for long-term markets."""
        # Create market ending in 200 days
        long_term_market = Market(
            condition_id="long_market",
            question="Long-term market",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=200)
        )
        
        adjustment, reasoning = self.engine._calculate_time_adjustment(long_term_market)
        
        assert adjustment < 0.0  # Should be negative adjustment
        assert "Long-term event" in reasoning
        
    def test_calculate_market_adjustment_high_volume(self):
        """Test market adjustment for high-volume markets."""
        high_volume_market = Market(
            condition_id="high_vol",
            question="High volume market",
            description="Test",
            category="Politics",
            active=True,
            closed=False,
            volume=150000.0,  # High volume
            end_date_iso=datetime.now() + timedelta(days=100)
        )
        
        adjustment, reasoning = self.engine._calculate_market_adjustment(high_volume_market)
        
        assert adjustment > 0.0  # Should be positive adjustment
        assert "high volume" in reasoning
        
    def test_calculate_market_adjustment_low_volume(self):
        """Test market adjustment for low-volume markets."""
        low_volume_market = Market(
            condition_id="low_vol",
            question="Low volume market",
            description="Test",
            category="Crypto",
            active=True,
            closed=False,
            volume=1000.0,  # Low volume
            end_date_iso=datetime.now() + timedelta(days=100)
        )
        
        adjustment, reasoning = self.engine._calculate_market_adjustment(low_volume_market)
        
        assert adjustment < 0.0  # Should be negative adjustment
        assert "low volume" in reasoning and "crypto volatility" in reasoning
        
    @pytest.mark.asyncio
    async def test_calculate_llm_news_adjustment_success(self):
        """Test LLM news adjustment calculation."""
        market = self.markets["trump_election"]
        
        mock_analysis = NewsAnalysis(
            overall_sentiment=0.2,
            sentiment_confidence=0.8,
            news_impact_score=0.7,
            credible_sources_count=3,
            total_sources_count=4,
            probability_adjustment=0.03,
            key_insights=["Positive polling trend"],
            confidence_factors=["High-quality sources"],
            uncertainty_factors=["Early in cycle"]
        )
        
        with patch.object(self.engine.llm_news_analyzer, 'analyze_market_news', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis
            
            adjustment, reasoning = await self.engine._calculate_llm_news_adjustment(
                self.news_articles, market
            )
            
            assert adjustment == 0.03
            assert "LLM News Analysis" in reasoning
            assert "positive sentiment" in reasoning
            
    @pytest.mark.asyncio
    async def test_calculate_llm_news_adjustment_failure(self):
        """Test LLM news adjustment when analysis fails."""
        market = self.markets["trump_election"]
        
        with patch.object(self.engine.llm_news_analyzer, 'analyze_market_news', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("LLM API Error")
            
            adjustment, reasoning = await self.engine._calculate_llm_news_adjustment(
                self.news_articles, market
            )
            
            # Should fall back to simple analysis
            assert isinstance(adjustment, float)
            assert "Fallback news analysis" in reasoning
            
    def test_calculate_fallback_news_adjustment(self):
        """Test fallback news adjustment calculation."""
        positive_news = [
            NewsArticle(
                title="Positive Development in Market",
                description="Strong approval and good news for the outcome",
                url="https://example.com/positive",
                published_at=datetime.now(),
                source=NewsSource(name="Reuters")
            )
        ]
        
        adjustment, reasoning = self.engine._calculate_fallback_news_adjustment(
            positive_news, self.markets["trump_election"]
        )
        
        assert adjustment > 0.0  # Should be positive
        assert "Fallback news analysis" in reasoning
        assert "positive sentiment" in reasoning
        
    def test_simple_news_sentiment_positive(self):
        """Test simple sentiment analysis with positive keywords."""
        positive_news = [
            NewsArticle(
                title="Success and Victory in Latest Development",
                description="Strong growth and positive improvement seen",
                url="https://example.com/positive",
                published_at=datetime.now(),
                source=NewsSource(name="Reuters")
            )
        ]
        
        sentiment = self.engine._simple_news_sentiment(positive_news)
        assert sentiment > 0.0
        
    def test_simple_news_sentiment_negative(self):
        """Test simple sentiment analysis with negative keywords."""
        negative_news = [
            NewsArticle(
                title="Failure and Decline in Recent Events",
                description="Bad news with negative decline and loss",
                url="https://example.com/negative",
                published_at=datetime.now(),
                source=NewsSource(name="Reuters")
            )
        ]
        
        sentiment = self.engine._simple_news_sentiment(negative_news)
        assert sentiment < 0.0
        
    def test_simple_news_sentiment_neutral(self):
        """Test simple sentiment analysis with neutral content."""
        neutral_news = [
            NewsArticle(
                title="Regular Update on Market Status",
                description="Standard information about current conditions",
                url="https://example.com/neutral",
                published_at=datetime.now(),
                source=NewsSource(name="Reuters")
            )
        ]
        
        sentiment = self.engine._simple_news_sentiment(neutral_news)
        assert abs(sentiment) < 0.1  # Should be close to neutral
        
    def test_generate_bayesian_reasoning(self):
        """Test Bayesian reasoning generation."""
        distribution = ProbabilityDistribution(
            mean=0.65,
            std_dev=0.1,
            confidence_interval=(0.5, 0.8),
            sample_size=1000
        )
        
        reasoning = self.engine._generate_bayesian_reasoning(
            distribution, "Trump polling advantage"
        )
        
        assert "Base: Trump polling advantage" in reasoning
        assert "Bayesian Fair Value: 65.0%" in reasoning
        assert "Confidence Interval: 50.0% - 80.0%" in reasoning
        assert "Uncertainty:" in reasoning
        
    def test_learn_from_outcome(self):
        """Test learning from market outcomes."""
        # This should not raise an exception
        self.engine.learn_from_outcome("test_market", True, 0.75)
        
    def test_get_learning_suggestions(self):
        """Test getting learning suggestions."""
        suggestions = self.engine.get_learning_suggestions()
        assert isinstance(suggestions, list)
        
    def test_load_base_rates_placeholder(self):
        """Test base rates loading (placeholder implementation)."""
        base_rates = self.engine._load_base_rates()
        assert isinstance(base_rates, dict)
        assert len(base_rates) == 0  # Empty in current implementation
        
    def test_load_market_patterns_placeholder(self):
        """Test market patterns loading (placeholder implementation)."""
        patterns = self.engine._load_market_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) == 0  # Empty in current implementation


if __name__ == "__main__":
    pytest.main([__file__])