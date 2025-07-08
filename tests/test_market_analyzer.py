"""
Unit tests for MarketAnalyzer functionality.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from src.analyzers.market_analyzer import MarketAnalyzer
from src.analyzers.models import AnalysisResult, MarketOpportunity, OpportunityScore
from src.clients.polymarket.models import Market, MarketPrice, Token
from src.clients.news.models import NewsArticle, NewsSource


class TestMarketAnalyzer:
    """Test cases for MarketAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = MarketAnalyzer()
        
        # Create test market data
        self.test_market = Market(
            condition_id="test_market_123",
            question="Will Bitcoin reach $100,000 by end of 2024?",
            description="Bitcoin price prediction market",
            category="Cryptocurrency",
            active=True,
            closed=False,
            volume=25000.0,
            end_date_iso=datetime.now() + timedelta(days=60),
            tokens=[
                Token(token_id="yes_token", outcome="Yes", price=0.3),
                Token(token_id="no_token", outcome="No", price=0.7)
            ],
            minimum_order_size=1.0
        )
        
        self.test_price = MarketPrice(
            condition_id="test_market_123",
            yes_price=0.3,
            no_price=0.7,
            spread=0.4
        )
        
        self.test_news = [
            NewsArticle(
                source=NewsSource(name="Reuters"),
                title="Bitcoin surges to new monthly high",
                description="Cryptocurrency markets show strong momentum",
                url="https://example.com/bitcoin-surge",
                published_at=datetime.now() - timedelta(hours=2),
                content="Bitcoin has reached..."
            ),
            NewsArticle(
                source=NewsSource(name="Bloomberg"),
                title="Crypto analysts predict Bitcoin could hit $100k",
                description="Multiple analysts forecast major price targets",
                url="https://example.com/bitcoin-prediction",
                published_at=datetime.now() - timedelta(hours=5),
                content="Analysts are predicting..."
            )
        ]
        
    @pytest.mark.asyncio
    async def test_analyze_markets_success(self):
        """Test successful market analysis."""
        # Mock fair value engine
        self.analyzer.fair_value_engine.calculate_fair_value = AsyncMock(
            return_value=(0.6, 0.4, "Strong bullish indicators based on news")
        )
        
        # Analyze markets
        result = await self.analyzer.analyze_markets(
            markets=[self.test_market],
            market_prices=[self.test_price],
            news_articles=self.test_news
        )
        
        # Verify result structure
        assert isinstance(result, AnalysisResult)
        assert result.total_markets_analyzed == 1
        assert result.news_articles_processed == 2
        assert len(result.opportunities) == 1
        
        # Verify opportunity details
        opportunity = result.opportunities[0]
        assert isinstance(opportunity, MarketOpportunity)
        assert opportunity.condition_id == "test_market_123"
        assert opportunity.fair_yes_price == 0.6
        assert opportunity.fair_no_price == 0.4
        assert opportunity.recommended_position == "YES"
        assert opportunity.expected_return == 100.0  # (0.6 - 0.3) / 0.3 * 100
        
    @pytest.mark.asyncio
    async def test_analyze_markets_filters_low_volume(self):
        """Test that low volume markets are filtered out."""
        # Create low volume market
        low_volume_market = Market(
            condition_id="low_volume",
            question="Test question?",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=100.0,  # Below min_volume threshold
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[
                Token(token_id="yes", outcome="Yes", price=0.5),
                Token(token_id="no", outcome="No", price=0.5)
            ],
            minimum_order_size=1.0
        )
        
        result = await self.analyzer.analyze_markets(
            markets=[low_volume_market],
            market_prices=[MarketPrice(
                condition_id="low_volume",
                yes_price=0.5,
                no_price=0.5,
                spread=0.0
            )],
            news_articles=[]
        )
        
        assert result.total_markets_analyzed == 1
        assert len(result.opportunities) == 0  # Filtered out
        
    @pytest.mark.asyncio
    async def test_analyze_markets_filters_small_opportunities(self):
        """Test that small opportunities are filtered out."""
        # Mock fair value with small difference
        self.analyzer.fair_value_engine.calculate_fair_value = AsyncMock(
            return_value=(0.32, 0.68, "Minor price difference")
        )
        
        result = await self.analyzer.analyze_markets(
            markets=[self.test_market],
            market_prices=[self.test_price],
            news_articles=[]
        )
        
        assert len(result.opportunities) == 0  # Too small opportunity
        
    @pytest.mark.asyncio
    async def test_analyze_markets_handles_errors(self):
        """Test error handling during market analysis."""
        # Mock fair value engine to raise error
        self.analyzer.fair_value_engine.calculate_fair_value = AsyncMock(
            side_effect=Exception("API error")
        )
        
        result = await self.analyzer.analyze_markets(
            markets=[self.test_market],
            market_prices=[self.test_price],
            news_articles=[]
        )
        
        # Should handle error gracefully
        assert result.total_markets_analyzed == 1
        assert len(result.opportunities) == 0
        
    @pytest.mark.asyncio
    async def test_analyze_single_market_no_position(self):
        """Test market with no recommended position."""
        # Mock fair value showing both overvalued
        self.analyzer.fair_value_engine.calculate_fair_value = AsyncMock(
            return_value=(0.2, 0.6, "Both positions overvalued")
        )
        
        opportunity = await self.analyzer._analyze_single_market(
            self.test_market,
            self.test_price,
            []
        )
        
        assert opportunity is None  # No profitable position
        
    @pytest.mark.asyncio
    async def test_calculate_opportunity_score(self):
        """Test opportunity score calculation."""
        score = self.analyzer._calculate_opportunity_score(
            self.test_market,
            self.test_price,
            fair_yes_price=0.6,
            fair_no_price=0.4,
            news_articles=self.test_news
        )
        
        assert isinstance(score, OpportunityScore)
        assert 0 <= score.value_score <= 1
        assert 0 <= score.confidence_score <= 1
        assert 0 <= score.volume_score <= 1
        assert 0 <= score.time_score <= 1
        assert 0 <= score.news_relevance_score <= 1
        
    def test_analyze_news_sentiment(self):
        """Test news sentiment analysis."""
        # Positive sentiment news
        positive_news = [
            NewsArticle(
                source=NewsSource(name="Reuters"),
                title="Market shows strong growth and success",
                description="Positive trends continue",
                url="https://example.com/positive",
                published_at=datetime.now()
            )
        ]
        
        sentiment = self.analyzer._analyze_news_sentiment(positive_news)
        assert sentiment > 0  # Positive sentiment
        
        # Negative sentiment news
        negative_news = [
            NewsArticle(
                source=NewsSource(name="Reuters"),
                title="Market faces decline and losses",
                description="Negative trends persist",
                url="https://example.com/negative",
                published_at=datetime.now()
            )
        ]
        
        sentiment = self.analyzer._analyze_news_sentiment(negative_news)
        assert sentiment < 0  # Negative sentiment
        
        # No news
        sentiment = self.analyzer._analyze_news_sentiment([])
        assert sentiment == 0.0
        
    def test_calculate_time_factor(self):
        """Test time factor calculation."""
        # Very close to resolution
        market = Market(
            condition_id="test",
            question="Test?",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=3),
            tokens=[],
            minimum_order_size=1.0
        )
        assert self.analyzer._calculate_time_factor(market) == 1.0
        
        # Moderate time horizon
        market.end_date_iso = datetime.now() + timedelta(days=45)
        assert 0.5 < self.analyzer._calculate_time_factor(market) < 0.8
        
        # Long-term
        market.end_date_iso = datetime.now() + timedelta(days=180)
        assert self.analyzer._calculate_time_factor(market) < 0.5
        
        # No end date
        market.end_date_iso = None
        assert self.analyzer._calculate_time_factor(market) == 0.5
        
    def test_get_base_probability(self):
        """Test base probability estimation."""
        # ETF approval
        market = Market(
            condition_id="test",
            question="Will Bitcoin ETF be approved?",
            description="Test",
            category="Crypto",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[],
            minimum_order_size=1.0
        )
        prob = self.analyzer._get_base_probability(market)
        assert 0.3 < prob < 0.5  # Bitcoin ETF moderate probability
        
        # Political question
        market.question = "Will Trump win the election?"
        prob = self.analyzer._get_base_probability(market)
        assert 0.4 < prob < 0.5  # Political events competitive
        
        # Multi-party election
        market.question = "Will LDP win the most seats?"
        prob = self.analyzer._get_base_probability(market)
        assert 0.3 < prob < 0.4  # Major party higher chance
        
    def test_extract_market_keywords(self):
        """Test keyword extraction from market questions."""
        keywords = self.analyzer._extract_market_keywords(self.test_market)
        
        assert "bitcoin" in keywords
        assert "reach" in keywords
        assert "$100,000" in keywords or "100,000" in keywords
        assert "2024" in keywords
        assert "will" not in keywords  # Stop word filtered
        
    def test_find_related_news(self):
        """Test finding related news articles."""
        related = self.analyzer._find_related_news(
            self.test_market,
            self.test_news
        )
        
        assert len(related) == 2  # Both articles mention Bitcoin
        
        # Test with unrelated news
        unrelated_news = [
            NewsArticle(
                source=NewsSource(name="ESPN"),
                title="Basketball team wins championship",
                description="Sports update",
                url="https://example.com/sports",
                published_at=datetime.now()
            )
        ]
        
        related = self.analyzer._find_related_news(
            self.test_market,
            unrelated_news
        )
        
        assert len(related) == 0  # No related articles
        
    def test_generate_reasoning(self):
        """Test reasoning generation."""
        reasoning = self.analyzer._generate_reasoning(
            self.test_market,
            self.test_price,
            fair_yes_price=0.6,
            fair_no_price=0.4,
            related_news=self.test_news,
            fair_value_reasoning="Strong bullish indicators"
        )
        
        assert isinstance(reasoning, str)
        assert "Fair Value Analysis" in reasoning
        assert "undervalued" in reasoning
        assert "news" in reasoning.lower()
        assert "liquidity" in reasoning.lower()
        assert "days" in reasoning.lower()
        
    @pytest.mark.asyncio
    async def test_kelly_criterion_integration(self):
        """Test Kelly Criterion calculation integration."""
        # Mock fair value engine
        self.analyzer.fair_value_engine.calculate_fair_value = AsyncMock(
            return_value=(0.6, 0.4, "Test reasoning")
        )
        
        # Mock Kelly Criterion
        self.analyzer.kelly_criterion.calculate = MagicMock(
            return_value=MagicMock(kelly_fraction=0.15, recommended_bet_size=150.0)
        )
        
        opportunity = await self.analyzer._analyze_single_market(
            self.test_market,
            self.test_price,
            []
        )
        
        assert opportunity is not None
        assert opportunity.kelly_analysis is not None
        self.analyzer.kelly_criterion.calculate.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_backtesting_integration(self):
        """Test backtesting engine integration."""
        # Mock fair value engine
        self.analyzer.fair_value_engine.calculate_fair_value = AsyncMock(
            return_value=(0.6, 0.4, "Test reasoning")
        )
        
        # Mock backtesting engine
        self.analyzer.backtesting_engine.record_prediction = MagicMock()
        
        opportunity = await self.analyzer._analyze_single_market(
            self.test_market,
            self.test_price,
            []
        )
        
        assert opportunity is not None
        self.analyzer.backtesting_engine.record_prediction.assert_called_once()
        
    def test_get_category_adjustment(self):
        """Test category-specific adjustments."""
        # Crypto category
        self.test_market.category = "Cryptocurrency"
        adjustment = self.analyzer._get_category_adjustment(self.test_market)
        assert adjustment > 0  # Bullish on crypto
        
        # Politics category
        self.test_market.category = "Politics"
        adjustment = self.analyzer._get_category_adjustment(self.test_market)
        assert adjustment == 0  # Neutral
        
        # Unknown category
        self.test_market.category = "Unknown"
        adjustment = self.analyzer._get_category_adjustment(self.test_market)
        assert adjustment == 0  # Default neutral


if __name__ == "__main__":
    pytest.main([__file__, "-v"])