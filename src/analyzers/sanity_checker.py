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
        
        # Industry-specific merger knowledge
        self.industry_merger_rates = {
            "tech": 0.15,      # Tech has higher merger activity
            "pharma": 0.12,    # Pharma consolidation common
            "finance": 0.08,   # Banking heavily regulated
            "energy": 0.06,    # Oil/gas sector consolidation
            "media": 0.10,     # Media consolidation trends
            "telecom": 0.05,   # Heavily regulated
            "defense": 0.03,   # National security concerns
            "social_media": 0.02  # Antitrust scrutiny
        }
        
        # Regulatory complexity by industry
        self.regulatory_hurdles = {
            "finance": ["CFTC", "SEC", "Fed", "FDIC"],
            "defense": ["CFIUS", "DoD", "export controls"],
            "telecom": ["FCC", "antitrust", "national security"],
            "media": ["FCC", "antitrust", "content ownership"],
            "social_media": ["FTC", "antitrust", "data privacy"]
        }
        
        # Companies with known antitrust scrutiny
        self.antitrust_targets = {
            "google", "apple", "amazon", "microsoft", "meta", "facebook",
            "x", "twitter", "tesla", "nvidia", "openai"
        }
        
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
        """Check if merger prediction is plausible with comprehensive domain knowledge."""
        warnings = []
        
        # Extract company names and context
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        # Enhanced unlikely combinations with reasoning
        unlikely_pairs = [
            ("x", "truth social", "Competing platforms with different ownership structures and user bases"),
            ("google", "apple", "Major competitors with overlapping products (antitrust concerns)"),
            ("tesla", "ford", "Different EV strategies and manufacturing philosophies"),
            ("microsoft", "apple", "Historical rivals with competing ecosystems"),
            ("amazon", "google", "Cloud computing competitors (AWS vs GCP)"),
            ("meta", "x", "Direct social media competitors under antitrust scrutiny"),
            ("openai", "google", "AI competition and existing Google AI investments"),
            ("netflix", "disney", "Streaming competitors with content conflicts")
        ]
        
        for company1, company2, reason in unlikely_pairs:
            if company1 in full_text and company2 in full_text:
                if probability > 0.1:  # More than 10% for unlikely merger
                    warnings.append(
                        f"Merger between {company1.title()} and {company2.title()} "
                        f"is highly unlikely. {reason}. Historical precedent < 3%."
                    )
                break
        
        # Check for antitrust scrutiny
        antitrust_warnings = self._check_antitrust_concerns(full_text, probability)
        warnings.extend(antitrust_warnings)
        
        # Industry-specific checks
        industry_warnings = self._check_industry_feasibility(full_text, probability)
        warnings.extend(industry_warnings)
        
        # Market cap compatibility (if we can infer)
        size_warnings = self._check_size_compatibility(full_text, probability)
        warnings.extend(size_warnings)
                
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
    
    def _check_antitrust_concerns(self, text: str, probability: float) -> List[str]:
        """Check for potential antitrust issues."""
        warnings = []
        
        # Count antitrust-sensitive companies
        antitrust_count = sum(1 for company in self.antitrust_targets if company in text)
        
        if antitrust_count >= 2 and probability > 0.15:
            warnings.append(
                "Multiple companies under antitrust scrutiny. "
                "Regulatory approval highly unlikely in current environment."
            )
        elif antitrust_count >= 1 and probability > 0.25:
            warnings.append(
                "Involves company under antitrust scrutiny. "
                "Recent regulatory environment suggests <10% approval chance."
            )
            
        # Check for market dominance keywords
        dominance_keywords = ["monopoly", "market share", "dominant", "competition"]
        if any(keyword in text for keyword in dominance_keywords) and probability > 0.2:
            warnings.append(
                "Market dominance concerns mentioned. "
                "Antitrust review would likely block merger."
            )
            
        return warnings
    
    def _check_industry_feasibility(self, text: str, probability: float) -> List[str]:
        """Check industry-specific merger feasibility."""
        warnings = []
        
        # Identify industry
        industry = self._identify_industry(text)
        
        if industry:
            base_rate = self.industry_merger_rates.get(industry, self.merger_base_rate)
            
            # Adjust probability expectations based on industry
            if probability > base_rate * 3:  # 3x industry average
                warnings.append(
                    f"{industry.title()} industry historical merger rate: {base_rate:.1%}. "
                    f"Prediction {probability:.1%} is {probability/base_rate:.1f}x higher than typical."
                )
                
            # Industry-specific regulatory warnings
            if industry in self.regulatory_hurdles:
                regulators = ", ".join(self.regulatory_hurdles[industry])
                if probability > 0.3:
                    warnings.append(
                        f"{industry.title()} mergers require approval from: {regulators}. "
                        f"Complex regulatory process reduces probability."
                    )
                    
        return warnings
    
    def _check_size_compatibility(self, text: str, probability: float) -> List[str]:
        """Check if company sizes are compatible for merger."""
        warnings = []
        
        # Large company indicators
        large_company_indicators = [
            "trillion dollar", "fortune 500", "s&p 500", "nasdaq 100",
            "big tech", "faang", "megacap"
        ]
        
        # Small company indicators  
        small_company_indicators = [
            "startup", "series", "funding", "venture", "private",
            "small cap", "penny stock"
        ]
        
        has_large = any(indicator in text for indicator in large_company_indicators)
        has_small = any(indicator in text for indicator in small_company_indicators)
        
        if has_large and has_small and probability > 0.4:
            warnings.append(
                "Significant size mismatch between companies. "
                "Large acquisitions of small companies more likely than mergers."
            )
            
        # Equal-size merger challenges
        if "merger of equals" in text and probability > 0.25:
            warnings.append(
                "Merger of equals historically has <20% success rate. "
                "Cultural integration and governance challenges are significant."
            )
            
        return warnings
    
    def _identify_industry(self, text: str) -> Optional[str]:
        """Identify industry from text."""
        industry_keywords = {
            "tech": ["technology", "software", "ai", "cloud", "saas", "platform"],
            "pharma": ["pharmaceutical", "drug", "biotech", "medicine", "clinical"],
            "finance": ["bank", "financial", "credit", "loan", "investment", "fintech"],
            "energy": ["oil", "gas", "energy", "renewable", "solar", "wind"],
            "media": ["media", "entertainment", "streaming", "content", "film", "tv"],
            "telecom": ["telecom", "wireless", "network", "broadband", "5g"],
            "defense": ["defense", "military", "aerospace", "weapons", "security"],
            "social_media": ["social media", "social network", "platform", "x", "twitter", "facebook"]
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text for keyword in keywords):
                return industry
                
        return None