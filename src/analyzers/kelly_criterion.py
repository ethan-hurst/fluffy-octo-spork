"""
Kelly Criterion implementation for optimal position sizing.

The Kelly Criterion calculates the optimal fraction of bankroll to wager
to maximize long-term growth while minimizing risk of ruin.
"""

import math
from typing import Tuple, Optional
from dataclasses import dataclass

from src.clients.polymarket.models import Market


@dataclass
class KellyResult:
    """Result of Kelly Criterion calculation."""
    
    # Basic Kelly calculation
    kelly_fraction: float  # Optimal fraction of bankroll to bet
    expected_value: float  # Expected value of the bet
    win_probability: float  # Probability of winning
    lose_probability: float  # Probability of losing
    
    # Odds and payouts
    odds_if_win: float  # Payout odds if bet wins
    odds_if_lose: float  # Loss if bet loses (typically -1.0)
    
    # Risk metrics
    probability_of_ruin: float  # Risk of losing entire bankroll
    expected_growth_rate: float  # Expected logarithmic growth
    
    # Recommendations
    recommended_fraction: float  # Conservative recommendation
    max_bankroll_fraction: float  # Maximum ever recommended
    recommendation: str  # Human-readable recommendation
    
    # Warnings
    warnings: list[str]  # Risk warnings


