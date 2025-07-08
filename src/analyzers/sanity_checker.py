"""
Sanity checker for market predictions.

Validates predictions against common sense and market efficiency principles.
"""

import logging
from typing import Tuple, List, Optional
from dataclasses import dataclass

from src.clients.polymarket.models import Market

logger = logging.getLogger(__name__)


@dataclass
class SanityCheckResult:
    """Result of sanity check validation."""
    is_sane: bool
    warnings: List[str]
    adjusted_probability: Optional[float] = None
    confidence_penalty: float = 0.0


class SanityChecker:
    """
    Validates market predictions against reality checks.
    """
    
    def __init__(self):
        """Initialize sanity checker with thresholds."""
        self.max_deviation_from_market = 10.0  # Max 10x deviation
        self.extreme_probability_threshold = 0.05  # 5% or 95%
        self.merger_base_rate = 0.02  # 2% base rate for mergers
        
    def check_prediction(
        self,
        market: Market,
        predicted_probability: float,
        confidence: float,
        reasoning: str
    ) -> SanityCheckResult:
        """
        Perform sanity checks on a prediction.
        
        Args:
            market: The market being analyzed
            predicted_probability: Model's probability estimate
            confidence: Model's confidence level
            reasoning: Model's reasoning
            
        Returns:
            SanityCheckResult with warnings and adjustments
        """
        warnings = []
        confidence_penalty = 0.0
        adjusted_prob = predicted_probability
        
        # Get current market probability
        market_prob = self._get_market_probability(market)
        
        # Check 1: Extreme deviation from market
        if market_prob > 0:
            deviation = predicted_probability / market_prob
            if deviation > self.max_deviation_from_market:
                warnings.append(
                    f"Prediction ({predicted_probability:.1%}) is {deviation:.1f}x "
                    f"higher than market ({market_prob:.1%}). Consider market efficiency."
                )
                confidence_penalty += 0.3
                
        # Check 2: Merger-specific checks
        if self._is_merger_market(market):
            merger_warnings = self._check_merger_plausibility(market, predicted_probability)
            warnings.extend(merger_warnings)
            if merger_warnings:
                confidence_penalty += 0.2
                # Cap merger predictions at reasonable levels
                if predicted_probability > 0.1 and not self._has_merger_evidence(reasoning):
                    adjusted_prob = min(predicted_probability, 0.05)
                    warnings.append(
                        f"Capping merger probability at {adjusted_prob:.1%} without specific evidence"
                    )
                    
        # Check 3: Extreme probabilities without strong evidence
        if (predicted_probability < self.extreme_probability_threshold or 
            predicted_probability > (1 - self.extreme_probability_threshold)):
            if "limited news" in reasoning.lower() or "no news" in reasoning.lower():
                warnings.append(
                    "Extreme probability estimate with limited news coverage. "
                    "Consider reverting toward market consensus."
                )
                confidence_penalty += 0.4
                
        # Check 4: Time-based reality checks
        time_warnings = self._check_time_feasibility(market, predicted_probability)
        warnings.extend(time_warnings)
        if time_warnings:
            confidence_penalty += 0.2
            
        # Check 5: Liquidity warnings
        if market.volume and market.volume < 10000:
            warnings.append(
                f"Low market volume (${market.volume:,.0f}). "
                "Price may not reflect true probability."
            )
            
        # Determine if prediction passes sanity checks
        is_sane = len(warnings) == 0 or confidence_penalty < 0.5
        
        return SanityCheckResult(
            is_sane=is_sane,
            warnings=warnings,
            adjusted_probability=adjusted_prob if adjusted_prob != predicted_probability else None,
            confidence_penalty=min(confidence_penalty, 0.5)
        )
        
    def _get_market_probability(self, market: Market) -> float:
        """Extract YES probability from market."""
        for token in market.tokens:
            if token.outcome.upper() == "YES":
                return token.price or 0.5
        return 0.5
        
    def _is_merger_market(self, market: Market) -> bool:
        """Check if market is about a merger or acquisition."""
        keywords = ["merger", "merge", "acquisition", "acquire", "buyout", "combine"]
        text = f"{market.question} {market.description or ''}".lower()
        return any(keyword in text for keyword in keywords)
        
    def _check_merger_plausibility(self, market: Market, probability: float) -> List[str]:
        """Check if merger prediction is plausible."""
        warnings = []
        
        # Extract company names
        question = market.question.lower()
        
        # Check for unlikely combinations
        unlikely_pairs = [
            ("x", "truth social"),  # Different owners, competing platforms
            ("google", "apple"),    # Major competitors
            ("tesla", "ford"),      # Unlikely combination
        ]
        
        for company1, company2 in unlikely_pairs:
            if company1 in question and company2 in question:
                if probability > 0.1:  # More than 10% for unlikely merger
                    warnings.append(
                        f"Merger between {company1.title()} and {company2.title()} "
                        f"is highly unlikely. Historical precedent suggests < 5% probability."
                    )
                break
                
        # Check timeline feasibility
        if "before" in question or "by" in question:
            import re
            from datetime import datetime, timedelta
            
            # Try to extract timeline
            months = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)', question)
            if months and market.end_date_iso:
                days_until = (market.end_date_iso - datetime.now()).days
                if days_until < 60 and probability > 0.2:
                    warnings.append(
                        f"Only {days_until} days until deadline. "
                        f"Major mergers typically take 6-12 months to announce."
                    )
                    
        return warnings
        
    def _has_merger_evidence(self, reasoning: str) -> bool:
        """Check if reasoning contains specific merger evidence."""
        evidence_keywords = [
            "announcement", "talks", "negotiations", "sources say",
            "reported", "considering", "exploring", "due diligence"
        ]
        reasoning_lower = reasoning.lower()
        return any(keyword in reasoning_lower for keyword in evidence_keywords)
        
    def _check_time_feasibility(self, market: Market, probability: float) -> List[str]:
        """Check if timeline makes sense for the predicted probability."""
        warnings = []
        
        if not market.end_date_iso:
            return warnings
            
        from datetime import datetime
        days_until = (market.end_date_iso - datetime.now()).days
        
        # Short timeline checks
        if days_until < 30:
            if self._is_merger_market(market) and probability > 0.15:
                warnings.append(
                    f"Only {days_until} days remaining. Complex corporate events "
                    f"rarely materialize this quickly without prior announcements."
                )
            elif "will reach" in market.question.lower() and probability > 0.8:
                # Price target markets
                warnings.append(
                    f"High probability ({probability:.1%}) for price target "
                    f"with only {days_until} days remaining. Consider volatility."
                )
                
        return warnings
        
    def generate_recommendation_warning(self, result: SanityCheckResult) -> Optional[str]:
        """Generate user-facing warning for problematic predictions."""
        if not result.warnings:
            return None
            
        warning_text = "⚠️ **Important Considerations:**\n\n"
        
        for warning in result.warnings[:3]:  # Show top 3 warnings
            warning_text += f"• {warning}\n"
            
        if result.adjusted_probability:
            warning_text += f"\n📊 Adjusted estimate: {result.adjusted_probability:.1%}"
            
        if result.confidence_penalty > 0.3:
            warning_text += "\n\n🔴 **High uncertainty** - Treat this prediction with caution."
            
        return warning_text