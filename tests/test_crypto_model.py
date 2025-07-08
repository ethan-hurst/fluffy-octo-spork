"""
Unit tests for crypto/financial market model functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.analyzers.crypto_model import (
    CryptoFinancialModel, ETFApprovalStage, ETFApplication, 
    CryptoMarketData, FinancialIndicators
)
from src.clients.polymarket.models import Market, Token
from src.clients.news.models import NewsArticle, NewsSource
from src.analyzers.bayesian_updater import ProbabilityDistribution


class TestCryptoFinancialModel:
    """Test cases for CryptoFinancialModel."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.model = CryptoFinancialModel()
        
        # Create test markets
        now = datetime.now()
        self.markets = {
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
            "eth_etf": Market(
                condition_id="eth_etf_2024",
                question="Will an Ethereum ETF be approved by the SEC?",
                description="Ethereum ETF approval prediction",
                category="Cryptocurrency",
                active=True,
                closed=False,
                volume=300000.0,
                end_date_iso=now + timedelta(days=120),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            "btc_price": Market(
                condition_id="btc_100k",
                question="Will Bitcoin reach $100,000 by end of 2024?",
                description="Bitcoin price prediction",
                category="Cryptocurrency",
                active=True,
                closed=False,
                volume=750000.0,
                end_date_iso=now + timedelta(days=60),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            "crypto_regulation": Market(
                condition_id="crypto_ban_2024",
                question="Will the US ban cryptocurrency trading in 2024?",
                description="Crypto regulation prediction",
                category="Cryptocurrency",
                active=True,
                closed=False,
                volume=200000.0,
                end_date_iso=now + timedelta(days=365),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            )
        }
        
        # Create test ETF applications
        self.etf_applications = [
            ETFApplication(
                asset_name="Bitcoin",
                applicant="BlackRock",
                filing_date=now - timedelta(days=180),
                expected_decision_date=now + timedelta(days=30),
                stage=ETFApprovalStage.FINAL_REVIEW,
                public_comments_count=1250,
                sec_staff_feedback="positive"
            ),
            ETFApplication(
                asset_name="Ethereum", 
                applicant="Fidelity",
                filing_date=now - timedelta(days=90),
                expected_decision_date=now + timedelta(days=60),
                stage=ETFApprovalStage.UNDER_REVIEW,
                public_comments_count=800,
                sec_staff_feedback="neutral"
            )
        ]
        
        # Create test market data
        self.market_data = {
            "BTC": CryptoMarketData(
                symbol="BTC",
                current_price=65000.0,
                market_cap=1280000000000.0,
                volume_24h=28000000000.0,
                price_change_7d=5.2,
                price_change_30d=12.8,
                volatility_30d=0.45,
                all_time_high=69000.0,
                distance_from_ath=0.058
            ),
            "ETH": CryptoMarketData(
                symbol="ETH",
                current_price=3200.0,
                market_cap=385000000000.0,
                volume_24h=15000000000.0,
                price_change_7d=3.8,
                price_change_30d=8.5,
                volatility_30d=0.52,
                all_time_high=4878.0,
                distance_from_ath=0.344
            )
        }
        
        # Create test technical indicators
        self.technical_indicators = FinancialIndicators(
            vix_level=18.5,
            spy_trend="bullish",
            dxy_trend="neutral",
            bond_yield_10y=4.25,
            risk_sentiment="risk_on"
        )
        
        # Create test regulatory sentiment
        self.regulatory_sentiment = dict(
            sec_stance="cautiously_positive",
            cftc_stance="neutral",
            fed_stance="concerned",
            recent_statements_sentiment=0.2,
            regulatory_clarity_score=0.6,
            compliance_trend="improving"
        )
        
        # Create test news articles
        self.news_articles = [
            NewsArticle(
                title="SEC Chairman Signals Openness to Bitcoin ETF",
                description="Regulatory chief indicates willingness to approve crypto products",
                url="https://example.com/sec-btc-etf",
                published_at=now - timedelta(hours=2),
                source=NewsSource(name="Reuters")
            ),
            NewsArticle(
                title="Major Institution Adds Bitcoin to Portfolio",
                description="Large pension fund allocates 5% to cryptocurrency",
                url="https://example.com/institutional-adoption",
                published_at=now - timedelta(hours=1),
                source=NewsSource(name="Bloomberg")
            ),
            NewsArticle(
                title="Crypto Market Volatility Concerns Regulators",
                description="Officials cite price swings as barrier to approval",
                url="https://example.com/volatility-concerns",
                published_at=now - timedelta(hours=3),
                source=NewsSource(name="WSJ")
            )
        ]
        
    def test_identify_crypto_asset_bitcoin(self):
        """Test Bitcoin asset identification."""
        market = self.markets["btc_etf"]
        asset = self.model._identify_crypto_asset(market)
        assert asset == "Bitcoin"
        
    def test_identify_crypto_asset_ethereum(self):
        """Test Ethereum asset identification."""
        market = self.markets["eth_etf"]
        asset = self.model._identify_crypto_asset(market)
        assert asset == "Ethereum"
        
    def test_classify_crypto_event_etf_approval(self):
        """Test ETF approval event classification."""
        market = self.markets["btc_etf"]
        event_type = self.model._classify_crypto_event(market)
        assert event_type == "etf_approval"
        
    def test_classify_crypto_event_price_prediction(self):
        """Test price prediction event classification."""
        market = self.markets["btc_price"]
        event_type = self.model._classify_crypto_event(market)
        assert event_type == "price_prediction"
        
    def test_classify_crypto_event_regulation(self):
        """Test regulation event classification."""
        market = self.markets["crypto_regulation"]
        event_type = self.model._classify_crypto_event(market)
        assert event_type == "regulation"
        
    def test_calculate_etf_approval_probability_final_review(self):
        """Test ETF approval probability in final review stage."""
        application = self.etf_applications[0]  # BlackRock Bitcoin, final review
        
        prob = self.model._calculate_etf_approval_probability(
            application, self.regulatory_sentiment
        )
        
        assert 0.0 <= prob <= 1.0
        assert prob > 0.5  # Should be high in final review with positive feedback
        
    def test_calculate_etf_approval_probability_under_review(self):
        """Test ETF approval probability under review."""
        application = self.etf_applications[1]  # Fidelity Ethereum, under review
        
        prob = self.model._calculate_etf_approval_probability(
            application, self.regulatory_sentiment
        )
        
        assert 0.0 <= prob <= 1.0
        assert prob < 0.8  # Should be lower in earlier stage
        
    def test_calculate_price_probability_bullish(self):
        """Test price probability calculation with bullish indicators."""
        market = self.markets["btc_price"]
        market_data = self.market_data["BTC"]
        
        prob = self.model._calculate_price_probability(
            market, market_data, self.technical_indicators
        )
        
        assert 0.0 <= prob <= 1.0
        # With positive technical indicators, should be reasonable probability
        
    def test_calculate_price_probability_target_extraction(self):
        """Test price target extraction from market question."""
        targets = self.model._extract_price_targets(self.markets["btc_price"].question)
        assert 100000.0 in targets
        
    def test_calculate_regulation_probability_positive_sentiment(self):
        """Test regulation probability with positive sentiment."""
        market = self.markets["crypto_regulation"]
        
        prob = self.model._calculate_regulation_probability(
            market, self.regulatory_sentiment
        )
        
        assert 0.0 <= prob <= 1.0
        # Should be low probability for banning with cautiously positive sentiment
        assert prob < 0.3
        
    def test_analyze_regulatory_news_positive(self):
        """Test regulatory news analysis with positive sentiment."""
        positive_news = [
            NewsArticle(
                title="SEC Approves New Crypto Framework",
                description="Regulatory clarity improves for digital assets",
                url="https://example.com/sec-framework",
                published_at=datetime.now(),
                source="Reuters"
            )
        ]
        
        sentiment = self.model._analyze_regulatory_news(positive_news)
        assert sentiment > 0.0  # Should be positive
        
    def test_analyze_regulatory_news_negative(self):
        """Test regulatory news analysis with negative sentiment."""
        negative_news = [
            NewsArticle(
                title="SEC Rejects Latest Crypto Proposal",
                description="Regulators cite security concerns in denial",
                url="https://example.com/sec-rejection",
                published_at=datetime.now(),
                source="Reuters"
            )
        ]
        
        sentiment = self.model._analyze_regulatory_news(negative_news)
        assert sentiment < 0.0  # Should be negative
        
    def test_analyze_market_sentiment_institutional(self):
        """Test market sentiment analysis with institutional news."""
        institutional_news = [
            NewsArticle(
                title="Major Banks Enter Crypto Market",
                description="Traditional finance embracing digital assets",
                url="https://example.com/banks-crypto",
                published_at=datetime.now(),
                source="Bloomberg"
            )
        ]
        
        sentiment = self.model._analyze_market_sentiment(institutional_news)
        assert sentiment > 0.0  # Should be positive for institutional adoption
        
    def test_get_technical_signal_strength_bullish(self):
        """Test technical signal strength for bullish indicators."""
        bullish_indicators = FinancialIndicators(
            rsi=45.0,  # Not overbought
            macd_signal="bullish",
            bollinger_position="lower",  # Room to grow
            volume_trend="increasing",
            momentum_score=0.75,
            trend_strength=0.80,
            volatility_index=0.35
        )
        
        strength = self.model._get_technical_signal_strength(bullish_indicators)
        assert strength > 0.0  # Should be positive
        
    def test_get_technical_signal_strength_bearish(self):
        """Test technical signal strength for bearish indicators."""
        bearish_indicators = FinancialIndicators(
            rsi=75.0,  # Overbought
            macd_signal="bearish",
            bollinger_position="upper",  # At resistance
            volume_trend="decreasing",
            momentum_score=0.25,
            trend_strength=0.30,
            volatility_index=0.65
        )
        
        strength = self.model._get_technical_signal_strength(bearish_indicators)
        assert strength < 0.0  # Should be negative
        
    def test_assess_institutional_adoption_high(self):
        """Test institutional adoption assessment with positive news."""
        institutional_news = [
            NewsArticle(
                title="Tesla Increases Bitcoin Holdings",
                description="Electric vehicle company adds to crypto portfolio",
                url="https://example.com/tesla-btc",
                published_at=datetime.now(),
                source="Reuters"
            ),
            NewsArticle(
                title="Pension Fund Allocates to Crypto",
                description="Major institutional investor embraces digital assets",
                url="https://example.com/pension-crypto",
                published_at=datetime.now(),
                source="Bloomberg"
            )
        ]
        
        adoption = self.model._assess_institutional_adoption(institutional_news)
        assert adoption > 0.0  # Should be positive
        
    def test_extract_price_targets_simple(self):
        """Test price target extraction from simple question."""
        question = "Will Bitcoin reach $100,000?"
        targets = self.model._extract_price_targets(question)
        assert 100000.0 in targets
        
    def test_extract_price_targets_multiple(self):
        """Test price target extraction with multiple targets."""
        question = "Will Bitcoin be above $80,000 or below $50,000?"
        targets = self.model._extract_price_targets(question)
        assert 80000.0 in targets
        assert 50000.0 in targets
        
    def test_extract_price_targets_no_targets(self):
        """Test price target extraction with no numeric targets."""
        question = "Will Bitcoin outperform the stock market?"
        targets = self.model._extract_price_targets(question)
        assert len(targets) == 0
        
    def test_calculate_distance_to_target_above(self):
        """Test distance calculation when price is below target."""
        current_price = 65000.0
        target_price = 100000.0
        
        distance = self.model._calculate_distance_to_target(current_price, target_price)
        expected = (100000.0 - 65000.0) / 65000.0  # ~53.8% increase needed
        assert abs(distance - expected) < 0.01
        
    def test_calculate_distance_to_target_below(self):
        """Test distance calculation when price is above target."""
        current_price = 65000.0
        target_price = 50000.0
        
        distance = self.model._calculate_distance_to_target(current_price, target_price)
        expected = (50000.0 - 65000.0) / 65000.0  # ~23% decrease needed
        assert abs(distance - expected) < 0.01
        
    def test_get_volatility_adjustment_high_volatility(self):
        """Test volatility adjustment for high volatility."""
        high_vol_indicators = FinancialIndicators(
            rsi=50.0,
            macd_signal="neutral",
            bollinger_position="middle",
            volume_trend="stable",
            momentum_score=0.5,
            trend_strength=0.4,
            volatility_index=0.8  # High volatility
        )
        
        adjustment = self.model._get_volatility_adjustment(high_vol_indicators)
        assert adjustment < 0.0  # Should reduce probability due to high volatility
        
    def test_get_volatility_adjustment_low_volatility(self):
        """Test volatility adjustment for low volatility."""
        low_vol_indicators = FinancialIndicators(
            rsi=50.0,
            macd_signal="neutral",
            bollinger_position="middle",
            volume_trend="stable",
            momentum_score=0.5,
            trend_strength=0.6,
            volatility_index=0.2  # Low volatility
        )
        
        adjustment = self.model._get_volatility_adjustment(low_vol_indicators)
        assert adjustment > 0.0  # Should increase probability due to stability
        
    @patch('src.analyzers.crypto_model.CryptoFinancialModel._get_etf_applications')
    @patch('src.analyzers.crypto_model.CryptoFinancialModel._get_market_data')
    @patch('src.analyzers.crypto_model.CryptoFinancialModel._get_technical_indicators')
    @patch('src.analyzers.crypto_model.CryptoFinancialModel._get_regulatory_sentiment')
    def test_calculate_crypto_probability_etf(self, mock_regulatory, mock_technical, mock_market, mock_etf):
        """Test full crypto probability calculation for ETF market."""
        # Mock data
        mock_etf.return_value = [self.etf_applications[0]]
        mock_market.return_value = self.market_data["BTC"]
        mock_technical.return_value = self.technical_indicators
        mock_regulatory.return_value = self.regulatory_sentiment
        
        market = self.markets["btc_etf"]
        result = self.model.calculate_crypto_probability(market, self.news_articles)
        
        assert isinstance(result, ProbabilityDistribution)
        assert 0.0 <= result.mean <= 1.0
        assert result.lower_bound <= result.mean <= result.upper_bound
        
    def test_calculate_crypto_probability_no_data(self):
        """Test crypto probability calculation with no data."""
        market = self.markets["btc_price"]
        
        with patch.object(self.model, '_get_market_data', return_value=None):
            with patch.object(self.model, '_get_technical_indicators', return_value=None):
                result = self.model.calculate_crypto_probability(market, [])
                
                assert isinstance(result, ProbabilityDistribution)
                assert 0.0 <= result.mean <= 1.0
                
    def test_get_etf_applications_placeholder(self):
        """Test ETF applications retrieval (placeholder implementation)."""
        applications = self.model._get_etf_applications("Bitcoin")
        assert isinstance(applications, list)
        
    def test_get_market_data_placeholder(self):
        """Test market data retrieval (placeholder implementation)."""
        data = self.model._get_market_data("Bitcoin")
        # Should return None in current implementation
        assert data is None
        
    def test_get_technical_indicators_placeholder(self):
        """Test technical indicators retrieval (placeholder implementation)."""
        indicators = self.model._get_technical_indicators("Bitcoin")
        # Should return None in current implementation
        assert indicators is None
        
    def test_get_regulatory_sentiment_placeholder(self):
        """Test regulatory sentiment retrieval (placeholder implementation)."""
        sentiment = self.model._get_regulatory_sentiment()
        # Should return None in current implementation
        assert sentiment is None
        
    def test_etf_application_creation(self):
        """Test ETFApplication dataclass creation."""
        application = ETFApplication(
            asset_name="Test Asset",
            applicant="Test Company",
            filing_date=datetime.now(),
            expected_decision_date=datetime.now() + timedelta(days=60),
            stage=ETFApprovalStage.UNDER_REVIEW,
            public_comments_count=500,
            sec_staff_feedback="neutral"
        )
        
        assert application.asset_name == "Test Asset"
        assert application.applicant == "Test Company"
        assert application.stage == ETFApprovalStage.UNDER_REVIEW
        assert application.public_comments_count == 500
        assert application.sec_staff_feedback == "neutral"
        
    def test_crypto_market_data_creation(self):
        """Test CryptoMarketData dataclass creation."""
        data = CryptoMarketData(
            symbol="TEST",
            current_price=1000.0,
            market_cap=10000000.0,
            volume_24h=1000000.0,
            price_change_7d=5.0,
            price_change_30d=10.0,
            rsi=50.0,
            ma_50=950.0,
            ma_200=800.0,
            support_level=900.0,
            resistance_level=1100.0
        )
        
        assert data.symbol == "TEST"
        assert data.current_price == 1000.0
        assert data.market_cap == 10000000.0
        assert data.volume_24h == 1000000.0
        assert data.rsi == 50.0
        
    def test_technical_indicators_creation(self):
        """Test FinancialIndicators dataclass creation."""
        indicators = FinancialIndicators(
            rsi=50.0,
            macd_signal="neutral",
            bollinger_position="middle",
            volume_trend="stable",
            momentum_score=0.5,
            trend_strength=0.6,
            volatility_index=0.4
        )
        
        assert indicators.rsi == 50.0
        assert indicators.macd_signal == "neutral"
        assert indicators.bollinger_position == "middle"
        assert indicators.volume_trend == "stable"
        assert indicators.momentum_score == 0.5
        
    def test_regulatory_sentiment_creation(self):
        """Test dict dataclass creation."""
        sentiment = dict(
            sec_stance="neutral",
            cftc_stance="positive",
            fed_stance="negative",
            recent_statements_sentiment=0.0,
            regulatory_clarity_score=0.5,
            compliance_trend="stable"
        )
        
        assert sentiment.sec_stance == "neutral"
        assert sentiment.cftc_stance == "positive"
        assert sentiment.fed_stance == "negative"
        assert sentiment.recent_statements_sentiment == 0.0
        assert sentiment.regulatory_clarity_score == 0.5


if __name__ == "__main__":
    pytest.main([__file__])