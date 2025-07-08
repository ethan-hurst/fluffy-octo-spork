"""
Bayesian probability updating for sophisticated fair value calculation.
"""

import math
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Types of evidence for Bayesian updating."""
    NEWS_SENTIMENT = "news_sentiment"
    POLLING_DATA = "polling_data"
    MARKET_BEHAVIOR = "market_behavior"
    TIME_DECAY = "time_decay"
    EXPERT_OPINION = "expert_opinion"
    SOCIAL_SENTIMENT = "social_sentiment"


@dataclass
class Evidence:
    """Single piece of evidence for Bayesian updating."""
    evidence_type: EvidenceType
    likelihood_ratio: float  # P(evidence|hypothesis_true) / P(evidence|hypothesis_false)
    confidence: float  # 0-1, how reliable this evidence is
    weight: float  # How much to trust this evidence type for this market
    description: str
    source: str = "unknown"


@dataclass
class ProbabilityDistribution:
    """Represents a probability with uncertainty."""
    mean: float
    std_dev: float
    confidence_interval: Tuple[float, float]
    sample_size: int = 100
    
    @property
    def lower_bound(self) -> float:
        return self.confidence_interval[0]
    
    @property
    def upper_bound(self) -> float:
        return self.confidence_interval[1]
    
    @property
    def uncertainty(self) -> float:
        """How uncertain we are (width of confidence interval)."""
        return self.upper_bound - self.lower_bound


class BayesianUpdater:
    """
    Sophisticated Bayesian probability updating system.
    """
    
    def __init__(self):
        """Initialize the Bayesian updater."""
        self.evidence_weights = self._load_evidence_weights()
        
    def update_probability(
        self, 
        prior: float, 
        evidence_list: List[Evidence],
        market_type: str = "general"
    ) -> ProbabilityDistribution:
        """
        Update probability using Bayesian inference with multiple pieces of evidence.
        
        Args:
            prior: Prior probability (0-1)
            evidence_list: List of evidence to incorporate
            market_type: Type of market for context-specific weighting
            
        Returns:
            ProbabilityDistribution: Updated probability with uncertainty
        """
        if not evidence_list:
            return self._create_distribution_from_point(prior, confidence=0.3)
            
        # Start with prior odds
        prior_odds = self._probability_to_odds(prior)
        
        # Apply each piece of evidence using Bayes' theorem
        posterior_odds = prior_odds
        total_weight = 0.0
        evidence_contributions = []
        
        for evidence in evidence_list:
            # Adjust likelihood ratio based on confidence and market-specific weights
            adjusted_lr = self._adjust_likelihood_ratio(
                evidence, market_type
            )
            
            # Update odds: P(H|E) = P(E|H) / P(E|~H) * P(H) / P(~H)
            posterior_odds *= adjusted_lr
            
            # Track contributions for uncertainty calculation
            weight = evidence.confidence * evidence.weight
            evidence_contributions.append({
                'type': evidence.evidence_type,
                'contribution': adjusted_lr,
                'weight': weight,
                'description': evidence.description
            })
            total_weight += weight
            
        # Convert back to probability
        posterior_prob = self._odds_to_probability(posterior_odds)
        
        # Calculate uncertainty based on evidence quality and consistency
        uncertainty = self._calculate_uncertainty(
            prior, posterior_prob, evidence_list, evidence_contributions
        )
        
        # Create confidence interval
        ci_lower, ci_upper = self._calculate_confidence_interval(
            posterior_prob, uncertainty
        )
        
        return ProbabilityDistribution(
            mean=posterior_prob,
            std_dev=uncertainty,
            confidence_interval=(ci_lower, ci_upper),
            sample_size=len(evidence_list) * 10  # Rough approximation
        )
        
    def _probability_to_odds(self, prob: float) -> float:
        """Convert probability to odds ratio."""
        prob = max(0.001, min(0.999, prob))  # Avoid division by zero
        return prob / (1 - prob)
        
    def _odds_to_probability(self, odds: float) -> float:
        """Convert odds ratio to probability."""
        return odds / (1 + odds)
        
    def _adjust_likelihood_ratio(self, evidence: Evidence, market_type: str) -> float:
        """
        Adjust likelihood ratio based on evidence confidence and market-specific weights.
        """
        base_lr = evidence.likelihood_ratio
        
        # Get market-specific weight for this evidence type
        market_weight = self.evidence_weights.get(market_type, {}).get(
            evidence.evidence_type.value, 1.0
        )
        
        # Adjust towards 1.0 (no effect) based on confidence
        # Low confidence evidence should have less impact
        confidence_adjustment = evidence.confidence * evidence.weight * market_weight
        
        # Interpolate between 1.0 (no effect) and the full likelihood ratio
        adjusted_lr = 1.0 + confidence_adjustment * (base_lr - 1.0)
        
        # Ensure we don't create extreme odds
        return max(0.1, min(10.0, adjusted_lr))
        
    def _calculate_uncertainty(
        self, 
        prior: float, 
        posterior: float, 
        evidence_list: List[Evidence],
        contributions: List[Dict]
    ) -> float:
        """
        Calculate uncertainty in the posterior probability.
        """
        # Base uncertainty depends on how much we updated from prior
        update_magnitude = abs(posterior - prior)
        
        # More evidence generally reduces uncertainty
        evidence_quality = sum(e.confidence * e.weight for e in evidence_list) / len(evidence_list)
        
        # Check consistency of evidence
        consistency = self._calculate_evidence_consistency(contributions)
        
        # Calculate uncertainty components
        base_uncertainty = 0.15  # Base epistemic uncertainty
        update_uncertainty = update_magnitude * 0.3  # Uncertainty from large updates
        evidence_uncertainty = (1.0 - evidence_quality) * 0.2  # Uncertainty from low-quality evidence
        consistency_uncertainty = (1.0 - consistency) * 0.25  # Uncertainty from conflicting evidence
        
        total_uncertainty = math.sqrt(
            base_uncertainty**2 + 
            update_uncertainty**2 + 
            evidence_uncertainty**2 + 
            consistency_uncertainty**2
        )
        
        return min(0.4, total_uncertainty)  # Cap at 40% uncertainty
        
    def _calculate_evidence_consistency(self, contributions: List[Dict]) -> float:
        """
        Calculate how consistent the evidence is (0-1, higher is more consistent).
        """
        if len(contributions) <= 1:
            return 1.0
            
        # Look at how much each piece of evidence agrees
        contributions_values = [c['contribution'] for c in contributions]
        
        # Calculate variance in log-space (since these are ratios)
        log_contributions = [math.log(max(0.01, c)) for c in contributions_values]
        mean_log = sum(log_contributions) / len(log_contributions)
        variance = sum((x - mean_log)**2 for x in log_contributions) / len(log_contributions)
        
        # Convert variance to consistency score (lower variance = higher consistency)
        consistency = math.exp(-variance)
        return max(0.1, min(1.0, consistency))
        
    def _calculate_confidence_interval(
        self, 
        probability: float, 
        uncertainty: float, 
        confidence_level: float = 0.68
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for the probability estimate.
        """
        # Use normal approximation for confidence interval
        # (This is a simplification - could use Beta distribution for more accuracy)
        z_score = 1.0  # For 68% confidence interval (≈ 1 standard deviation)
        
        margin = z_score * uncertainty
        lower = max(0.001, probability - margin)
        upper = min(0.999, probability + margin)
        
        return (lower, upper)
        
    def _create_distribution_from_point(
        self, 
        probability: float, 
        confidence: float = 0.5
    ) -> ProbabilityDistribution:
        """Create a probability distribution from a point estimate."""
        uncertainty = (1.0 - confidence) * 0.3  # Higher confidence = lower uncertainty
        ci_lower, ci_upper = self._calculate_confidence_interval(probability, uncertainty)
        
        return ProbabilityDistribution(
            mean=probability,
            std_dev=uncertainty,
            confidence_interval=(ci_lower, ci_upper),
            sample_size=10
        )
        
    def combine_independent_estimates(
        self, 
        estimates: List[ProbabilityDistribution],
        weights: Optional[List[float]] = None
    ) -> ProbabilityDistribution:
        """
        Combine multiple independent probability estimates using inverse variance weighting.
        """
        if not estimates:
            raise ValueError("No estimates provided")
            
        if len(estimates) == 1:
            return estimates[0]
            
        if weights is None:
            weights = [1.0] * len(estimates)
            
        # Use inverse variance weighting (more certain estimates get higher weight)
        inverse_variances = [1.0 / (est.std_dev**2 + 0.001) for est in estimates]
        total_inverse_var = sum(inv_var * weight for inv_var, weight in zip(inverse_variances, weights))
        
        # Weighted average of means
        weighted_mean = sum(
            est.mean * inv_var * weight 
            for est, inv_var, weight in zip(estimates, inverse_variances, weights)
        ) / total_inverse_var
        
        # Combined uncertainty (inverse variance formula)
        combined_variance = 1.0 / total_inverse_var
        combined_std = math.sqrt(combined_variance)
        
        # Calculate new confidence interval
        ci_lower, ci_upper = self._calculate_confidence_interval(weighted_mean, combined_std)
        
        return ProbabilityDistribution(
            mean=weighted_mean,
            std_dev=combined_std,
            confidence_interval=(ci_lower, ci_upper),
            sample_size=sum(est.sample_size for est in estimates)
        )
        
    def _load_evidence_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Load market-specific weights for different types of evidence.
        """
        return {
            "political": {
                "polling_data": 1.5,
                "news_sentiment": 0.8,
                "social_sentiment": 0.6,
                "expert_opinion": 1.2,
                "market_behavior": 1.0,
                "time_decay": 0.9
            },
            "crypto": {
                "market_behavior": 1.4,
                "news_sentiment": 1.1,
                "social_sentiment": 1.0,
                "expert_opinion": 0.8,
                "time_decay": 1.2
            },
            "sports": {
                "expert_opinion": 1.3,
                "news_sentiment": 1.0,
                "market_behavior": 1.1,
                "social_sentiment": 0.7,
                "time_decay": 0.8
            },
            "general": {
                "news_sentiment": 1.0,
                "market_behavior": 1.0,
                "expert_opinion": 1.0,
                "social_sentiment": 0.8,
                "time_decay": 1.0
            }
        }
        
    def create_evidence(
        self,
        evidence_type: EvidenceType,
        positive_signal: bool,
        strength: float,
        confidence: float,
        description: str,
        source: str = "unknown"
    ) -> Evidence:
        """
        Helper to create Evidence objects with proper likelihood ratios.
        
        Args:
            evidence_type: Type of evidence
            positive_signal: True if evidence supports the hypothesis
            strength: How strong the signal is (0-1)
            confidence: How confident we are in this evidence (0-1)
            description: Human-readable description
            source: Source of the evidence
            
        Returns:
            Evidence object
        """
        # Convert strength and direction to likelihood ratio
        if positive_signal:
            # Positive evidence: makes hypothesis more likely
            likelihood_ratio = 1.0 + strength * 3.0  # 1.0 to 4.0 range
        else:
            # Negative evidence: makes hypothesis less likely
            likelihood_ratio = 1.0 / (1.0 + strength * 3.0)  # 0.25 to 1.0 range
            
        return Evidence(
            evidence_type=evidence_type,
            likelihood_ratio=likelihood_ratio,
            confidence=confidence,
            weight=1.0,  # Default weight, can be adjusted
            description=description,
            source=source
        )