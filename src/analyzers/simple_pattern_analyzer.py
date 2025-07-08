"""
Simple pattern-based market analyzer.
Replaces complex fair value engine with proven heuristics.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.clients.polymarket.models import Market, MarketPrice
from src.clients.news.models import NewsArticle

logger = logging.getLogger(__name__)


@dataclass
class SimpleOpportunity:
    """A simple trading opportunity."""
    market: Market
    current_price: float
    recommended_action: str  # "BUY_YES", "BUY_NO", "SELL_YES", "SELL_NO"
    edge: float  # Expected edge (0-1)
    confidence: float  # Confidence in edge (0-1)
    reason: str
    pattern_type: str  # "TIME_DECAY", "EXTREME_PRICE", "NEWS_OVERREACTION", etc.


class SimplePatternAnalyzer:
    """
    Find trading opportunities using simple, proven patterns.
    No complex models, just market inefficiencies.
    """
    
    def __init__(self):
        """Initialize the simple analyzer."""
        # Thresholds
        self.min_edge = 0.10  # 10% minimum edge
        self.min_volume = 5000  # $5k minimum volume
        self.time_decay_days = 7  # Focus on markets ending within a week
        
        # Pattern weights (how much we trust each pattern)
        self.pattern_confidence = {
            'TIME_DECAY': 0.7,
            'EXTREME_PRICE': 0.6,
            'NEWS_OVERREACTION': 0.5,
            'STRUCTURAL': 0.8,
        }
    
    def analyze_market(
        self,
        market: Market,
        price: MarketPrice,
        news_articles: List[NewsArticle] = None
    ) -> Optional[SimpleOpportunity]:
        """
        Analyze a single market for opportunities.
        
        Args:
            market: Market to analyze
            price: Current market price
            news_articles: Recent news (optional)
            
        Returns:
            SimpleOpportunity if found, None otherwise
        """
        # Skip low volume markets
        if market.volume and market.volume < self.min_volume:
            return None
            
        # Skip markets already at extremes (0 or 1)
        if price.yes_price <= 0.01 or price.yes_price >= 0.99:
            return None
        
        # Try each pattern
        patterns = [
            self._check_time_decay(market, price),
            self._check_extreme_pricing(market, price),
            self._check_structural_inefficiency(market, price),
        ]
        
        # Add news pattern if we have articles
        if news_articles:
            patterns.append(self._check_news_overreaction(market, price, news_articles))
        
        # Return the best opportunity
        opportunities = [p for p in patterns if p is not None]
        if opportunities:
            # Sort by edge * confidence
            opportunities.sort(key=lambda x: x.edge * x.confidence, reverse=True)
            return opportunities[0]
            
        return None
    
    def _check_time_decay(self, market: Market, price: MarketPrice) -> Optional[SimpleOpportunity]:
        """
        Check for time decay opportunities.
        Markets close to resolution with prices far from 0 or 1.
        """
        if not market.end_date_iso:
            return None
            
        days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
        
        # Only interested in markets ending soon
        if days_left > self.time_decay_days or days_left < 0:
            return None
            
        # Calculate expected movement
        # Rule: Unlikely to move more than 10% per day in final week
        max_likely_move = 0.10 * days_left
        
        # If price is far from extremes, bet against movement
        if 0.2 < price.yes_price < 0.8:
            # Bet against the direction further from 0.5
            if price.yes_price > 0.5:
                # Price is high, bet it won't go higher
                edge = (price.yes_price - 0.5) * (1 - max_likely_move)
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=min(edge, 0.3),  # Cap edge at 30%
                    confidence=self.pattern_confidence['TIME_DECAY'],
                    reason=f"Only {days_left} days left - price unlikely to rise further",
                    pattern_type="TIME_DECAY"
                )
            else:
                # Price is low, bet it won't go lower
                edge = (0.5 - price.yes_price) * (1 - max_likely_move)
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_YES",
                    edge=min(edge, 0.3),
                    confidence=self.pattern_confidence['TIME_DECAY'],
                    reason=f"Only {days_left} days left - price unlikely to fall further",
                    pattern_type="TIME_DECAY"
                )
                
        return None
    
    def _check_extreme_pricing(self, market: Market, price: MarketPrice) -> Optional[SimpleOpportunity]:
        """
        Check for extreme mispricing.
        Long shots too high, sure things too low.
        """
        question = market.question.lower()
        
        # Long shot patterns
        longshot_keywords = [
            'reach $1 million', 'reach $500k', '10x', '1000%',
            'break all-time high', 'exceed 1 billion', 'go viral'
        ]
        
        if any(keyword in question for keyword in longshot_keywords):
            if price.yes_price > 0.15:  # Long shot priced above 15%
                edge = price.yes_price - 0.05  # Assume 5% fair value
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=edge,
                    confidence=self.pattern_confidence['EXTREME_PRICE'],
                    reason="Long-shot event overpriced",
                    pattern_type="EXTREME_PRICE"
                )
        
        # Near certainty patterns
        certainty_keywords = [
            'sun rise', 'continue to exist', 'remain president until',
            'complete their term', 'still be trading'
        ]
        
        if any(keyword in question for keyword in certainty_keywords):
            if price.yes_price < 0.85:  # Near certainty priced below 85%
                edge = 0.95 - price.yes_price  # Assume 95% fair value
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_YES",
                    edge=edge,
                    confidence=self.pattern_confidence['EXTREME_PRICE'],
                    reason="Near-certain event underpriced",
                    pattern_type="EXTREME_PRICE"
                )
                
        return None
    
    def _check_structural_inefficiency(self, market: Market, price: MarketPrice) -> Optional[SimpleOpportunity]:
        """
        Check for structural market inefficiencies.
        """
        # Binary outcome far from 50/50
        if self._is_true_binary(market.question):
            distance_from_half = abs(price.yes_price - 0.5)
            if distance_from_half > 0.15:  # More than 15% from 50/50
                if price.yes_price > 0.5:
                    edge = distance_from_half - 0.05  # Keep 5% buffer
                    action = "BUY_NO"
                else:
                    edge = distance_from_half - 0.05
                    action = "BUY_YES"
                    
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action=action,
                    edge=edge,
                    confidence=self.pattern_confidence['STRUCTURAL'],
                    reason="True binary event should be closer to 50/50",
                    pattern_type="STRUCTURAL"
                )
        
        # Constitutional/legal impossibilities
        if self._is_constitutional_impossibility(market.question):
            if price.yes_price > 0.05:
                edge = price.yes_price - 0.02  # These should trade at 2% max
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=edge,
                    confidence=self.pattern_confidence['STRUCTURAL'] * 1.2,  # Higher confidence
                    reason="Constitutional/legal impossibility overpriced",
                    pattern_type="STRUCTURAL"
                )
                
        return None
    
    def _check_news_overreaction(
        self,
        market: Market,
        price: MarketPrice,
        news_articles: List[NewsArticle]
    ) -> Optional[SimpleOpportunity]:
        """
        Check for news-driven overreactions.
        Markets often overreact to headlines.
        """
        # Count relevant news mentions
        question_keywords = market.question.lower().split()
        relevant_articles = 0
        
        for article in news_articles[:20]:  # Check recent 20 articles
            article_text = f"{article.title} {article.description or ''}".lower()
            if any(keyword in article_text for keyword in question_keywords if len(keyword) > 4):
                relevant_articles += 1
        
        # High news volume often indicates overreaction
        if relevant_articles >= 5:
            # Check if price moved significantly (would need historical data)
            # For now, assume prices far from 0.5 with high news volume are overreactions
            if price.yes_price > 0.7:
                edge = 0.15  # Assume 15% overreaction
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=edge,
                    confidence=self.pattern_confidence['NEWS_OVERREACTION'],
                    reason=f"High news volume ({relevant_articles} articles) - possible overreaction",
                    pattern_type="NEWS_OVERREACTION"
                )
            elif price.yes_price < 0.3:
                edge = 0.15
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_YES",
                    edge=edge,
                    confidence=self.pattern_confidence['NEWS_OVERREACTION'],
                    reason=f"High news volume ({relevant_articles} articles) - possible overreaction",
                    pattern_type="NEWS_OVERREACTION"
                )
                
        return None
    
    def _is_true_binary(self, question: str) -> bool:
        """Check if this is a true 50/50 binary event."""
        binary_patterns = [
            'coin flip', 'coin toss', 'heads or tails',
            'odd or even', 'red or black', 'random',
            'die roll', 'dice'
        ]
        question_lower = question.lower()
        return any(pattern in question_lower for pattern in binary_patterns)
    
    def _is_constitutional_impossibility(self, question: str) -> bool:
        """Check if this requires constitutional change or is legally impossible."""
        impossible_patterns = [
            'constitutional amendment', 'repeal the', 'third term',
            'change the constitution', 'abolish the supreme court',
            'merge states', 'secede from'
        ]
        question_lower = question.lower()
        return any(pattern in question_lower for pattern in impossible_patterns)
    
    def calculate_fair_value(
        self,
        opportunity: SimpleOpportunity
    ) -> Tuple[float, float]:
        """
        Calculate simple fair value based on opportunity.
        
        Returns:
            Tuple of (fair_yes_price, fair_no_price)
        """
        current = opportunity.current_price
        
        if opportunity.recommended_action == "BUY_YES":
            fair_yes = min(0.95, current + opportunity.edge)
            fair_no = 1.0 - fair_yes
        elif opportunity.recommended_action == "BUY_NO":
            fair_yes = max(0.05, current - opportunity.edge)
            fair_no = 1.0 - fair_yes
        else:
            # SELL actions - price should move toward 0.5
            if current > 0.5:
                fair_yes = max(0.5, current - opportunity.edge)
            else:
                fair_yes = min(0.5, current + opportunity.edge)
            fair_no = 1.0 - fair_yes
            
        return fair_yes, fair_no