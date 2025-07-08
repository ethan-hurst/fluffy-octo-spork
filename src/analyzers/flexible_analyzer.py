"""
Flexible analyzer that adapts to current market conditions.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from src.clients.polymarket.models import Market, MarketPrice
from src.analyzers.simple_pattern_analyzer import SimpleOpportunity

logger = logging.getLogger(__name__)


class FlexibleAnalyzer:
    """
    More flexible analyzer that finds opportunities in current market conditions.
    """
    
    def __init__(self):
        self.min_edge = 0.08  # Lower threshold
        self.min_volume = 5000  # Lower volume requirement
        
    def analyze_market(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Analyze with flexible patterns."""
        
        if not self._basic_filters(market, price):
            return None
            
        # Try multiple patterns
        patterns = [
            self._check_extreme_low_longshots(market, price),
            self._check_medium_term_stability(market, price),
            self._check_high_confidence_events(market, price),
            self._check_binary_mispricing(market, price),
        ]
        
        # Return best opportunity
        opportunities = [p for p in patterns if p is not None]
        if opportunities:
            opportunities.sort(key=lambda x: x.edge * x.confidence, reverse=True)
            return opportunities[0]
            
        return None
    
    def _basic_filters(self, market: Market, price: MarketPrice) -> bool:
        """Basic filters."""
        if not market.volume or market.volume < self.min_volume:
            return False
        if price.yes_price <= 0.01 or price.yes_price >= 0.99:
            return False
        return True
    
    def _check_extreme_low_longshots(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for overpriced longshots."""
        
        # Markets priced 5-15% that are likely < 2%
        if 0.05 < price.yes_price < 0.15:
            question = market.question.lower()
            
            # Extreme longshot patterns
            if any(pattern in question for pattern in [
                'reach $1 million', '1000x', 'break all-time high',
                'world record', 'unanimous', 'sweep all',
                'perfect season', '100% accuracy', 'hottest year',
                'coldest year', 'most ever', 'least ever',
                'highest ever', 'lowest ever', 'record-breaking'
            ]):
                edge = price.yes_price - 0.02  # Assume 2% fair value
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=edge,
                    confidence=0.8,
                    reason=f"Extreme longshot overpriced at {price.yes_price:.0%}",
                    pattern_type="EXTREME_LONGSHOT"
                )
                
        return None
    
    def _check_medium_term_stability(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check medium-term stable events."""
        
        if not market.end_date_iso:
            return None
            
        days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
        
        # Medium term: 10-30 days
        if 10 <= days_left <= 30:
            question = market.question.lower()
            
            # Stable event types unlikely to change
            if any(pattern in question for pattern in [
                'remain', 'continue', 'stay', 'maintain',
                'will still', 'keep', 'hold'
            ]):
                if 0.70 < price.yes_price < 0.90:
                    # High probability of continuation
                    edge = 0.92 - price.yes_price  # Assume 92% fair value
                    return SimpleOpportunity(
                        market=market,
                        current_price=price.yes_price,
                        recommended_action="BUY_YES",
                        edge=edge,
                        confidence=0.7,
                        reason=f"Stable continuation event underpriced at {price.yes_price:.0%}",
                        pattern_type="STABLE_CONTINUATION"
                    )
                    
        return None
    
    def _check_high_confidence_events(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for high confidence mispricing."""
        
        question = market.question.lower()
        
        # Near impossibilities priced too high
        impossible_patterns = [
            ('constitutional amendment', 0.01),
            ('abolish the', 0.02),
            ('merge states', 0.01),
            ('change the flag', 0.02),
            ('rename the country', 0.01),
        ]
        
        for pattern, fair_value in impossible_patterns:
            if pattern in question and price.yes_price > fair_value + 0.05:
                edge = price.yes_price - fair_value
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=edge,
                    confidence=0.9,
                    reason=f"Near impossibility overpriced (fair value ~{fair_value:.0%})",
                    pattern_type="IMPOSSIBILITY"
                )
                
        return None
    
    def _check_binary_mispricing(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for binary event mispricing."""
        
        question = market.question.lower()
        
        # True 50/50 events
        if any(pattern in question for pattern in [
            'coin flip', 'coin toss', 'heads or tails',
            'odd or even', 'red or black'
        ]):
            distance_from_half = abs(price.yes_price - 0.5)
            if distance_from_half > 0.10:
                if price.yes_price > 0.5:
                    edge = price.yes_price - 0.52  # Small edge over 50%
                    action = "BUY_NO"
                else:
                    edge = 0.48 - price.yes_price
                    action = "BUY_YES"
                    
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action=action,
                    edge=edge,
                    confidence=0.9,
                    reason=f"True 50/50 event mispriced at {price.yes_price:.0%}",
                    pattern_type="BINARY_MISPRICING"
                )
                
        return None
    
    def calculate_fair_value(
        self,
        opportunity: SimpleOpportunity
    ) -> Tuple[float, float]:
        """Calculate fair value based on opportunity."""
        
        current = opportunity.current_price
        
        if opportunity.recommended_action == "BUY_YES":
            fair_yes = min(0.98, current + opportunity.edge)
            fair_no = 1.0 - fair_yes
        elif opportunity.recommended_action == "BUY_NO":
            fair_yes = max(0.02, current - opportunity.edge)
            fair_no = 1.0 - fair_yes
        else:
            if current > 0.5:
                fair_yes = max(0.5, current - opportunity.edge)
            else:
                fair_yes = min(0.5, current + opportunity.edge)
            fair_no = 1.0 - fair_yes
            
        return fair_yes, fair_no