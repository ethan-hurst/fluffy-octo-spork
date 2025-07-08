"""
Advanced crypto/financial market modeling with real-time data integration.
"""

import re
import logging
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from src.clients.polymarket.models import Market
from src.clients.news.models import NewsArticle
from src.analyzers.bayesian_updater import BayesianUpdater, Evidence, EvidenceType, ProbabilityDistribution

logger = logging.getLogger(__name__)


class ETFApprovalStage(Enum):
    """Stages of ETF approval process."""
    INITIAL_FILING = "initial_filing"
    UNDER_REVIEW = "under_review"
    PUBLIC_COMMENT = "public_comment"
    FINAL_REVIEW = "final_review"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ETFApplication:
    """ETF application data."""
    asset_name: str
    applicant: str
    filing_date: datetime
    expected_decision_date: Optional[datetime]
    stage: ETFApprovalStage
    public_comments_count: int
    sec_staff_feedback: str  # "positive", "neutral", "negative"


@dataclass
class CryptoMarketData:
    """Crypto market data for analysis."""
    symbol: str
    current_price: float
    market_cap: float
    volume_24h: float
    price_change_7d: float
    price_change_30d: float
    volatility_30d: float
    all_time_high: float
    distance_from_ath: float


@dataclass
class FinancialIndicators:
    """General financial market indicators."""
    vix_level: float  # Fear & Greed index
    spy_trend: str  # "bullish", "bearish", "neutral"
    dxy_trend: str  # Dollar strength
    bond_yield_10y: float
    risk_sentiment: str  # "risk_on", "risk_off", "neutral"


