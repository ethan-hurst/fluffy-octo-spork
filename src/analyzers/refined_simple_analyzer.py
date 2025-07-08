"""
Refined simple pattern analyzer with better validation.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.clients.polymarket.models import Market, MarketPrice
from src.analyzers.simple_pattern_analyzer import SimpleOpportunity

logger = logging.getLogger(__name__)


class RefinedSimpleAnalyzer:
    """
    Refined version that avoids false positives.
    """
    
    def __init__(self):
        self.min_edge = 0.10
        self.min_volume = 10000
        
        # Patterns to AVOID for time decay
        self.volatile_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto',
            'stock', 'price', '$', 'nasdaq', 's&p',
            'meme', 'viral', 'twitter', 'tiktok'
        ]
        
        # Patterns GOOD for time decay
        self.stable_keywords = [
            'game', 'match', 'vs', 'versus', 'beat',
            'election', 'vote', 'win', 'championship',
            'season', 'series', 'finals', 'bowl'
        ]
        
    def analyze_market(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Analyze with better validation."""
        
        if not self._basic_filters(market, price):
            return None
            
        question_lower = market.question.lower()
        
        # Check time decay opportunity
        days_left = self._get_days_left(market)
        if days_left and 1 <= days_left <= 7:
            
            # AVOID volatile markets
            if any(keyword in question_lower for keyword in self.volatile_keywords):
                logger.debug(f"Skipping volatile market: {market.question[:50]}")
                return None
                
            # FOCUS on stable binary events
            if any(keyword in question_lower for keyword in self.stable_keywords):
                return self._analyze_stable_time_decay(market, price, days_left)
        
        # Check extreme mispricing (but be conservative)
        return self._check_extreme_mispricing(market, price)
    
    def _basic_filters(self, market: Market, price: MarketPrice) -> bool:
        """Basic filters."""
        if not market.volume or market.volume < self.min_volume:
            return False
        if price.yes_price <= 0.01 or price.yes_price >= 0.99:
            return False
        return True
    
    def _get_days_left(self, market: Market) -> Optional[int]:
        """Get days until resolution."""
        if not market.end_date_iso:
            return None
        days = (market.end_date_iso - datetime.now(timezone.utc)).days
        return days if days >= 0 else None
    
    def _analyze_stable_time_decay(
        self,
        market: Market,
        price: MarketPrice,
        days_left: int
    ) -> Optional[SimpleOpportunity]:
        """Analyze stable markets for time decay."""
        
        # For truly stable events, prices far from 50% are unlikely to move
        if 0.15 < price.yes_price < 0.35:
            # Low probability events tend to stay low
            edge = (0.35 - price.yes_price) * 0.5  # Conservative edge
            return SimpleOpportunity(
                market=market,
                current_price=price.yes_price,
                recommended_action="SELL_YES",
                edge=edge,
                confidence=0.7,
                reason=f"Stable event at {price.yes_price:.0%} with {days_left} days left",
                pattern_type="STABLE_TIME_DECAY"
            )
            
        elif 0.65 < price.yes_price < 0.85:
            # High probability events tend to stay high
            edge = (price.yes_price - 0.65) * 0.5
            return SimpleOpportunity(
                market=market,
                current_price=price.yes_price,
                recommended_action="SELL_NO",
                edge=edge,
                confidence=0.7,
                reason=f"Stable event at {price.yes_price:.0%} with {days_left} days left",
                pattern_type="STABLE_TIME_DECAY"
            )
            
        return None
    
    def _check_extreme_mispricing(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for obvious mispricings only."""
        
        question = market.question.lower()
        
        # Constitutional impossibilities
        if any(term in question for term in [
            'constitutional amendment', 'third term', 'abolish supreme court'
        ]):
            if price.yes_price > 0.10:
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=price.yes_price - 0.05,
                    confidence=0.9,
                    reason="Constitutional change nearly impossible",
                    pattern_type="EXTREME_MISPRICING"
                )
        
        # Already resolved events
        if any(term in question for term in ['already', 'has been', 'was']):
            # Need to be careful here - verify it's actually resolved
            pass
            
        return None
    
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