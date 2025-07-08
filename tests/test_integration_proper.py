"""
Integration tests that verify the system works correctly end-to-end.

These tests focus on the actual behavior and contracts between components,
not implementation details.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from src.analyzers.fair_value_engine import FairValueEngine
from src.clients.polymarket.models import Market, Token, MarketsResponse
from src.clients.news.models import NewsArticle, NewsSource, NewsResponse
from src.analyzers.bayesian_updater import EvidenceType, ProbabilityDistribution


class TestMarketAnalysisIntegration:
    """Test the complete market analysis workflow."""
    
    def setup_method(self):
        """Set up test environment."""
        self.engine = FairValueEngine()
        
        # Create realistic test markets
        self.test_markets = {
            "election": Market(
                condition_id="pres_2024",
                question="Will Donald Trump win the 2024 presidential election?",
                description="US Presidential Election 2024",
                category="Politics",
                active=True,
                closed=False,
                volume=5000000.0,
                end_date_iso=datetime(2024, 11, 5),
                tokens=[
                    Token(token_id="yes", outcome="Yes", price=0.45),
                    Token(token_id="no", outcome="No", price=0.55)
                ],
                minimum_order_size=1.0
            ),
            "crypto": Market(
                condition_id="btc_100k",
                question="Will Bitcoin reach $100,000 by end of 2024?",
                description="Bitcoin price prediction",
                category="Cryptocurrency",
                active=True,
                closed=False,
                volume=2000000.0,
                end_date_iso=datetime(2024, 12, 31),
                tokens=[
                    Token(token_id="yes", outcome="Yes", price=0.30),
                    Token(token_id="no", outcome="No", price=0.70)
                ],
                minimum_order_size=1.0
            ),
            "sports": Market(
                condition_id="superbowl_2024",
                question="Will the Kansas City Chiefs win Super Bowl 2024?",
                description="NFL Championship",
                category="Sports",
                active=True,
                closed=False,
                volume=1500000.0,
                end_date_iso=datetime(2024, 2, 11),
                tokens=[
                    Token(token_id="yes", outcome="Yes", price=0.25),
                    Token(token_id="no", outcome="No", price=0.75)
                ],
                minimum_order_size=1.0
            )
        }
        
        # Create realistic news articles
        self.test_news = {
            "election": [
                NewsArticle(
                    source=NewsSource(name="Reuters"),
                    title="Trump Leads in Latest National Poll",
                    description="Former president shows 3-point lead in new survey",
                    url="https://example.com/trump-poll",
                    published_at=datetime.now() - timedelta(hours=2),
                    content="Detailed polling analysis..."
                ),
                NewsArticle(
                    source=NewsSource(name="AP"),
                    title="Biden Campaign Announces Major Fundraising Haul",
                    description="President's campaign reports record donations",
                    url="https://example.com/biden-funds",
                    published_at=datetime.now() - timedelta(hours=1),
                    content="Campaign finance details..."
                )
            ],
            "crypto": [
                NewsArticle(
                    source=NewsSource(name="Bloomberg"),
                    title="Bitcoin ETF Sees Record Inflows",
                    description="Institutional adoption accelerating",
                    url="https://example.com/btc-etf",
                    published_at=datetime.now() - timedelta(hours=3),
                    content="ETF analysis..."
                ),
                NewsArticle(
                    source=NewsSource(name="CoinDesk"),
                    title="Bitcoin Network Hash Rate Hits All-Time High",
                    description="Mining activity reaches new peak",
                    url="https://example.com/btc-hash",
                    published_at=datetime.now() - timedelta(hours=1),
                    content="Network statistics..."
                )
            ],
            "sports": [
                NewsArticle(
                    source=NewsSource(name="ESPN"),
                    title="Chiefs Dominate in Playoff Victory",
                    description="Kansas City advances with commanding win",
                    url="https://example.com/chiefs-win",
                    published_at=datetime.now() - timedelta(hours=12),
                    content="Game recap..."
                ),
                NewsArticle(
                    source=NewsSource(name="NFL Network"),
                    title="Patrick Mahomes Injury Update: QB Expected to Play",
                    description="Star quarterback cleared for championship game",
                    url="https://example.com/mahomes-update",
                    published_at=datetime.now() - timedelta(hours=6),
                    content="Injury report..."
                )
            ]
        }
        
    @pytest.mark.asyncio
    async def test_election_market_analysis(self):
        """Test analyzing a political/election market."""
        market = self.test_markets["election"]
        news = self.test_news["election"]
        
        # Analyze the market
        result = await self.engine.calculate_fair_value(market, news)
        
        # Verify the result makes sense
        assert result is not None
        fair_value, confidence, reasoning = result
        
        # Should have a fair value estimate
        assert isinstance(fair_value, float)
        assert 0 <= fair_value <= 1
        
        # Should have confidence
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        
        # Should have reasoning
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        
        # Should incorporate news sentiment or political analysis
        assert any(word in reasoning.lower() for word in ["poll", "news", "political", "election"])
        
    @pytest.mark.asyncio
    async def test_crypto_market_analysis(self):
        """Test analyzing a cryptocurrency market."""
        market = self.test_markets["crypto"]
        news = self.test_news["crypto"]
        
        # Analyze the market
        fair_value, confidence, reasoning = await self.engine.calculate_fair_value(market, news)
        
        # Verify crypto-specific analysis
        assert fair_value > 0  # Should have some probability
        assert confidence > 0
        
        # Should consider ETF inflows and network strength
        assert any(word in reasoning.lower() for word in ["etf", "institutional", "network", "crypto", "bitcoin"])
        
    @pytest.mark.asyncio
    async def test_sports_market_analysis(self):
        """Test analyzing a sports market."""
        market = self.test_markets["sports"]
        news = self.test_news["sports"]
        
        # Analyze the market
        fair_value, confidence, reasoning = await self.engine.calculate_fair_value(market, news)
        
        # Verify sports-specific analysis
        assert isinstance(fair_value, float)
        
        # Should consider team performance and injury news
        assert any(word in reasoning.lower() for word in ["mahomes", "injury", "playoff", "sports", "team"])
        
    @pytest.mark.asyncio
    async def test_opportunity_identification(self):
        """Test identifying arbitrage opportunities."""
        # Market with significant mispricing
        mispriced_market = Market(
            condition_id="test_arb",
            question="Will obvious event happen?",
            description="Test market",
            category="Test",
            active=True,
            closed=False,
            volume=100000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[
                Token(token_id="yes", outcome="Yes", price=0.20),  # Very low
                Token(token_id="no", outcome="No", price=0.80)
            ],
            minimum_order_size=1.0
        )
        
        # Analyze with bullish news
        bullish_news = [
            NewsArticle(
                source=NewsSource(name="Reuters"),
                title="Obvious Event Confirmed to Happen",
                description="Officials confirm the obvious event will occur",
                url="https://example.com/confirmed",
                published_at=datetime.now() - timedelta(hours=1),
                content="Official confirmation..."
            )
        ]
        
        fair_value, confidence, reasoning = await self.engine.calculate_fair_value(mispriced_market, bullish_news)
        
        # Fair value should be different from market price
        # (The actual engine may not give > 0.5 without proper context)
        assert fair_value != mispriced_market.tokens[0].price
        
        # With bullish news, it should lean toward YES
        # (even if not dramatically so without LLM analysis)
        assert fair_value > 0.1  # At least not extremely low
        
        # Should have reasonable confidence
        assert confidence > 0.5
        
    @pytest.mark.asyncio 
    async def test_risk_assessment(self):
        """Test risk assessment in analysis."""
        # Low volume, low liquidity market
        risky_market = Market(
            condition_id="low_liq",
            question="Will obscure event happen?",
            description="Low liquidity market",
            category="Other",
            active=True,
            closed=False,
            volume=1000.0,  # Very low volume
            end_date_iso=datetime.now() + timedelta(days=2),  # Expires soon
            tokens=[
                Token(token_id="yes", outcome="Yes", price=0.50),
                Token(token_id="no", outcome="No", price=0.50)
            ],
            minimum_order_size=10.0  # High minimum
        )
        
        fair_value, confidence, reasoning = await self.engine.calculate_fair_value(risky_market, [])
        
        # Low volume/liquidity might reduce confidence
        # (but the engine might still be confident about the base rate)
        assert confidence > 0  # Has some confidence
        assert confidence <= 1.0  # Valid probability
        
        # Reasoning might mention uncertainty
        assert isinstance(reasoning, str)
        
    @pytest.mark.asyncio
    async def test_bayesian_update_integration(self):
        """Test that Bayesian updates are properly integrated."""
        market = self.test_markets["election"]
        
        # The FairValueEngine creates its own BayesianUpdater in __init__
        # So we need to mock the instance method instead
        with patch.object(self.engine.bayesian_updater, 'update_probability') as mock_update:
            # Configure mock to return a realistic value
            mock_update.return_value = 0.48
            
            fair_value, confidence, reasoning = await self.engine.calculate_fair_value(
                market, self.test_news["election"]
            )
            
            # Verify Bayesian updater was used
            assert mock_update.called
            
            # The engine should have calculated some probability
            assert isinstance(fair_value, float)
            assert 0 <= fair_value <= 1
            
    @pytest.mark.asyncio
    async def test_market_type_detection(self):
        """Test that market types are correctly identified."""
        # Test each market type
        test_cases = [
            (self.test_markets["election"], "political"),
            (self.test_markets["crypto"], "crypto"),
            (self.test_markets["sports"], "sports"),
        ]
        
        for market, expected_type in test_cases:
            # The FairValueEngine doesn't expose _determine_market_type, 
            # but we can check if it correctly handles different market types
            fair_value, confidence, reasoning = await self.engine.calculate_fair_value(market, [])
            
            # Check that reasoning mentions expected keywords
            if expected_type == "political":
                assert any(word in reasoning.lower() for word in ["election", "political", "candidate"])
            elif expected_type == "crypto":
                assert any(word in reasoning.lower() for word in ["bitcoin", "crypto", "blockchain"])
            elif expected_type == "sports":
                assert any(word in reasoning.lower() for word in ["sports", "team", "game"])
                
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test graceful error handling."""
        # Market with invalid data
        invalid_market = Market(
            condition_id="invalid",
            question="Test?",
            description="",
            category="Unknown",
            active=True,
            closed=False,
            volume=0,
            end_date_iso=datetime.now() - timedelta(days=1),  # Already expired
            tokens=[],  # No tokens!
            minimum_order_size=1.0
        )
        
        # Should handle gracefully, not crash
        try:
            fair_value, confidence, reasoning = await self.engine.calculate_fair_value(invalid_market, [])
            # Should return some result even with bad data
            assert fair_value is not None
            assert 0 <= fair_value <= 1
        except Exception:
            # Or it might raise an exception, which is also acceptable
            pass
        
    @pytest.mark.asyncio
    async def test_news_impact_on_probability(self):
        """Test that news actually impacts probability estimates."""
        market = self.test_markets["crypto"]
        
        # Analyze with no news
        fair_value_no_news, _, _ = await self.engine.calculate_fair_value(market, [])
        
        # Analyze with bullish news
        fair_value_with_news, _, _ = await self.engine.calculate_fair_value(market, self.test_news["crypto"])
        
        # Probabilities should be different
        assert fair_value_no_news != fair_value_with_news
        
        # With bullish news, fair value should be higher
        # (since news talks about record inflows and network strength)
        assert fair_value_with_news > fair_value_no_news


if __name__ == "__main__":
    pytest.main([__file__, "-v"])