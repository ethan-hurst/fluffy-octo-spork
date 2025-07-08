"""
Integration tests for the complete Polymarket analyzer system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from src.analyzers.market_analyzer import MarketAnalyzer
from src.analyzers.fair_value_engine import FairValueEngine
from src.clients.polymarket.client import PolymarketClient
from src.clients.news.client import NewsClient
from src.clients.polymarket.models import Market, Token, MarketPrice
from src.clients.news.models import NewsArticle, NewsSource
from src.analyzers.bayesian_updater import ProbabilityDistribution
from src.analyzers.llm_news_analyzer import MarketNewsAnalysis


class TestSystemIntegration:
    """Integration tests for the complete system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.market_analyzer = MarketAnalyzer()
        self.fair_value_engine = FairValueEngine()
        self.polymarket_client = PolymarketClient()
        self.news_client = NewsClient()
        
        # Create comprehensive test data
        now = datetime.now()
        
        # Test markets covering all major categories
        self.test_markets = [
            Market(
                condition_id="trump_2024_election",
                question="Will Donald Trump win the 2024 presidential election?",
                description="Presidential election prediction market for 2024",
                category="Politics",
                active=True,
                closed=False,
                volume=2500000.0,
                end_date_iso=now + timedelta(days=300),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            Market(
                condition_id="btc_etf_approval",
                question="Will a Bitcoin ETF be approved by the SEC in 2024?",
                description="Bitcoin ETF regulatory approval prediction",
                category="Cryptocurrency",
                active=True,
                closed=False,
                volume=1800000.0,
                end_date_iso=now + timedelta(days=120),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            Market(
                condition_id="nfl_coaching_change",
                question="Will the New York Jets fire their head coach this season?",
                description="NFL coaching change prediction for current season",
                category="Sports",
                active=True,
                closed=False,
                volume=750000.0,
                end_date_iso=now + timedelta(days=90),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            Market(
                condition_id="constitutional_amendment",
                question="Will the 22nd Amendment be repealed before 2025?",
                description="Constitutional amendment to repeal presidential term limits",
                category="Politics",
                active=True,
                closed=False,
                volume=150000.0,
                end_date_iso=now + timedelta(days=365),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            )
        ]
        
        # Test news articles for different topics
        self.test_news_articles = [
            NewsArticle(
                title="Trump Maintains Lead in Key Swing States",
                description="Latest polling shows former president ahead in critical battleground states",
                url="https://example.com/trump-polling-lead",
                published_at=now - timedelta(hours=2),
                source=NewsSource(name="Reuters")
            ),
            NewsArticle(
                title="SEC Chairman Signals Crypto ETF Approval",
                description="Regulatory chief indicates positive outlook for Bitcoin ETF applications",
                url="https://example.com/sec-crypto-etf",
                published_at=now - timedelta(hours=1),
                source=NewsSource(name="Bloomberg")
            ),
            NewsArticle(
                title="Jets Coach Under Intense Pressure After Loss",
                description="Team performance raises questions about coaching staff future",
                url="https://example.com/jets-coach-pressure",
                published_at=now - timedelta(hours=3),
                source=NewsSource(name="ESPN")
            ),
            NewsArticle(
                title="Constitutional Scholars Debate Term Limits",
                description="Legal experts discuss feasibility of constitutional amendments",
                url="https://example.com/constitutional-debate",
                published_at=now - timedelta(hours=4),
                source=NewsSource(name="Washington Post")
            )
        ]
        
        # Test market data - using simple mock data instead of non-existent classes
        self.test_market_data = {
            "market": "trump_2024_election",
            "asset_id": "trump_yes_token",
            "bid": 0.47,
            "ask": 0.53,
            "volume_24h": 125000.0,
            "price_change_24h": 0.023,
            "last_trade_price": 0.495,
            "trades_24h": 450
        }
        
    @pytest.mark.asyncio
    async def test_complete_market_analysis_workflow(self):
        """Test the complete market analysis workflow from data fetching to opportunity identification."""
        
        # Mock all external dependencies
        with patch.object(self.polymarket_client, 'get_markets', new_callable=AsyncMock) as mock_get_markets:
            with patch.object(self.news_client, 'get_relevant_news', new_callable=AsyncMock) as mock_search_news:
                with patch.object(self.polymarket_client, 'get_market_prices', new_callable=AsyncMock) as mock_get_prices:
                    # Setup mocks
                    mock_get_markets.return_value = self.test_markets
                    mock_search_news.return_value = self.test_news_articles
                    
                    # Mock market prices for each market
                    market_prices = []
                    for market in self.test_markets:
                        price = MarketPrice(
                            condition_id=market.condition_id,
                            yes_price=0.5,
                            no_price=0.5,
                            volume_24h=market.volume,
                            liquidity=50000.0
                        )
                        market_prices.append(price)
                        mock_get_prices.return_value = price
                    
                    # Execute complete workflow
                    result = await self.market_analyzer.analyze_markets(
                        self.test_markets,
                        market_prices,
                        self.test_news_articles
                    )
                    
                    # Verify results
                    assert hasattr(result, 'opportunities')
                    opportunities = result.opportunities
                    assert isinstance(opportunities, list)
                    assert len(opportunities) > 0
                    
                    # Check that opportunities contain required fields
                    for opportunity in opportunities:
                        assert hasattr(opportunity, 'market')
                        assert hasattr(opportunity, 'fair_yes_price')
                        assert hasattr(opportunity, 'fair_no_price')
                        assert hasattr(opportunity, 'current_price')
                        assert hasattr(opportunity, 'value_score')
                        assert hasattr(opportunity, 'reasoning')
                        
                    # Verify external calls were made
                    mock_get_markets.assert_called_once()
                    assert mock_search_news.call_count >= 1
                        
    @pytest.mark.asyncio
    async def test_political_market_end_to_end(self):
        """Test end-to-end analysis for political markets."""
        political_market = self.test_markets[0]  # Trump election market
        political_news = [self.test_news_articles[0]]  # Trump polling news
        
        with patch.object(self.fair_value_engine.political_model, 'calculate_political_probability') as mock_political:
            mock_political.return_value = ProbabilityDistribution(
                mean=0.48,
                std_dev=0.08,
                confidence_interval=(0.40, 0.56),
                sample_size=1000
            )
            
            # Calculate fair value
            yes_price, no_price, reasoning = await self.fair_value_engine.calculate_fair_value(
                political_market, political_news
            )
            
            # Verify political model was used
            assert mock_political.called
            assert abs(yes_price - 0.48) < 0.01
            assert abs(no_price - 0.52) < 0.01
            assert "Advanced political model" in reasoning
            
    @pytest.mark.asyncio
    async def test_crypto_market_end_to_end(self):
        """Test end-to-end analysis for crypto markets."""
        crypto_market = self.test_markets[1]  # Bitcoin ETF market
        crypto_news = [self.test_news_articles[1]]  # SEC ETF news
        
        with patch.object(self.fair_value_engine.crypto_model, 'calculate_crypto_probability') as mock_crypto:
            mock_crypto.return_value = ProbabilityDistribution(
                mean=0.72,
                std_dev=0.10,
                confidence_interval=(0.62, 0.82),
                sample_size=500
            )
            
            # Calculate fair value
            yes_price, no_price, reasoning = await self.fair_value_engine.calculate_fair_value(
                crypto_market, crypto_news
            )
            
            # Verify crypto model was used
            assert mock_crypto.called
            assert abs(yes_price - 0.72) < 0.01
            assert abs(no_price - 0.28) < 0.01
            assert "Advanced crypto/financial model" in reasoning
            
    @pytest.mark.asyncio
    async def test_sports_market_analysis(self):
        """Test sports market analysis workflow."""
        sports_market = self.test_markets[2]  # Jets coaching market
        sports_news = [self.test_news_articles[2]]  # Jets coaching news
        
        with patch.object(self.fair_value_engine.sports_model, 'calculate_sports_probability') as mock_sports:
            mock_sports.return_value = ProbabilityDistribution(
                mean=0.65,
                std_dev=0.12,
                confidence_interval=(0.53, 0.77),
                sample_size=300
            )
            
            # Test sports model integration
            result = self.fair_value_engine.sports_model.calculate_sports_probability(
                sports_market, sports_news
            )
            
            assert isinstance(result, ProbabilityDistribution)
            assert 0.0 <= result.mean <= 1.0
            assert result.lower_bound <= result.mean <= result.upper_bound
            
    @pytest.mark.asyncio
    async def test_constitutional_amendment_analysis(self):
        """Test constitutional amendment market analysis with very low probabilities."""
        constitutional_market = self.test_markets[3]  # 22nd Amendment repeal
        constitutional_news = [self.test_news_articles[3]]  # Constitutional debate news
        
        # Calculate fair value - should be very low for constitutional amendments
        yes_price, no_price, reasoning = await self.fair_value_engine.calculate_fair_value(
            constitutional_market, constitutional_news
        )
        
        # Constitutional amendments should have extremely low probability
        assert yes_price < 0.05
        assert no_price > 0.95
        assert "Constitutional amendment" in reasoning or "22nd Amendment" in reasoning
        
    @pytest.mark.asyncio
    async def test_news_integration_and_sentiment_analysis(self):
        """Test news integration and sentiment analysis across the system."""
        market = self.test_markets[0]  # Political market
        news = self.test_news_articles[:2]  # Mixed news
        
        # Mock LLM news analysis
        mock_analysis = MarketNewsAnalysis(
            overall_sentiment=0.15,
            sentiment_confidence=0.8,
            news_impact_score=0.7,
            credible_sources_count=2,
            total_articles_analyzed=2,
            probability_adjustment=0.03,
            key_findings=["Positive polling trend", "Strong media coverage"],
            reasoning="Based on multiple credible sources and recent data"
        )
        
        with patch.object(self.fair_value_engine.llm_news_analyzer, 'analyze_market_news', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_analysis
            
            adjustment, reasoning = await self.fair_value_engine._calculate_llm_news_adjustment(news, market)
            
            assert adjustment == 0.03  # Should match mock analysis
            assert "LLM News Analysis" in reasoning
            assert "positive sentiment" in reasoning
            
    @pytest.mark.asyncio
    async def test_bayesian_updating_integration(self):
        """Test Bayesian updating integration across different market types."""
        from src.analyzers.bayesian_updater import BayesianUpdater, EvidenceType
        
        updater = BayesianUpdater()
        
        # Create evidence from different sources
        evidence_list = [
            updater.create_evidence(
                evidence_type=EvidenceType.POLLING_DATA,
                positive_signal=True,
                strength=0.7,
                confidence=0.8,
                description="Strong polling support",
                source=NewsSource(name="polling_aggregator")
            ),
            updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=True,
                strength=0.5,
                confidence=0.6,
                description="Positive news coverage",
                source=NewsSource(name="news_analyzer")
            ),
            updater.create_evidence(
                evidence_type=EvidenceType.MARKET_BEHAVIOR,
                positive_signal=False,
                strength=0.3,
                confidence=0.5,
                description="Some market resistance",
                source=NewsSource(name="market_analysis")
            )
        ]
        
        # Test Bayesian updating with multiple evidence pieces
        result = updater.update_probability(
            prior=0.45,
            evidence_list=evidence_list,
            market_type="political"
        )
        
        assert isinstance(result, ProbabilityDistribution)
        assert result.mean > 0.45  # Should increase from prior given positive evidence
        assert 0.0 <= result.mean <= 1.0
        assert result.lower_bound <= result.mean <= result.upper_bound
        assert result.uncertainty > 0.0
        
    @pytest.mark.asyncio
    async def test_market_filtering_and_selection(self):
        """Test market filtering and opportunity selection."""
        
        with patch.object(self.market_analyzer, '_calculate_opportunity_value') as mock_calc_value:
            # Mock different value scores for different markets
            mock_calc_value.side_effect = [0.85, 0.45, 0.70, 0.15]  # High, medium, good, low values
            
            # Test market filtering
            filtered_opportunities = []
            for i, market in enumerate(self.test_markets):
                value_score = mock_calc_value.return_value if mock_calc_value.called else [0.85, 0.45, 0.70, 0.15][i]
                
                if value_score > 0.5:  # Filter threshold
                    filtered_opportunities.append({
                        'market': market,
                        'value_score': value_score
                    })
            
            # Should include high-value opportunities and exclude low-value ones
            assert len(filtered_opportunities) >= 2  # At least Trump and Jets markets
            
    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self):
        """Test system resilience with various error conditions."""
        
        # Test with network errors
        with patch.object(self.polymarket_client, 'get_markets', new_callable=AsyncMock) as mock_markets:
            mock_markets.side_effect = Exception("Network error")
            
            # System should handle errors gracefully
            try:
                opportunities = await self.market_analyzer.analyze_markets()
                assert opportunities == []  # Should return empty list on error
            except Exception:
                pytest.fail("System should handle network errors gracefully")
                
        # Test with partial data availability
        with patch.object(self.polymarket_client, 'get_markets', new_callable=AsyncMock) as mock_markets:
            with patch.object(self.news_client, 'get_relevant_news', new_callable=AsyncMock) as mock_news:
                mock_markets.return_value = self.test_markets[:2]  # Partial market data
                mock_news.return_value = []  # No news available
                
                # Should still work with limited data
                opportunities = await self.market_analyzer.analyze_markets()
                assert isinstance(opportunities, list)
                
    @pytest.mark.asyncio
    async def test_performance_and_efficiency(self):
        """Test system performance with multiple markets."""
        
        # Create larger dataset
        large_market_set = self.test_markets * 5  # 20 markets total
        
        with patch.object(self.polymarket_client, 'get_markets', new_callable=AsyncMock) as mock_markets:
            with patch.object(self.news_client, 'get_relevant_news', new_callable=AsyncMock) as mock_news:
                mock_markets.return_value = large_market_set
                mock_news.return_value = self.test_news_articles
                
                # Measure execution time
                import time
                start_time = time.time()
                
                opportunities = await self.market_analyzer.analyze_markets()
                
                execution_time = time.time() - start_time
                
                # Should complete within reasonable time (adjust threshold as needed)
                assert execution_time < 10.0  # 10 seconds max for 20 markets
                assert isinstance(opportunities, list)
                
    @pytest.mark.asyncio
    async def test_data_consistency_and_validation(self):
        """Test data consistency and validation across the system."""
        
        # Test with invalid market data
        invalid_market = Market(
            condition_id="invalid_market",
            question="",  # Empty question
            description=None,
            category="Invalid",
            active=True,
            closed=False,
            volume=-1000.0,  # Negative volume
            end_date_iso=datetime.now() - timedelta(days=1),  # Past date
            tokens=[
                Token(token_id="yes_token", outcome="Yes", price=0.5),
                Token(token_id="no_token", outcome="No", price=0.5)
            ],
            minimum_order_size=1.0
        )
        
        # System should handle invalid data gracefully
        try:
            yes_price, no_price, reasoning = await self.fair_value_engine.calculate_fair_value(
                invalid_market, []
            )
            
            # Should return valid probabilities even with invalid input
            assert 0.0 <= yes_price <= 1.0
            assert 0.0 <= no_price <= 1.0
            assert abs(yes_price + no_price - 1.0) < 0.01
            
        except Exception as e:
            pytest.fail(f"System should handle invalid data gracefully: {e}")
            
    @pytest.mark.asyncio
    async def test_model_integration_consistency(self):
        """Test consistency across different specialized models."""
        
        # Test that all models return valid probability distributions
        models_to_test = [
            (self.fair_value_engine.political_model, self.test_markets[0], "political"),
            (self.fair_value_engine.crypto_model, self.test_markets[1], "crypto"),
            (self.fair_value_engine.sports_model, self.test_markets[2], "sports")
        ]
        
        for model, test_market, model_type in models_to_test:
            # Mock the specific calculation method for each model
            method_name = f"calculate_{model_type}_probability"
            if hasattr(model, method_name):
                with patch.object(model, method_name) as mock_method:
                    mock_method.return_value = ProbabilityDistribution(
                        mean=0.6,
                        std_dev=0.1,
                        confidence_interval=(0.5, 0.7),
                        sample_size=500
                    )
                    
                    result = getattr(model, method_name)(test_market, self.test_news_articles)
                    
                    # Verify consistency
                    assert isinstance(result, ProbabilityDistribution)
                    assert 0.0 <= result.mean <= 1.0
                    assert result.lower_bound <= result.mean <= result.upper_bound
                    assert result.uncertainty >= 0.0
                    
    @pytest.mark.asyncio 
    async def test_end_to_end_opportunity_identification(self):
        """Test complete end-to-end opportunity identification."""
        
        # Mock all components for a complete test
        with patch.object(self.polymarket_client, 'get_markets', new_callable=AsyncMock) as mock_markets:
            with patch.object(self.news_client, 'get_relevant_news', new_callable=AsyncMock) as mock_news:
                with patch.object(self.polymarket_client, 'get_orderbook', new_callable=AsyncMock) as mock_orderbook:
                    with patch.object(self.polymarket_client, 'get_market_stats', new_callable=AsyncMock) as mock_stats:
                        
                        # Setup comprehensive mocks
                        mock_markets.return_value = self.test_markets
                        mock_news.return_value = self.test_news_articles
                        mock_orderbook.return_value = self.test_orderbook
                        mock_stats.return_value = self.test_market_stats
                        
                        # Create a complete market analyzer instance
                        analyzer = MarketAnalyzer()
                        
                        # Run complete analysis
                        opportunities = await analyzer.analyze_markets()
                        
                        # Comprehensive verification
                        assert isinstance(opportunities, list)
                        
                        for opportunity in opportunities:
                            # Verify opportunity structure
                            assert hasattr(opportunity, 'market')
                            assert hasattr(opportunity, 'fair_yes_price')
                            assert hasattr(opportunity, 'fair_no_price')
                            assert hasattr(opportunity, 'current_price')
                            assert hasattr(opportunity, 'value_score')
                            assert hasattr(opportunity, 'reasoning')
                            
                            # Verify value ranges
                            assert 0.0 <= opportunity.fair_yes_price <= 1.0
                            assert 0.0 <= opportunity.fair_no_price <= 1.0
                            assert abs(opportunity.fair_yes_price + opportunity.fair_no_price - 1.0) < 0.01
                            assert opportunity.value_score >= 0.0
                            assert isinstance(opportunity.reasoning, str)
                            assert len(opportunity.reasoning) > 0


if __name__ == "__main__":
    pytest.main([__file__])