"""
High confidence opportunity analyzer.
Focuses on finding markets with strong directional conviction.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from src.clients.polymarket.models import Market, MarketPrice
from src.analyzers.simple_pattern_analyzer import SimpleOpportunity

logger = logging.getLogger(__name__)


class HighConfidenceAnalyzer:
    """
    Analyzer focused on high confidence opportunities only.
    """
    
    def __init__(self):
        self.min_edge = 0.10  # 10% minimum edge
        self.min_volume = 5000  # $5k minimum volume
        self.min_confidence = 0.7  # 70% minimum confidence
        
    def analyze_market(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Analyze for high confidence opportunities only."""
        
        if not self._basic_filters(market, price):
            return None
            
        # Try all high confidence patterns
        patterns = [
            self._check_near_certainties(market, price),
            self._check_near_impossibilities(market, price),
            self._check_stable_continuations(market, price),
            self._check_structural_certainties(market, price),
            self._check_extreme_mispricing(market, price),
        ]
        
        # Filter by minimum confidence
        opportunities = [p for p in patterns if p is not None and p.confidence >= self.min_confidence]
        
        if opportunities:
            # Return highest confidence
            opportunities.sort(key=lambda x: x.confidence * x.edge, reverse=True)
            return opportunities[0]
            
        return None
    
    def _basic_filters(self, market: Market, price: MarketPrice) -> bool:
        """Basic filters."""
        if not market.volume or market.volume < self.min_volume:
            return False
        if price.yes_price <= 0.01 or price.yes_price >= 0.99:
            return False
        return True
    
    def _check_near_certainties(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for near-certain events underpriced."""
        
        question = market.question.lower()
        
        # Near certainty patterns with expected probabilities
        certainty_patterns = [
            # Physical certainties
            ('sun rise', 0.9999, "Physical certainty"),
            ('earth continue', 0.9999, "Physical certainty"),
            ('gravity exist', 0.9999, "Physical law"),
            
            # Institutional continuity
            ('remain president until', 0.98, "Constitutional term"),
            ('complete their term', 0.97, "Historical precedent"),
            ('stay in office until', 0.97, "Term completion likely"),
            ('continue as ceo', 0.90, "CEO stability"),
            
            # Market continuity
            ('still be trading', 0.95, "Market persistence"),
            ('remain listed', 0.94, "Exchange listing stability"),
            ('continue operations', 0.92, "Business continuity"),
            
            # Regulatory persistence
            ('remain legal', 0.96, "Regulatory inertia"),
            ('stay regulated', 0.95, "Regulatory stability"),
            ('maintain license', 0.93, "License renewal likely"),
        ]
        
        for pattern, fair_prob, reason in certainty_patterns:
            if pattern in question and price.yes_price < fair_prob - 0.05:
                edge = fair_prob - price.yes_price
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_YES",
                    edge=edge,
                    confidence=0.85,
                    reason=f"{reason} - severely underpriced at {price.yes_price:.0%}",
                    pattern_type="NEAR_CERTAINTY"
                )
                
        return None
    
    def _check_near_impossibilities(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for near-impossible events overpriced."""
        
        question = market.question.lower()
        
        # Near impossibility patterns with expected probabilities
        impossibility_patterns = [
            # Constitutional/legal impossibilities
            ('constitutional amendment', 0.01, "Requires supermajority"),
            ('abolish the supreme court', 0.001, "Constitutional impossibility"),
            ('merge states', 0.001, "Constitutional prohibition"),
            ('third term', 0.001, "22nd Amendment"),
            ('dissolve congress', 0.001, "Separation of powers"),
            
            # Physical impossibilities
            ('faster than light', 0.0001, "Physics violation"),
            ('perpetual motion', 0.0001, "Thermodynamics violation"),
            ('time travel', 0.001, "Physical impossibility"),
            
            # Extreme financial events
            ('bankrupt the fed', 0.001, "Central bank impossibility"),
            ('dollar collapse to zero', 0.001, "Reserve currency stability"),
            ('stock market to zero', 0.001, "Market structure"),
            
            # Extreme records (context dependent)
            ('10x in one day', 0.001, "Trading halt mechanisms"),
            ('100% unanimous', 0.01, "Statistical impossibility"),
            ('zero votes', 0.001, "Democratic impossibility"),
        ]
        
        for pattern, fair_prob, reason in impossibility_patterns:
            if pattern in question and price.yes_price > fair_prob + 0.03:
                edge = price.yes_price - fair_prob
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=edge,
                    confidence=0.9,
                    reason=f"{reason} - overpriced at {price.yes_price:.0%}",
                    pattern_type="NEAR_IMPOSSIBILITY"
                )
                
        return None
    
    def _check_stable_continuations(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for stable continuation events."""
        
        question = market.question.lower()
        
        # Only for medium-term markets
        if market.end_date_iso:
            days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
            if days_left < 7 or days_left > 90:
                return None
        else:
            return None
            
        # Stable continuation patterns
        continuation_keywords = [
            'remain above', 'stay above', 'continue above',
            'remain below', 'stay below', 'continue below',
            'maintain', 'keep', 'hold', 'sustain'
        ]
        
        if any(keyword in question for keyword in continuation_keywords):
            # Check if it's about stable metrics
            if any(stable in question for stable in [
                'interest rate', 'inflation', 'unemployment',
                'approval rating', 'market share', 'price'
            ]):
                if 0.70 < price.yes_price < 0.85:
                    # Continuation likely but underpriced
                    edge = 0.88 - price.yes_price
                    return SimpleOpportunity(
                        market=market,
                        current_price=price.yes_price,
                        recommended_action="BUY_YES",
                        edge=edge,
                        confidence=0.75,
                        reason=f"Stable metric continuation likely ({days_left} days)",
                        pattern_type="STABLE_CONTINUATION"
                    )
                elif 0.15 < price.yes_price < 0.30:
                    # Discontinuation unlikely but overpriced
                    edge = price.yes_price - 0.12
                    return SimpleOpportunity(
                        market=market,
                        current_price=price.yes_price,
                        recommended_action="BUY_NO",
                        edge=edge,
                        confidence=0.75,
                        reason=f"Stable metric change unlikely ({days_left} days)",
                        pattern_type="STABLE_CONTINUATION"
                    )
                    
        return None
    
    def _check_structural_certainties(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for structural/mathematical certainties."""
        
        question = market.question.lower()
        
        # Mathematical/structural patterns
        if 'at least one' in question or 'any' in question:
            # "At least one" events with many trials
            if any(word in question for word in ['day', 'week', 'month', 'game']):
                if price.yes_price < 0.80:
                    edge = 0.90 - price.yes_price
                    return SimpleOpportunity(
                        market=market,
                        current_price=price.yes_price,
                        recommended_action="BUY_YES",
                        edge=edge,
                        confidence=0.8,
                        reason="Multiple independent trials increase probability",
                        pattern_type="STRUCTURAL_CERTAINTY"
                    )
                    
        # Mutually exclusive events
        if 'both' in question and any(word in question for word in ['and', 'same time']):
            if price.yes_price > 0.20:
                edge = price.yes_price - 0.10
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=edge,
                    confidence=0.75,
                    reason="Joint probability of independent events is low",
                    pattern_type="STRUCTURAL_CERTAINTY"
                )
                
        return None
    
    def _check_extreme_mispricing(
        self,
        market: Market,
        price: MarketPrice
    ) -> Optional[SimpleOpportunity]:
        """Check for extreme mispricings with high confidence."""
        
        question = market.question.lower()
        
        # Extreme longshots that should be < 1%
        extreme_patterns = [
            'reach $10 million', 'reach $100 million', 'reach $1 billion',
            '1000x', '10000x', 'trillion dollar',
            'all 50 states', 'every single', 'perfect record',
            'break all records', 'highest ever recorded',
            'lowest ever recorded', 'never before seen'
        ]
        
        for pattern in extreme_patterns:
            if pattern in question and 0.05 < price.yes_price < 0.20:
                edge = price.yes_price - 0.01
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_NO",
                    edge=edge,
                    confidence=0.85,
                    reason=f"Extreme event vastly overpriced at {price.yes_price:.0%}",
                    pattern_type="EXTREME_MISPRICING"
                )
                
        # Near certainties that should be > 95%
        certainty_patterns = [
            'at least one goal', 'at least one point',
            'at least one trade', 'at least one sale',
            'any rain', 'any snow' # (in appropriate season/location)
        ]
        
        for pattern in certainty_patterns:
            if pattern in question and 0.70 < price.yes_price < 0.90:
                edge = 0.96 - price.yes_price
                return SimpleOpportunity(
                    market=market,
                    current_price=price.yes_price,
                    recommended_action="BUY_YES",
                    edge=edge,
                    confidence=0.8,
                    reason=f"High probability event underpriced at {price.yes_price:.0%}",
                    pattern_type="EXTREME_MISPRICING"
                )
                
        return None
    
    def calculate_fair_value(
        self,
        opportunity: SimpleOpportunity
    ) -> Tuple[float, float]:
        """Calculate fair value for high confidence opportunities."""
        
        current = opportunity.current_price
        
        if opportunity.recommended_action == "BUY_YES":
            fair_yes = min(0.99, current + opportunity.edge)
            fair_no = 1.0 - fair_yes
        elif opportunity.recommended_action == "BUY_NO":
            fair_yes = max(0.01, current - opportunity.edge)
            fair_no = 1.0 - fair_yes
        else:
            if current > 0.5:
                fair_yes = max(0.5, current - opportunity.edge)
            else:
                fair_yes = min(0.5, current + opportunity.edge)
            fair_no = 1.0 - fair_yes
            
        return fair_yes, fair_no