class KellyCriterion:
    """
    Calculate optimal position sizing using Kelly Criterion.
    
    The Kelly Criterion maximizes long-term growth by optimizing the fraction
    of bankroll to wager based on the probability and payoff of favorable bets.
    """
    
    def __init__(self):
        """Initialize Kelly calculator with safety parameters."""
        self.max_kelly_fraction = 0.25  # Never bet more than 25% of bankroll
        self.min_edge_required = 0.05   # Require 5% edge minimum
        self.confidence_adjustment = True  # Reduce bet size for low confidence
        
    def calculate(
        self,
        market: Market,
        predicted_probability: float,
        confidence: float,
        recommended_position: str
    ) -> KellyResult:
        """
        Calculate Kelly Criterion for a market position.
        
        Args:
            market: Market to analyze
            predicted_probability: Model's probability estimate
            confidence: Model's confidence level (0-1)
            recommended_position: "YES" or "NO"
            
        Returns:
            KellyResult: Complete Kelly analysis
        """
        # Get market probabilities and prices
        if recommended_position == "YES":
            market_price = self._get_yes_price(market)
            win_prob = predicted_probability
        else:
            market_price = self._get_no_price(market)  
            win_prob = 1.0 - predicted_probability
            
        lose_prob = 1.0 - win_prob
        
        # Calculate odds and payouts
        # In prediction markets: if you pay $0.60 for a $1 token, you win $0.40 profit if correct
        if market_price <= 0 or market_price >= 1:
            return self._create_no_bet_result("Invalid market price", win_prob, lose_prob)
            
        odds_if_win = (1.0 - market_price) / market_price  # Profit/stake ratio
        odds_if_lose = -1.0  # Lose entire stake
        
        # Calculate expected value
        expected_value = (win_prob * odds_if_win) + (lose_prob * odds_if_lose)
        
        # Basic Kelly formula: f* = (bp - q) / b
        # where b = odds if win, p = win probability, q = lose probability
        if odds_if_win <= 0:
            return self._create_no_bet_result("No positive odds", win_prob, lose_prob)
            
        kelly_fraction = (win_prob * odds_if_win - lose_prob) / odds_if_win
        
        # Expected growth rate (log utility)
        if kelly_fraction > 0 and kelly_fraction < 1:
            expected_growth = (
                win_prob * math.log(1 + kelly_fraction * odds_if_win) +
                lose_prob * math.log(1 - kelly_fraction)
            )
        else:
            expected_growth = float('-inf') if kelly_fraction >= 1 else expected_value
            
        # Risk of ruin calculation (simplified)
        probability_of_ruin = self._calculate_ruin_probability(
            kelly_fraction, win_prob, odds_if_win
        )
        
        # Apply safety adjustments
        recommended_fraction, warnings = self._apply_safety_adjustments(
            kelly_fraction, expected_value, confidence, win_prob, market_price
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            recommended_fraction, expected_value, win_prob
        )
        
        return KellyResult(
            kelly_fraction=kelly_fraction,
            expected_value=expected_value,
            win_probability=win_prob,
            lose_probability=lose_prob,
            odds_if_win=odds_if_win,
            odds_if_lose=odds_if_lose,
            probability_of_ruin=probability_of_ruin,
            expected_growth_rate=expected_growth,
            recommended_fraction=recommended_fraction,
            max_bankroll_fraction=self.max_kelly_fraction,
            recommendation=recommendation,
            warnings=warnings
        )
        
    def _get_yes_price(self, market: Market) -> float:
        """Get YES token price from market."""
        for token in market.tokens:
            if token.outcome.upper() == "YES":
                return token.price or 0.5
        return 0.5
        
    def _get_no_price(self, market: Market) -> float:
        """Get NO token price from market."""
        for token in market.tokens:
            if token.outcome.upper() == "NO":
                return token.price or 0.5
        return 0.5
        
    def _calculate_ruin_probability(
        self, 
        kelly_fraction: float, 
        win_prob: float, 
        odds_if_win: float
    ) -> float:
        """
        Calculate probability of ruin using gambler's ruin formula.
        
        This is a simplified calculation - real ruin probability depends
        on many factors including bet sequence and stopping rules.
        """
        if kelly_fraction <= 0:
            return 0.0
        if kelly_fraction >= 1:
            return 1.0
            
        # Simplified model: probability that a series of bets leads to ruin
        # Higher Kelly fractions = higher ruin risk
        lose_prob = 1.0 - win_prob
        
        if win_prob <= 0.5:
            return 1.0  # Negative edge = certain ruin
            
        # Use approximation for geometric Brownian motion
        # Real calculation would require more sophisticated modeling
        base_ruin_rate = lose_prob / win_prob
        kelly_multiplier = kelly_fraction * 2  # Higher fractions = more risk
        
        return min(0.9, base_ruin_rate * kelly_multiplier)
        
    def _apply_safety_adjustments(
        self,
        kelly_fraction: float,
        expected_value: float,
        confidence: float,
        win_prob: float,
        market_price: float
    ) -> Tuple[float, list[str]]:
        """Apply safety adjustments to reduce risk."""
        warnings = []
        adjusted_fraction = kelly_fraction
        
        # Rule 1: Never bet on negative expected value
        if expected_value <= 0:
            warnings.append(f"Negative expected value ({expected_value:.1%}). Recommended: DO NOT BET")
            return 0.0, warnings
            
        # Rule 2: Require minimum edge
        edge = expected_value
        if edge < self.min_edge_required:
            warnings.append(f"Edge too small ({edge:.1%} < {self.min_edge_required:.1%}). Recommended: SKIP")
            return 0.0, warnings
            
        # Rule 3: Confidence adjustment
        if self.confidence_adjustment and confidence < 0.8:
            confidence_multiplier = confidence / 0.8
            adjusted_fraction *= confidence_multiplier
            warnings.append(f"Low confidence ({confidence:.1%}). Reducing bet size by {1-confidence_multiplier:.1%}")
            
        # Rule 4: Cap maximum fraction
        if adjusted_fraction > self.max_kelly_fraction:
            warnings.append(f"Capping bet at {self.max_kelly_fraction:.1%} of bankroll (Kelly suggested {adjusted_fraction:.1%})")
            adjusted_fraction = self.max_kelly_fraction
            
        # Rule 5: Extreme long-shot warning
        if market_price < 0.05:  # Less than 5%
            warnings.append("Extreme long-shot bet. Consider that market may be efficient.")
            adjusted_fraction *= 0.5  # Reduce by half
            
        # Rule 6: Low probability warning
        if win_prob < 0.3:  # Less than 30% chance
            warnings.append(f"Low win probability ({win_prob:.1%}). High risk of total loss.")
            
        # Rule 7: Very high Kelly warning
        if kelly_fraction > 0.5:
            warnings.append("Very high Kelly fraction suggests extreme confidence. Consider model uncertainty.")
            
        return max(0.0, adjusted_fraction), warnings
        
    def _generate_recommendation(
        self, 
        recommended_fraction: float, 
        expected_value: float,
        win_probability: float
    ) -> str:
        """Generate human-readable recommendation."""
        if recommended_fraction <= 0:
            return "DO NOT BET"
        elif recommended_fraction < 0.01:  # Less than 1%
            return "VERY SMALL POSITION (< 1% bankroll)"
        elif recommended_fraction < 0.05:  # Less than 5%
            return "SMALL POSITION (1-5% bankroll)"
        elif recommended_fraction < 0.15:  # Less than 15%
            return "MODERATE POSITION (5-15% bankroll)"
        elif recommended_fraction < 0.25:  # Less than 25%
            return "LARGE POSITION (15-25% bankroll)"
        else:
            return "MAXIMUM POSITION (25% bankroll limit)"
            
    def _create_no_bet_result(
        self, 
        reason: str, 
        win_prob: float, 
        lose_prob: float
    ) -> KellyResult:
        """Create result for situations where we shouldn't bet."""
        return KellyResult(
            kelly_fraction=0.0,
            expected_value=-1.0,  # Negative EV
            win_probability=win_prob,
            lose_probability=lose_prob,
            odds_if_win=0.0,
            odds_if_lose=-1.0,
            probability_of_ruin=0.0,
            expected_growth_rate=0.0,
            recommended_fraction=0.0,
            max_bankroll_fraction=self.max_kelly_fraction,
            recommendation="DO NOT BET",
            warnings=[reason]
        )
        
    def format_analysis(self, result: KellyResult) -> str:
        """Format Kelly analysis for display."""
        lines = []
        
        lines.append("📊 **Kelly Criterion Analysis:**")
        lines.append("")
        
        # Basic metrics
        lines.append(f"• Win Probability: {result.win_probability:.1%}")
        lines.append(f"• Expected Value: {result.expected_value:.1%}")
        lines.append(f"• Kelly Fraction: {result.kelly_fraction:.1%}")
        lines.append("")
        
        # Recommendation
        if result.recommended_fraction > 0:
            lines.append(f"💰 **Recommended Position: {result.recommended_fraction:.1%} of bankroll**")
            lines.append(f"📈 Position Size: {result.recommendation}")
        else:
            lines.append("🚫 **Recommendation: DO NOT BET**")
        lines.append("")
        
        # Risk metrics
        lines.append("⚠️ **Risk Assessment:**")
        lines.append(f"• Probability of Ruin: {result.probability_of_ruin:.1%}")
        lines.append(f"• Chance of Total Loss: {result.lose_probability:.1%}")
        
        # Warnings
        if result.warnings:
            lines.append("")
            lines.append("🔴 **Warnings:**")
            for warning in result.warnings:
                lines.append(f"• {warning}")
                
        return "\n".join(lines)