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
        self.min_edge = 0.05  # Lower threshold to 5%
        self.min_volume = 1000  # Lower volume requirement to $1k
        
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
            self._check_overpriced_moderate_events(market, price),
            self._check_underpriced_high_probability(market, price),
            self._check_time_sensitive_opportunities(market, price),
            self._check_categorical_mispricings(market, price),
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
                'highest ever', 'lowest ever', 'record-breaking',
                'win every', 'lose every', 'zero', 'nobody',
                'everyone', 'all countries', 'every state',
                '100 million', '1 billion', 'trillion',
                'double', 'triple', 'quadruple'
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
    
    def _check_overpriced_moderate_events(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for overpriced moderate probability events."""
        
        # Markets priced 10-25% that might be overpriced
        if 0.10 < price.yes_price < 0.25:
            question = market.question.lower()
            
            # Unlikely patterns in this range
            if any(pattern in question for pattern in [
                'impeach', 'resign', 'quit', 'step down', 'fired',
                'collapse', 'crash', 'default', 'bankrupt',
                'war', 'attack', 'terrorist', 'pandemic',
                'revolution', 'overthrow', 'coup',
                'death', 'die', 'assassin'
            ]):
                edge = price.yes_price - 0.05  # These are usually ~5%
                if edge >= self.min_edge:
                    return SimpleOpportunity(
                        market=market,
                        current_price=price.yes_price,
                        recommended_action="BUY_NO",
                        edge=edge,
                        confidence=0.75,
                        reason=f"Dramatic event overpriced at {price.yes_price:.0%}",
                        pattern_type="OVERPRICED_MODERATE"
                    )
                    
        return None
    
    def _check_underpriced_high_probability(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for underpriced high probability events."""
        
        if 0.60 < price.yes_price < 0.80:
            question = market.question.lower()
            
            # High probability patterns
            if any(pattern in question for pattern in [
                'will the sun rise', 'will continue to exist',
                'at least one', 'at least 1', 'any',
                'more than zero', 'more than 0',
                'less than 100%', 'less than 100 percent',
                'between', 'range'
            ]):
                edge = 0.95 - price.yes_price
                if edge >= self.min_edge:
                    return SimpleOpportunity(
                        market=market,
                        current_price=price.yes_price,
                        recommended_action="BUY_YES",
                        edge=edge,
                        confidence=0.85,
                        reason=f"Near certainty underpriced at {price.yes_price:.0%}",
                        pattern_type="UNDERPRICED_HIGH"
                    )
                    
        return None
    
    def _check_time_sensitive_opportunities(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for time-sensitive opportunities."""
        
        if not market.end_date_iso:
            return None
            
        days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
        
        # Very short term (< 7 days) - status quo likely
        if days_left < 7 and days_left > 0:
            if 0.15 < price.yes_price < 0.40:
                question = market.question.lower()
                if any(pattern in question for pattern in [
                    'announce', 'release', 'launch', 'debut',
                    'happen', 'occur', 'take place'
                ]):
                    edge = price.yes_price - 0.10  # Unlikely in very short term
                    if edge >= self.min_edge:
                        return SimpleOpportunity(
                            market=market,
                            current_price=price.yes_price,
                            recommended_action="BUY_NO",
                            edge=edge,
                            confidence=0.70,
                            reason=f"Unlikely in {days_left} days",
                            pattern_type="TIME_SENSITIVE"
                        )
                        
        return None
    
    def _check_categorical_mispricings(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for category-specific mispricings."""
        
        question = market.question.lower()
        
        # Crypto/Bitcoin specific patterns
        if 'bitcoin' in question or 'btc' in question:
            if 'reach' in question and '$' in question:
                # Extract price target
                if '200,000' in question or '200k' in question:
                    if price.yes_price > 0.20:
                        edge = price.yes_price - 0.15
                        if edge >= self.min_edge:
                            return SimpleOpportunity(
                                market=market,
                                current_price=price.yes_price,
                                recommended_action="BUY_NO",
                                edge=edge,
                                confidence=0.70,
                                reason="BTC $200k unlikely in timeframe",
                                pattern_type="CRYPTO_OVERPRICED"
                            )
                            
        # Sports patterns
        elif any(sport in question for sport in ['nfl', 'nba', 'championship', 'super bowl']):
            if 'undefeated' in question or 'perfect season' in question:
                if price.yes_price > 0.05:
                    edge = price.yes_price - 0.02
                    if edge >= self.min_edge:
                        return SimpleOpportunity(
                            market=market,
                            current_price=price.yes_price,
                            recommended_action="BUY_NO",
                            edge=edge,
                            confidence=0.85,
                            reason="Perfect seasons extremely rare",
                            pattern_type="SPORTS_LONGSHOT"
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