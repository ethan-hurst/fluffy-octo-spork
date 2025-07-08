"""
Sophisticated fair value calculation engine.
Replaces the naive 50% baseline with intelligent base rates.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.clients.polymarket.models import Market
from src.clients.news.models import NewsArticle
from src.analyzers.llm_news_analyzer import LLMNewsAnalyzer
from src.analyzers.market_categorizer import MarketCategorizer

logger = logging.getLogger(__name__)


@dataclass
class BaseRateData:
    """Historical base rate information for a market type."""
    probability: float
    confidence: float
    sample_size: int
    last_updated: datetime
    source: str


class FairValueEngine:
    """
    Advanced fair value calculation using historical base rates,
    market fundamentals, and intelligent probability estimation.
    """
    
    def __init__(self):
        """Initialize the fair value engine."""
        self.base_rates = self._load_base_rates()
        self.market_patterns = self._load_market_patterns()
        self.llm_news_analyzer = LLMNewsAnalyzer()
        self.categorizer = MarketCategorizer()
        
    async def calculate_fair_value(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> Tuple[float, float, str]:
        """
        Calculate sophisticated fair value for a market.
        
        Args:
            market: Market to analyze
            news_articles: Related news articles
            
        Returns:
            Tuple[float, float, str]: (fair_yes_price, fair_no_price, reasoning)
        """
        # Step 1: Get intelligent base probability
        base_prob, base_reasoning = self._get_base_probability(market)
        is_constitutional = self._is_constitutional_amendment(market)
        
        # Step 2: Apply sophisticated news sentiment adjustment
        news_adjustment, news_reasoning = await self._calculate_llm_news_adjustment(news_articles, market)
        
        # Step 3: Apply temporal factors (skip for constitutional amendments - already factored in)
        if is_constitutional:
            time_adjustment, time_reasoning = 0.0, "Constitutional amendment timeline already factored into base probability"
        else:
            time_adjustment, time_reasoning = self._calculate_time_adjustment(market)
        
        # Step 4: Apply market-specific factors
        market_adjustment, market_reasoning = self._calculate_market_adjustment(market)
        
        # Step 5: Combine all factors
        final_probability = self._combine_factors(
            base_prob, news_adjustment, time_adjustment, market_adjustment
        )
        
        # Ensure reasonable bounds
        final_probability = max(0.02, min(0.98, final_probability))
        
        reasoning = self._generate_reasoning(
            base_prob, base_reasoning, news_adjustment, news_reasoning,
            time_adjustment, time_reasoning, market_adjustment, market_reasoning,
            final_probability
        )
        
        return final_probability, 1.0 - final_probability, reasoning
        
    def _get_base_probability(self, market: Market) -> Tuple[float, str]:
        """
        Get intelligent base probability using historical patterns.
        
        Args:
            market: Market to analyze
            
        Returns:
            Tuple[float, str]: (base_probability, reasoning)
        """
        question_lower = market.question.lower()
        
        # Political Elections - Multi-party systems
        if self._is_multi_party_election(market):
            return self._calculate_multi_party_probability(market)
            
        # Constitutional Amendments (must come before general political)
        if self._is_constitutional_amendment(market):
            return self._calculate_constitutional_probability(market)
            
        # Binary Political Events
        if self._is_political_binary(market):
            return self._calculate_political_binary_probability(market)
            
        # Crypto/Financial Events
        if self._is_crypto_financial(market):
            return self._calculate_crypto_probability(market)
            
        # Sports Events
        if self._is_sports_event(market):
            return self._calculate_sports_probability(market)
            
        # Corporate/Business Events
        if self._is_corporate_event(market):
            return self._calculate_corporate_probability(market)
            
        # Natural Disasters/Rare Events
        if self._is_rare_event(market):
            return self._calculate_rare_event_probability(market)
            
        # Use learning categorizer for unknown types
        category, baseline_prob, reasoning = self.categorizer.categorize_market(market)
        return baseline_prob, reasoning
        
    def _is_multi_party_election(self, market: Market) -> bool:
        """Check if this is a multi-party election market."""
        question = market.question.lower()
        has_election_phrase = any(phrase in question for phrase in [
            "most seats", "win the most", "hold the most", "plurality", "largest party"
        ])
        has_party_indicator = any(party in question for party in [
            "ldp", "cdp", "party", "democratic", "republican", "conservative", "liberal",
            "sdp", "jcp", "komeito", "jip", "dpj", "dpp", "labour", "labor", "green",
            "reiwa", "shinsengumi"
        ])
        return has_election_phrase and has_party_indicator
        
    def _calculate_multi_party_probability(self, market: Market) -> Tuple[float, str]:
        """Calculate probability for multi-party elections."""
        question = market.question.lower()
        
        # Major parties (historical advantage)
        if any(party in question for party in ["ldp", "liberal democratic party"]):
            return 0.42, "LDP historically wins ~42% of Japanese elections"
        elif any(party in question for party in ["cdp", "constitutional democratic"]):
            return 0.28, "CDP is main opposition with ~28% historical win rate"
        elif any(party in question for party in ["republican", "gop"]):
            return 0.45, "Republican Party wins ~45% of US elections"
        elif any(party in question for party in ["democratic", "democrat"]):
            return 0.45, "Democratic Party wins ~45% of US elections"
        elif any(party in question for party in ["conservative", "tory"]):
            return 0.40, "Conservative parties historically win ~40% in Westminster systems"
        elif any(party in question for party in ["labour", "labor"]):
            return 0.35, "Labour parties win ~35% historically"
            
        # Japanese specific parties
        elif any(party in question for party in ["komeito"]):
            return 0.12, "Komeito is a significant coalition partner (~12% win rate)"
        elif any(party in question for party in ["jip", "japan innovation party"]):
            return 0.09, "Japan Innovation Party is a growing minor party (~9% win rate)"
        elif any(party in question for party in ["dpj", "democratic party of japan"]):
            return 0.08, "Democratic Party of Japan has limited current influence (~8% win rate)"
        elif any(party in question for party in ["jcp", "japan communist party", "communist"]):
            return 0.04, "Japan Communist Party has minimal electoral success (~4% win rate)"
        elif any(party in question for party in ["sdp", "social democratic party"]):
            return 0.03, "Social Democratic Party has very limited support (~3% win rate)"
        elif any(party in question for party in ["reiwa shinsengumi", "reiwa"]):
            return 0.02, "Reiwa Shinsengumi is a very small party with ~2% win rate"
        elif any(party in question for party in ["dpp", "democratic progressive party"]):
            return 0.03, "Democratic Progressive Party has limited support (~3% win rate)"
            
        # Generic minor parties
        elif any(party in question for party in ["green", "libertarian", "reform"]):
            return 0.08, "Minor parties rarely win major elections (~8% success rate)"
        elif any(party in question for party in ["communist", "socialist"]):
            return 0.05, "Far-left parties have ~5% win rate in developed democracies"
        elif any(party in question for party in ["minor"]):
            return 0.05, "Generic minor parties have ~5% win rate"
        else:
            # Unknown party - check if it sounds like a small party
            if any(indicator in question for indicator in ["new", "citizens", "people's", "workers"]):
                return 0.04, "Unknown small party - using minimal baseline (4%)"
            else:
                return 0.08, "Unknown party - using minor party baseline (8%)"
            
    def _is_political_binary(self, market: Market) -> bool:
        """Check if this is a binary political event."""
        question = market.question.lower()
        return any(term in question for term in [
            "trump", "biden", "president", "election", "impeach", "resign", 
            "tariff", "war", "treaty", "law", "bill", "congress", "senate"
        ])
        
    def _calculate_political_binary_probability(self, market: Market) -> Tuple[float, str]:
        """Calculate probability for binary political events."""
        question = market.question.lower()
        
        # Presidential Elections
        if "president" in question and "elect" in question:
            if "trump" in question:
                return 0.48, "Trump historically competitive in elections (~48% baseline)"
            elif "biden" in question:
                return 0.47, "Biden/incumbent advantage (~47% baseline)"
            else:
                return 0.45, "Presidential elections typically close (~45% for challengers)"
                
        # Policy Implementation
        if any(policy in question for policy in ["tariff", "tax", "law", "bill"]):
            if "first" in question and ("month" in question or "100 days" in question):
                return 0.65, "New presidents implement ~65% of first-term promises"
            else:
                return 0.35, "Congressional legislation has ~35% passage rate"
                
        # Geopolitical Events
        if any(event in question for event in ["war", "military", "troops", "conflict"]):
            return 0.25, "Military conflicts are relatively rare (~25% base rate)"
            
        # Resignation/Impeachment
        if any(event in question for event in ["resign", "impeach", "remove"]):
            return 0.15, "Political removals are rare (~15% historical rate)"
            
        return 0.40, "Generic political event baseline (40%)"
        
    def _is_constitutional_amendment(self, market: Market) -> bool:
        """Check if this market involves a Constitutional amendment."""
        question = market.question.lower()
        description = (market.description or "").lower()
        
        # Direct constitutional amendment indicators
        constitutional_indicators = [
            "constitutional amendment", "22nd amendment", "term limits", "repeal",
            "constitution", "amendment", "supreme court", "constitutional"
        ]
        
        # Actions that require constitutional changes
        action_indicators = [
            "repeal presidential term limits", "change term limits", "third term",
            "more than two terms", "eliminate term limits", "extend presidency"
        ]
        
        # Check in both question and description
        full_text = f"{question} {description}"
        
        has_constitutional = any(indicator in full_text for indicator in constitutional_indicators)
        has_action = any(indicator in full_text for indicator in action_indicators)
        
        # Specific Trump term limits case
        is_trump_term_limits = "trump" in full_text and any(term in full_text for term in ["term limit", "22nd amendment", "third term"])
        
        return has_constitutional and has_action or is_trump_term_limits
        
    def _calculate_constitutional_probability(self, market: Market) -> Tuple[float, str]:
        """Calculate probability for Constitutional amendment markets."""
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        # Check timeline - constitutional amendments take years typically
        days_remaining = self._get_days_remaining(market)
        
        if days_remaining and days_remaining < 365:  # Less than 1 year
            # Constitutional amendments virtually impossible in under 1 year
            if days_remaining < 180:  # Less than 6 months
                return 0.005, "Constitutional amendment impossible in <6 months (0.5% for extreme edge cases)"
            else:
                return 0.01, "Constitutional amendment extremely unlikely in <1 year (1% baseline)"
        
        # Long-term constitutional amendments (>1 year)
        if "22nd amendment" in full_text or "term limits" in full_text:
            return 0.02, "Repealing 22nd Amendment requires 2/3 Congress + 3/4 states - historically impossible (2%)"
            
        if "supreme court" in full_text and any(term in full_text for term in ["overturn", "rule", "decision"]):
            return 0.03, "Supreme Court overturning constitutional precedent extremely rare (3%)"
            
        # Generic constitutional amendment
        return 0.015, "Constitutional amendments succeed <2% of the time historically (1.5%)"
        
    def _get_days_remaining(self, market: Market) -> Optional[int]:
        """Get days remaining until market resolution."""
        if not market.end_date_iso:
            return None
            
        now = datetime.now()
        if market.end_date_iso.tzinfo is not None:
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        else:
            market.end_date_iso = market.end_date_iso.replace(tzinfo=None)
            
        return (market.end_date_iso - now).days
        
    def _is_crypto_financial(self, market: Market) -> bool:
        """Check if this is a crypto/financial market."""
        question = market.question.lower()
        return any(term in question for term in [
            "bitcoin", "ethereum", "crypto", "btc", "eth", "price", "etf", 
            "sec", "approved", "stock", "market", "$"
        ])
        
    def _calculate_crypto_probability(self, market: Market) -> Tuple[float, str]:
        """Calculate probability for crypto/financial events."""
        question = market.question.lower()
        
        # ETF Approvals
        if "etf" in question and "approved" in question:
            if "bitcoin" in question:
                return 0.75, "Bitcoin ETF already approved - high precedent (75%)"
            elif "ethereum" in question:
                return 0.60, "Ethereum ETF following Bitcoin precedent (60%)"
            elif any(coin in question for coin in ["litecoin", "ltc"]):
                return 0.35, "Litecoin ETF less likely without major adoption (35%)"
            elif any(coin in question for coin in ["ripple", "xrp"]):
                return 0.25, "Ripple ETF unlikely due to SEC litigation (25%)"
            elif any(coin in question for coin in ["doge", "dogecoin"]):
                return 0.20, "Dogecoin ETF unlikely due to meme status (20%)"
            else:
                return 0.30, "Generic crypto ETF approval rate (~30%)"
                
        # Price Targets
        if any(target in question for target in ["$", "price", "reach", "100k", "50k"]):
            # Extract price targets and timeframes for more sophisticated analysis
            return 0.35, "Crypto price targets historically achieved ~35% of the time"
            
        return 0.40, "Generic crypto event baseline (40%)"
        
    def _is_sports_event(self, market: Market) -> bool:
        """Check if this is a sports event."""
        question = market.question.lower()
        return any(term in question for term in [
            "nfl", "nba", "mlb", "nhl", "championship", "super bowl", "world series",
            "playoffs", "trade", "draft", "coach", "fire", "retire", "mvp"
        ])
        
    def _calculate_sports_probability(self, market: Market) -> Tuple[float, str]:
        """Calculate probability for sports events."""
        question = market.question.lower()
        
        # Coaching Changes
        if any(term in question for term in ["fire", "fired", "coach"]):
            return 0.25, "NFL coaches fired mid-season: ~25% rate"
            
        # Player Retirement
        if "retire" in question:
            if any(age_indicator in question for age_indicator in ["old", "veteran", "aging"]):
                return 0.40, "Veteran player retirements occur ~40% rate"
            else:
                return 0.15, "Early retirement rate: ~15%"
                
        # Championships
        if any(term in question for term in ["championship", "super bowl", "world series"]):
            # With 32 NFL teams, base probability would be ~3%, but market teams are pre-filtered
            return 0.25, "Championship markets pre-filter to competitive teams (~25%)"
            
        # Trades
        if "trade" in question:
            return 0.30, "High-profile trades occur ~30% of the time when speculated"
            
        return 0.35, "Generic sports event baseline (35%)"
        
    def _is_corporate_event(self, market: Market) -> bool:
        """Check if this is a corporate/business event."""
        question = market.question.lower()
        return any(term in question for term in [
            "merger", "acquisition", "ceo", "earnings", "ipo", "bankruptcy",
            "tesla", "apple", "amazon", "google", "microsoft", "meta"
        ])
        
    def _calculate_corporate_probability(self, market: Market) -> Tuple[float, str]:
        """Calculate probability for corporate events."""
        question = market.question.lower()
        
        # Mergers & Acquisitions
        if any(term in question for term in ["merger", "acquisition", "buyout"]):
            return 0.20, "Rumored M&A deals complete ~20% of the time"
            
        # CEO Changes
        if "ceo" in question and any(term in question for term in ["resign", "fire", "step down"]):
            return 0.18, "CEO departures under pressure: ~18% annual rate"
            
        # Earnings Beats
        if "earnings" in question:
            return 0.55, "Companies beat earnings expectations ~55% of the time"
            
        return 0.30, "Generic corporate event baseline (30%)"
        
    def _is_rare_event(self, market: Market) -> bool:
        """Check if this is a rare/catastrophic event."""
        question = market.question.lower()
        return any(term in question for term in [
            "pandemic", "earthquake", "hurricane", "war", "nuclear", "asteroid",
            "collapse", "crash", "disaster", "outbreak"
        ])
        
    def _calculate_rare_event_probability(self, market: Market) -> Tuple[float, str]:
        """Calculate probability for rare events."""
        question = market.question.lower()
        
        # Pandemics
        if "pandemic" in question:
            return 0.08, "Major pandemics occur ~once every 12-15 years (8% annual rate)"
            
        # Natural Disasters
        if any(term in question for term in ["earthquake", "hurricane", "tsunami"]):
            return 0.15, "Major natural disasters: ~15% annual probability in risk areas"
            
        # Market Crashes
        if any(term in question for term in ["crash", "collapse", "recession"]):
            return 0.20, "Market corrections >20%: ~20% probability in any given year"
            
        # Wars/Conflicts
        if "war" in question:
            return 0.12, "New major conflicts: ~12% annual probability globally"
            
        return 0.10, "Rare event baseline (10%)"
        
    async def _calculate_llm_news_adjustment(self, news_articles: List[NewsArticle], market: Market) -> Tuple[float, str]:
        """Calculate probability adjustment using LLM-powered news analysis."""
        if not news_articles:
            return 0.0, "No news coverage found"
            
        try:
            # Get sophisticated news analysis
            news_analysis = await self.llm_news_analyzer.analyze_market_news(market, news_articles)
            
            # Use the calculated probability adjustment from LLM analysis
            adjustment = news_analysis.probability_adjustment
            
            # Create detailed reasoning
            sentiment_desc = "positive" if news_analysis.overall_sentiment > 0.1 else "negative" if news_analysis.overall_sentiment < -0.1 else "neutral"
            
            reasoning = f"LLM News Analysis: {sentiment_desc} sentiment "
            reasoning += f"({news_analysis.sentiment_confidence:.1%} confidence), "
            reasoning += f"{news_analysis.credible_sources_count} credible sources, "
            reasoning += f"impact score: {news_analysis.news_impact_score:.2f}"
            
            return adjustment, reasoning
            
        except Exception as e:
            logger.error(f"LLM news analysis failed: {e}")
            # Fallback to simple analysis
            return self._calculate_fallback_news_adjustment(news_articles, market)
    
    def _calculate_fallback_news_adjustment(self, news_articles: List[NewsArticle], market: Market) -> Tuple[float, str]:
        """Fallback news analysis when LLM fails."""
        if not news_articles:
            return 0.0, "No news coverage found"
            
        # Use simplified sentiment analysis
        sentiment_score = self._simple_news_sentiment(news_articles)
        
        # Convert sentiment to probability adjustment (-0.15 to +0.15)
        adjustment = sentiment_score * 0.15
        
        sentiment_desc = "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral"
        
        return adjustment, f"Fallback news analysis: {sentiment_desc} sentiment ({len(news_articles)} articles)"
        
    def _simple_news_sentiment(self, news_articles: List[NewsArticle]) -> float:
        """Simple sentiment analysis (to be replaced with LLM)."""
        positive_keywords = [
            "approved", "success", "win", "victory", "positive", "good", "strong", 
            "growth", "increase", "improve", "better", "up", "gain", "likely"
        ]
        negative_keywords = [
            "rejected", "fail", "lose", "defeat", "negative", "bad", "weak",
            "decline", "decrease", "worse", "down", "loss", "drop", "unlikely"
        ]
        
        total_sentiment = 0.0
        article_count = 0
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in text)
            negative_count = sum(1 for keyword in negative_keywords if keyword in text)
            
            if positive_count > 0 or negative_count > 0:
                article_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                total_sentiment += article_sentiment
                article_count += 1
                
        return total_sentiment / article_count if article_count > 0 else 0.0
        
    def _calculate_time_adjustment(self, market: Market) -> Tuple[float, str]:
        """Calculate probability adjustment based on timing factors."""
        if not market.end_date_iso:
            return 0.0, "No end date available"
            
        now = datetime.now()
        if market.end_date_iso.tzinfo is not None:
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        else:
            market.end_date_iso = market.end_date_iso.replace(tzinfo=None)
            
        days_remaining = (market.end_date_iso - now).days
        
        if days_remaining <= 7:
            return 0.0, "Very close to resolution - no time adjustment"
        elif days_remaining <= 30:
            return -0.02, "Near-term event - slight conservatism"
        elif days_remaining <= 90:
            return -0.05, "Medium-term event - moderate conservatism"
        else:
            return -0.08, "Long-term event - high uncertainty discount"
            
    def _calculate_market_adjustment(self, market: Market) -> Tuple[float, str]:
        """Calculate probability adjustment based on market-specific factors."""
        adjustment = 0.0
        reasons = []
        
        # Volume-based adjustment
        if market.volume:
            if market.volume > 100000:
                adjustment += 0.02
                reasons.append("high volume (+2%)")
            elif market.volume < 5000:
                adjustment -= 0.03
                reasons.append("low volume (-3%)")
                
        # Category-based adjustment
        if market.category:
            category_lower = market.category.lower()
            if "politics" in category_lower:
                adjustment += 0.01
                reasons.append("political market (+1%)")
            elif "crypto" in category_lower:
                adjustment -= 0.02
                reasons.append("crypto volatility (-2%)")
                
        reason = f"Market factors: {', '.join(reasons)}" if reasons else "No market adjustments"
        return adjustment, reason
        
    def _combine_factors(self, base_prob: float, news_adj: float, time_adj: float, market_adj: float) -> float:
        """Combine all probability factors intelligently."""
        # Start with base probability
        final_prob = base_prob
        
        # Add adjustments
        final_prob += news_adj + time_adj + market_adj
        
        # Apply diminishing returns for extreme values
        if final_prob > 0.8:
            excess = final_prob - 0.8
            final_prob = 0.8 + (excess * 0.5)  # Diminishing returns
        elif final_prob < 0.2:
            deficit = 0.2 - final_prob
            final_prob = 0.2 - (deficit * 0.5)  # Diminishing returns
            
        return final_prob
        
    def _generate_reasoning(self, base_prob: float, base_reason: str, 
                          news_adj: float, news_reason: str,
                          time_adj: float, time_reason: str,
                          market_adj: float, market_reason: str,
                          final_prob: float) -> str:
        """Generate human-readable reasoning for the fair value calculation."""
        reasoning_parts = [
            f"Base probability: {base_prob:.1%} ({base_reason})"
        ]
        
        if abs(news_adj) > 0.01:
            sign = "+" if news_adj > 0 else ""
            reasoning_parts.append(f"News adjustment: {sign}{news_adj:.1%} ({news_reason})")
            
        if abs(time_adj) > 0.01:
            sign = "+" if time_adj > 0 else ""
            reasoning_parts.append(f"Time adjustment: {sign}{time_adj:.1%} ({time_reason})")
            
        if abs(market_adj) > 0.01:
            sign = "+" if market_adj > 0 else ""
            reasoning_parts.append(f"Market adjustment: {sign}{market_adj:.1%} ({market_reason})")
            
        reasoning_parts.append(f"Final fair value: {final_prob:.1%}")
        
        return " | ".join(reasoning_parts)
        
    def learn_from_outcome(self, condition_id: str, actual_outcome: bool, final_probability: float) -> None:
        """
        Learn from market outcomes to improve future predictions.
        
        Args:
            condition_id: Market condition ID
            actual_outcome: Whether market resolved to YES
            final_probability: Market price at resolution
        """
        self.categorizer.learn_from_outcomes(condition_id, actual_outcome, final_probability)
        
    def get_learning_suggestions(self) -> List[Dict]:
        """Get suggestions for new market categories to add."""
        return self.categorizer.suggest_new_patterns()
        
    def _load_base_rates(self) -> Dict[str, BaseRateData]:
        """Load historical base rates (placeholder for future database)."""
        # TODO: Load from historical database
        return {}
        
    def _load_market_patterns(self) -> Dict[str, float]:
        """Load market-specific patterns (placeholder for future ML)."""
        # TODO: Load from machine learning models
        return {}