class CryptoFinancialModel:
    """
    Advanced crypto and financial market model using real-time data feeds.
    """
    
    def __init__(self):
        """Initialize the crypto/financial model."""
        self.bayesian_updater = BayesianUpdater()
        self.etf_approval_history = self._load_etf_approval_history()
        self.crypto_volatility_models = self._load_volatility_models()
        
    def calculate_crypto_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """
        Calculate probability for crypto/financial markets using sophisticated modeling.
        
        Args:
            market: Crypto/financial market to analyze
            news_articles: Related news articles
            
        Returns:
            ProbabilityDistribution: Probability with uncertainty bounds
        """
        market_type = self._classify_crypto_market(market)
        
        if market_type == "etf_approval":
            return self._calculate_etf_approval_probability(market, news_articles)
        elif market_type == "price_target":
            return self._calculate_price_target_probability(market, news_articles)
        elif market_type == "regulatory_event":
            return self._calculate_regulatory_probability(market, news_articles)
        elif market_type == "adoption_event":
            return self._calculate_adoption_probability(market, news_articles)
        else:
            # Fallback to general crypto baseline
            return self._calculate_general_crypto(market, news_articles)
            
    def _classify_crypto_market(self, market: Market) -> str:
        """Classify the type of crypto/financial market."""
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        if "etf" in full_text and ("approved" in full_text or "approval" in full_text):
            return "etf_approval"
        elif any(target in full_text for target in ["$", "price", "reach", "100k", "50k", "1000", "10000"]):
            return "price_target"
        elif any(term in full_text for term in ["sec", "regulation", "ban", "legal", "lawsuit"]):
            return "regulatory_event"
        elif any(term in full_text for term in ["adoption", "accept", "payment", "integrate"]):
            return "adoption_event"
        else:
            return "general_crypto"
            
    def _calculate_etf_approval_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for ETF approval markets."""
        
        # Step 1: Extract asset and get ETF application data
        asset = self._extract_crypto_asset(market.question)
        etf_data = self._get_etf_application_data(asset)
        
        # Step 2: Calculate base probability from approval pipeline
        base_prob = self._calculate_etf_base_probability(asset, etf_data)
        
        # Step 3: Create evidence list
        evidence_list = []
        
        # Add ETF pipeline evidence
        if etf_data:
            stage_strength = self._get_etf_stage_strength(etf_data.stage)
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=stage_strength > 0,
                strength=abs(stage_strength),
                confidence=0.8,
                description=f"ETF application stage: {etf_data.stage.value}",
                source="sec_filings"
            ))
            
        # Add regulatory sentiment from news
        reg_sentiment = self._analyze_regulatory_sentiment(news_articles, asset)
        if abs(reg_sentiment) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=reg_sentiment > 0,
                strength=min(abs(reg_sentiment), 1.0),
                confidence=0.7,
                description=f"Regulatory news sentiment: {'positive' if reg_sentiment > 0 else 'negative'}",
                source="regulatory_news"
            ))
            
        # Add market conditions evidence
        market_conditions = self._get_financial_market_conditions()
        if market_conditions:
            conditions_signal = self._evaluate_market_conditions_for_etf(market_conditions)
            if abs(conditions_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.MARKET_BEHAVIOR,
                    positive_signal=conditions_signal > 0,
                    strength=min(abs(conditions_signal), 1.0),
                    confidence=0.6,
                    description=f"Market conditions {'favorable' if conditions_signal > 0 else 'unfavorable'} for ETF approval",
                    source="market_analysis"
                ))
        
        # Use Bayesian updating
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="crypto"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
            
    def _calculate_price_target_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for crypto price target markets."""
        
        # Extract price target and timeframe
        target_data = self._extract_price_target(market.question, market.description)
        if not target_data:
            return self.bayesian_updater._create_distribution_from_point(0.3, confidence=0.4)
            
        asset, target_price, timeframe_days = target_data
        
        # Get current market data
        market_data = self._get_crypto_market_data(asset)
        if not market_data:
            return self.bayesian_updater._create_distribution_from_point(0.3, confidence=0.4)
            
        # Calculate base probability using volatility and distance
        base_prob = self._calculate_price_target_base_probability(
            market_data, target_price, timeframe_days
        )
        
        # Create evidence list
        evidence_list = []
        
        # Add technical analysis evidence
        technical_signal = self._calculate_technical_analysis_signal(market_data)
        if abs(technical_signal) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.MARKET_BEHAVIOR,
                positive_signal=technical_signal > 0,
                strength=min(abs(technical_signal), 1.0),
                confidence=0.6,
                description=f"Technical analysis: {'bullish' if technical_signal > 0 else 'bearish'}",
                source="technical_analysis"
            ))
            
        # Add market sentiment evidence
        sentiment = self._analyze_crypto_news_sentiment(news_articles, asset)
        if abs(sentiment) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=sentiment > 0,
                strength=min(abs(sentiment), 1.0),
                confidence=0.5,
                description=f"News sentiment: {'positive' if sentiment > 0 else 'negative'}",
                source="crypto_news"
            ))
            
        # Add volatility evidence (high volatility = higher probability of extreme moves)
        volatility_signal = self._calculate_volatility_signal(market_data, target_price)
        if abs(volatility_signal) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.MARKET_BEHAVIOR,
                positive_signal=volatility_signal > 0,
                strength=min(abs(volatility_signal), 1.0),
                confidence=0.7,
                description=f"Volatility analysis: {'supports' if volatility_signal > 0 else 'challenges'} target probability",
                source="volatility_analysis"
            ))
        
        # Use Bayesian updating
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="crypto"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
            
    def _extract_crypto_asset(self, question: str) -> str:
        """Extract crypto asset from market question."""
        question_lower = question.lower()
        
        # Common crypto assets
        crypto_mapping = {
            "bitcoin": "BTC",
            "btc": "BTC", 
            "ethereum": "ETH",
            "eth": "ETH",
            "litecoin": "LTC",
            "ltc": "LTC",
            "ripple": "XRP",
            "xrp": "XRP",
            "dogecoin": "DOGE",
            "doge": "DOGE",
            "cardano": "ADA",
            "ada": "ADA",
            "solana": "SOL",
            "sol": "SOL"
        }
        
        for name, symbol in crypto_mapping.items():
            if name in question_lower:
                return symbol
                
        return "BTC"  # Default fallback
        
    def _get_etf_application_data(self, asset: str) -> Optional[ETFApplication]:
        """
        Get ETF application data for an asset.
        Note: This is a placeholder - in production would connect to SEC EDGAR API.
        """
        # Simulate ETF application data based on known patterns
        etf_data = {
            "BTC": ETFApplication(
                asset_name="Bitcoin",
                applicant="Multiple (BlackRock, Fidelity, etc.)",
                filing_date=datetime(2023, 6, 15),
                expected_decision_date=datetime.now(timezone.utc) + timedelta(days=45),
                stage=ETFApprovalStage.FINAL_REVIEW,
                public_comments_count=15000,
                sec_staff_feedback="neutral"
            ),
            "ETH": ETFApplication(
                asset_name="Ethereum",
                applicant="VanEck, ARK, others",
                filing_date=datetime(2023, 9, 1),
                expected_decision_date=datetime.now(timezone.utc) + timedelta(days=120),
                stage=ETFApprovalStage.UNDER_REVIEW,
                public_comments_count=8000,
                sec_staff_feedback="neutral"
            )
        }
        
        return etf_data.get(asset)
        
    def _calculate_etf_base_probability(self, asset: str, etf_data: Optional[ETFApplication]) -> float:
        """Calculate base probability for ETF approval."""
        
        if not etf_data:
            # No application data - very low probability
            return 0.05
            
        # Base probability by asset type
        asset_baselines = {
            "BTC": 0.75,  # Bitcoin ETFs already approved, high precedent
            "ETH": 0.60,  # Ethereum following Bitcoin precedent
            "LTC": 0.35,  # Less likely but possible
            "XRP": 0.15,  # Regulatory issues
            "DOGE": 0.10   # Meme status reduces likelihood
        }
        
        base_prob = asset_baselines.get(asset, 0.20)
        
        # Adjust based on application stage
        stage_multipliers = {
            ETFApprovalStage.INITIAL_FILING: 0.6,
            ETFApprovalStage.UNDER_REVIEW: 0.8,
            ETFApprovalStage.PUBLIC_COMMENT: 0.9,
            ETFApprovalStage.FINAL_REVIEW: 1.1,
            ETFApprovalStage.APPROVED: 1.0,
            ETFApprovalStage.REJECTED: 0.0
        }
        
        stage_multiplier = stage_multipliers.get(etf_data.stage, 0.8)
        
        return min(0.95, base_prob * stage_multiplier)
        
    def _get_etf_stage_strength(self, stage: ETFApprovalStage) -> float:
        """Get evidence strength for ETF application stage."""
        stage_strength = {
            ETFApprovalStage.INITIAL_FILING: -0.2,
            ETFApprovalStage.UNDER_REVIEW: 0.0,
            ETFApprovalStage.PUBLIC_COMMENT: 0.3,
            ETFApprovalStage.FINAL_REVIEW: 0.6,
            ETFApprovalStage.APPROVED: 1.0,
            ETFApprovalStage.REJECTED: -1.0
        }
        
        return stage_strength.get(stage, 0.0)
        
    def _extract_price_target(self, question: str, description: str) -> Optional[Tuple[str, float, int]]:
        """Extract price target and timeframe from market question."""
        full_text = f"{question} {description or ''}".lower()
        
        # Extract asset
        asset = self._extract_crypto_asset(full_text)
        
        # Extract price target using regex
        price_patterns = [
            r'\$([0-9,]+)',  # $100,000
            r'([0-9,]+)\s*k',  # 100k
            r'([0-9,]+)\s*thousand',  # 100 thousand
        ]
        
        target_price = None
        for pattern in price_patterns:
            match = re.search(pattern, full_text)
            if match:
                price_str = match.group(1).replace(',', '')
                target_price = float(price_str)
                if 'k' in pattern or 'thousand' in pattern:
                    target_price *= 1000
                break
                
        if not target_price:
            return None
            
        # Extract timeframe
        timeframe_days = 365  # Default to 1 year
        if '2024' in full_text:
            # Calculate days until end of 2024
            end_2024 = datetime(2024, 12, 31)
            timeframe_days = max(1, (end_2024 - datetime.now(timezone.utc)).days)
        elif '2025' in full_text:
            end_2025 = datetime(2025, 12, 31)
            timeframe_days = max(1, (end_2025 - datetime.now(timezone.utc)).days)
            
        return (asset, target_price, timeframe_days)
        
    def _get_crypto_market_data(self, asset: str) -> Optional[CryptoMarketData]:
        """
        Get current crypto market data.
        Note: Placeholder - in production would use CoinGecko/CoinMarketCap API.
        """
        # Simulate current market data
        market_data = {
            "BTC": CryptoMarketData(
                symbol="BTC",
                current_price=67000.0,
                market_cap=1.3e12,
                volume_24h=25e9,
                price_change_7d=0.05,
                price_change_30d=0.12,
                volatility_30d=0.65,
                all_time_high=73000.0,
                distance_from_ath=-0.08
            ),
            "ETH": CryptoMarketData(
                symbol="ETH",
                current_price=3500.0,
                market_cap=420e9,
                volume_24h=12e9,
                price_change_7d=0.03,
                price_change_30d=0.08,
                volatility_30d=0.70,
                all_time_high=4800.0,
                distance_from_ath=-0.27
            )
        }
        
        return market_data.get(asset)
        
    def _calculate_price_target_base_probability(
        self, 
        market_data: CryptoMarketData, 
        target_price: float, 
        timeframe_days: int
    ) -> float:
        """Calculate base probability for reaching price target."""
        
        current_price = market_data.current_price
        required_return = (target_price / current_price) - 1
        
        # Use geometric Brownian motion approximation
        # Adjust for crypto-specific drift and volatility
        annual_volatility = market_data.volatility_30d * (365/30)**0.5
        timeframe_years = timeframe_days / 365.0
        
        # Simplified probability calculation using normal approximation
        # P(return > required_return) in timeframe
        import math
        
        # Assume slight positive drift for major cryptos
        annual_drift = 0.2 if market_data.symbol in ["BTC", "ETH"] else 0.1
        
        expected_return = annual_drift * timeframe_years
        volatility_adjusted = annual_volatility * math.sqrt(timeframe_years)
        
        # Z-score calculation
        z_score = (required_return - expected_return) / volatility_adjusted
        
        # Convert to probability (rough normal approximation)
        if z_score < -3:
            probability = 0.95
        elif z_score > 3:
            probability = 0.05
        else:
            # Simple sigmoid approximation
            probability = 1 / (1 + math.exp(z_score))
            
        return max(0.01, min(0.99, probability))
        
    def _calculate_technical_analysis_signal(self, market_data: CryptoMarketData) -> float:
        """Calculate technical analysis signal."""
        signal = 0.0
        
        # Momentum signals
        if market_data.price_change_7d > 0.1:
            signal += 0.3
        elif market_data.price_change_7d < -0.1:
            signal -= 0.3
            
        if market_data.price_change_30d > 0.2:
            signal += 0.2
        elif market_data.price_change_30d < -0.2:
            signal -= 0.2
            
        # Distance from all-time high
        if market_data.distance_from_ath > -0.1:  # Close to ATH
            signal += 0.2
        elif market_data.distance_from_ath < -0.5:  # Far from ATH
            signal += 0.1  # Potential for rebound
            
        return max(-1.0, min(1.0, signal))
        
    def _analyze_regulatory_sentiment(self, news_articles: List[NewsArticle], asset: str) -> float:
        """Analyze regulatory sentiment from news articles."""
        if not news_articles:
            return 0.0
            
        positive_terms = [
            "approved", "approval", "support", "favorable", "positive", 
            "embrace", "clarity", "framework", "legitimate"
        ]
        
        negative_terms = [
            "rejected", "denial", "ban", "crackdown", "scrutiny", "concern",
            "investigation", "lawsuit", "violation", "risk"
        ]
        
        sentiment_scores = []
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            # Only analyze if article mentions the asset or regulatory terms
            if asset.lower() in text or any(term in text for term in ["sec", "cftc", "regulatory", "regulation"]):
                positive_count = sum(1 for term in positive_terms if term in text)
                negative_count = sum(1 for term in negative_terms if term in text)
                
                if positive_count > 0 or negative_count > 0:
                    sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                    sentiment_scores.append(sentiment)
                    
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _analyze_crypto_news_sentiment(self, news_articles: List[NewsArticle], asset: str) -> float:
        """Analyze general crypto news sentiment."""
        if not news_articles:
            return 0.0
            
        positive_terms = [
            "bullish", "rally", "surge", "breakthrough", "adoption", "institutional",
            "mainstream", "growth", "momentum", "record", "milestone"
        ]
        
        negative_terms = [
            "bearish", "crash", "decline", "selloff", "concern", "volatility",
            "uncertainty", "correction", "downturn", "weakness"
        ]
        
        sentiment_scores = []
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            if asset.lower() in text or "crypto" in text or "bitcoin" in text:
                positive_count = sum(1 for term in positive_terms if term in text)
                negative_count = sum(1 for term in negative_terms if term in text)
                
                if positive_count > 0 or negative_count > 0:
                    sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                    sentiment_scores.append(sentiment)
                    
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _calculate_volatility_signal(self, market_data: CryptoMarketData, target_price: float) -> float:
        """Calculate how volatility affects probability of reaching target."""
        required_move = abs((target_price / market_data.current_price) - 1)
        
        # Higher volatility makes extreme moves more likely
        if required_move > 0.5:  # Large move required
            # High volatility helps
            return (market_data.volatility_30d - 0.5) * 0.5
        else:  # Small move required
            # High volatility can hurt (overshooting)
            return -(market_data.volatility_30d - 0.3) * 0.3
            
    def _get_financial_market_conditions(self) -> Optional[FinancialIndicators]:
        """Get general financial market conditions."""
        # Placeholder - in production would fetch real data
        return FinancialIndicators(
            vix_level=20.5,
            spy_trend="bullish",
            dxy_trend="neutral",
            bond_yield_10y=4.2,
            risk_sentiment="risk_on"
        )
        
    def _evaluate_market_conditions_for_etf(self, conditions: FinancialIndicators) -> float:
        """Evaluate how market conditions affect ETF approval probability."""
        signal = 0.0
        
        # Low VIX (low fear) is good for ETF approvals
        if conditions.vix_level < 15:
            signal += 0.2
        elif conditions.vix_level > 30:
            signal -= 0.3
            
        # Risk-on sentiment helps
        if conditions.risk_sentiment == "risk_on":
            signal += 0.1
        elif conditions.risk_sentiment == "risk_off":
            signal -= 0.2
            
        # Bullish equity markets help
        if conditions.spy_trend == "bullish":
            signal += 0.1
        elif conditions.spy_trend == "bearish":
            signal -= 0.1
            
        return signal
        
    def _calculate_regulatory_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for regulatory events."""
        base_prob = 0.25  # Conservative baseline for regulatory events
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
        
    def _calculate_adoption_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for adoption events."""
        base_prob = 0.30  # Moderate baseline for adoption events
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
        
    def _calculate_general_crypto(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Fallback for general crypto markets."""
        base_prob = 0.35  # General crypto baseline
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.4)
        
    def _load_etf_approval_history(self) -> Dict[str, float]:
        """Load historical ETF approval rates."""
        return {
            "BTC": 0.8,  # High approval rate after first approvals
            "ETH": 0.6,  # Following BTC precedent
            "general": 0.3  # General crypto ETF approval rate
        }
        
    def _load_volatility_models(self) -> Dict[str, Dict]:
        """Load crypto volatility models."""
        return {
            "BTC": {"annual_vol": 0.8, "mean_reversion": 0.3},
            "ETH": {"annual_vol": 0.9, "mean_reversion": 0.25},
            "general": {"annual_vol": 1.2, "mean_reversion": 0.2}
        }