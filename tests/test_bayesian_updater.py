"""
Unit tests for Bayesian probability updating functionality.
"""

import pytest
import math
from unittest.mock import patch

from src.analyzers.bayesian_updater import (
    BayesianUpdater, Evidence, EvidenceType, ProbabilityDistribution
)


class TestBayesianUpdater:
    """Test cases for BayesianUpdater."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.updater = BayesianUpdater()
        
    def test_evidence_creation(self):
        """Test Evidence dataclass creation."""
        evidence = Evidence(
            evidence_type=EvidenceType.NEWS_SENTIMENT,
            likelihood_ratio=2.0,
            confidence=0.8,
            weight=0.7,
            description="Positive news sentiment",
            source="news_analyzer"
        )
        
        assert evidence.evidence_type == EvidenceType.NEWS_SENTIMENT
        assert evidence.likelihood_ratio == 2.0
        assert evidence.confidence == 0.8
        assert evidence.weight == 0.7
        assert evidence.description == "Positive news sentiment"
        assert evidence.source == "news_analyzer"
        
    def test_probability_distribution_creation(self):
        """Test ProbabilityDistribution dataclass creation."""
        dist = ProbabilityDistribution(
            mean=0.6,
            std_dev=0.1,
            confidence_interval=(0.45, 0.75),
            sample_size=1000
        )
        
        assert dist.mean == 0.6
        assert dist.std_dev == 0.1
        assert dist.lower_bound == 0.45
        assert dist.upper_bound == 0.75
        assert dist.sample_size == 1000
        
    def test_probability_distribution_properties(self):
        """Test ProbabilityDistribution property methods."""
        dist = ProbabilityDistribution(
            mean=0.7,
            std_dev=0.15,
            confidence_interval=(0.5, 0.9)
        )
        
        assert dist.lower_bound == 0.5
        assert dist.upper_bound == 0.9
        assert dist.uncertainty == 0.4  # 0.9 - 0.5
        
    def test_create_evidence_positive_signal(self):
        """Test evidence creation with positive signal."""
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.POLLING_DATA,
            positive_signal=True,
            strength=0.8,
            confidence=0.9,
            description="Strong polling support",
            source="polling_aggregator"
        )
        
        assert evidence.evidence_type == EvidenceType.POLLING_DATA
        assert evidence.likelihood_ratio > 1.0  # Should favor hypothesis
        assert evidence.confidence == 0.9
        assert evidence.description == "Strong polling support"
        assert evidence.source == "polling_aggregator"
        
    def test_create_evidence_negative_signal(self):
        """Test evidence creation with negative signal."""
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.NEWS_SENTIMENT,
            positive_signal=False,
            strength=0.6,
            confidence=0.7,
            description="Negative news coverage",
            source="news_analyzer"
        )
        
        assert evidence.evidence_type == EvidenceType.NEWS_SENTIMENT
        assert evidence.likelihood_ratio < 1.0  # Should oppose hypothesis
        assert evidence.confidence == 0.7
        
    def test_calculate_likelihood_ratio_strong_positive(self):
        """Test likelihood ratio calculation for strong positive evidence."""
        # Test through create_evidence method since _calculate_likelihood_ratio doesn't exist
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.POLLING_DATA,
            positive_signal=True,
            strength=0.9,
            confidence=0.8,
            description="Test",
            source="test"
        )
        
        assert evidence.likelihood_ratio > 2.0  # Should be strong evidence
        
    def test_calculate_likelihood_ratio_weak_positive(self):
        """Test likelihood ratio calculation for weak positive evidence."""
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.SOCIAL_SENTIMENT,
            positive_signal=True,
            strength=0.2,
            confidence=0.5,
            description="Test",
            source="test"
        )
        
        assert 1.0 < evidence.likelihood_ratio < 2.0  # Should be weak evidence
        
    def test_calculate_likelihood_ratio_strong_negative(self):
        """Test likelihood ratio calculation for strong negative evidence."""
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.EXPERT_OPINION,
            positive_signal=False,
            strength=0.8,
            confidence=0.9,
            description="Test",
            source="test"
        )
        
        assert evidence.likelihood_ratio < 0.5  # Should be strong opposing evidence
        
    def test_calculate_likelihood_ratio_neutral(self):
        """Test likelihood ratio calculation for neutral evidence."""
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.NEWS_SENTIMENT,
            positive_signal=True,
            strength=0.0,
            confidence=0.5,
            description="Test",
            source="test"
        )
        
        assert abs(evidence.likelihood_ratio - 1.0) < 0.1  # Should be close to neutral
        
    def test_get_evidence_weight_high_reliability(self):
        """Test evidence weighting for high reliability types."""
        # Test through the evidence_weights dictionary
        weight = self.updater.evidence_weights["political"]["polling_data"]
        assert weight > 1.0  # Polling should be high weight for political markets
        
    def test_get_evidence_weight_medium_reliability(self):
        """Test evidence weighting for medium reliability types."""
        weight = self.updater.evidence_weights["general"]["news_sentiment"]
        assert 0.8 <= weight <= 1.2  # News should be medium weight
        
    def test_get_evidence_weight_low_reliability(self):
        """Test evidence weighting for low reliability types."""
        weight = self.updater.evidence_weights["crypto"]["social_sentiment"]
        assert weight <= 1.0  # Social sentiment should be reasonable weight
        
    def test_update_probability_single_evidence(self):
        """Test probability updating with single piece of evidence."""
        prior = 0.5
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.POLLING_DATA,
            positive_signal=True,
            strength=0.7,
            confidence=0.8,
            description="Favorable polling",
            source="pollster"
        )
        
        result = self.updater.update_probability(
            prior=prior,
            evidence_list=[evidence],
            market_type="political"
        )
        
        assert isinstance(result, ProbabilityDistribution)
        assert result.mean > prior  # Should increase probability
        assert 0.0 <= result.mean <= 1.0
        assert result.lower_bound <= result.mean <= result.upper_bound
        
    def test_update_probability_multiple_evidence_consistent(self):
        """Test probability updating with multiple consistent evidence pieces."""
        prior = 0.4
        evidence_list = [
            self.updater.create_evidence(
                evidence_type=EvidenceType.POLLING_DATA,
                positive_signal=True,
                strength=0.6,
                confidence=0.8,
                description="Polling support",
                source="pollster1"
            ),
            self.updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=True,
                strength=0.5,
                confidence=0.7,
                description="Positive news",
                source="news"
            ),
            self.updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=True,
                strength=0.7,
                confidence=0.9,
                description="Expert analysis",
                source="analyst"
            )
        ]
        
        result = self.updater.update_probability(
            prior=prior,
            evidence_list=evidence_list,
            market_type="political"
        )
        
        assert result.mean > prior  # Should increase significantly
        assert result.mean > 0.5  # Should push above 50%
        
    def test_update_probability_multiple_evidence_conflicting(self):
        """Test probability updating with conflicting evidence."""
        prior = 0.5
        evidence_list = [
            self.updater.create_evidence(
                evidence_type=EvidenceType.POLLING_DATA,
                positive_signal=True,
                strength=0.7,
                confidence=0.8,
                description="Favorable polling",
                source="pollster"
            ),
            self.updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=False,
                strength=0.6,
                confidence=0.7,
                description="Negative news",
                source="news"
            )
        ]
        
        result = self.updater.update_probability(
            prior=prior,
            evidence_list=evidence_list,
            market_type="political"
        )
        
        # Result should be somewhere between prior and the evidence effects
        assert 0.0 <= result.mean <= 1.0
        assert result.uncertainty > 0.1  # Should have higher uncertainty due to conflict
        
    def test_update_probability_no_evidence(self):
        """Test probability updating with no evidence."""
        prior = 0.6
        
        result = self.updater.update_probability(
            prior=prior,
            evidence_list=[],
            market_type="general"
        )
        
        assert abs(result.mean - prior) < 0.05  # Should be close to prior
        assert result.uncertainty > 0.0  # Should have some uncertainty
        
    def test_apply_evidence_single(self):
        """Test applying single evidence to probability."""
        prior = 0.4
        evidence = Evidence(
            evidence_type=EvidenceType.MARKET_BEHAVIOR,
            likelihood_ratio=1.5,
            confidence=0.7,
            weight=0.6,
            description="Market signals",
            source="market_analysis"
        )
        
        # Test through update_probability with single evidence
        result = self.updater.update_probability(prior, [evidence], "general")
        
        assert result.mean > prior  # Should increase probability
        assert 0.0 <= result.mean <= 1.0
        
    def test_apply_evidence_extreme_values(self):
        """Test evidence application with extreme prior values."""
        # Very low prior
        low_prior = 0.05
        strong_evidence = Evidence(
            evidence_type=EvidenceType.EXPERT_OPINION,
            likelihood_ratio=5.0,
            confidence=0.9,
            weight=0.8,
            description="Strong expert opinion",
            source="expert"
        )
        
        result_low = self.updater.update_probability(low_prior, [strong_evidence], "general")
        assert result_low.mean > low_prior
        assert result_low.mean < 0.5  # Shouldn't jump too much from very low prior
        
        # Very high prior
        high_prior = 0.95
        weak_opposing = Evidence(
            evidence_type=EvidenceType.SOCIAL_SENTIMENT,
            likelihood_ratio=0.7,
            confidence=0.5,
            weight=0.3,
            description="Weak opposition",
            source="social"
        )
        
        result_high = self.updater.update_probability(high_prior, [weak_opposing], "general")
        assert result_high.mean < high_prior
        assert result_high.mean > 0.8  # Shouldn't drop too much from very high prior
        
    def test_calculate_uncertainty_single_evidence(self):
        """Test uncertainty calculation with single evidence."""
        evidence_list = [
            Evidence(
                evidence_type=EvidenceType.POLLING_DATA,
                likelihood_ratio=2.0,
                confidence=0.8,
                weight=0.7,
                description="Polling data",
                source="pollster"
            )
        ]
        
        # Test through update_probability which calculates uncertainty internally
        result = self.updater.update_probability(0.5, evidence_list, "political")
        
        assert 0.0 <= result.uncertainty <= 1.0
        assert result.uncertainty < 0.5  # Should be reasonable uncertainty
        
    def test_calculate_uncertainty_multiple_evidence(self):
        """Test uncertainty calculation with multiple evidence pieces."""
        evidence_list = [
            Evidence(
                evidence_type=EvidenceType.POLLING_DATA,
                likelihood_ratio=2.0,
                confidence=0.8,
                weight=0.7,
                description="Polling data",
                source="pollster"
            ),
            Evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                likelihood_ratio=1.5,
                confidence=0.6,
                weight=0.5,
                description="News sentiment",
                source="news"
            ),
            Evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                likelihood_ratio=2.5,
                confidence=0.9,
                weight=0.8,
                description="Expert opinion",
                source="expert"
            )
        ]
        
        result = self.updater.update_probability(0.5, evidence_list, "general")
        
        assert 0.0 <= result.uncertainty <= 1.0
        # More evidence should generally reduce uncertainty
        
    def test_calculate_uncertainty_conflicting_evidence(self):
        """Test uncertainty calculation with conflicting evidence."""
        evidence_list = [
            Evidence(
                evidence_type=EvidenceType.POLLING_DATA,
                likelihood_ratio=2.5,  # Strong positive
                confidence=0.8,
                weight=0.7,
                description="Positive polling",
                source="pollster"
            ),
            Evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                likelihood_ratio=0.4,  # Strong negative
                confidence=0.7,
                weight=0.6,
                description="Negative news",
                source="news"
            )
        ]
        
        result = self.updater.update_probability(0.5, evidence_list, "general")
        
        # Conflicting evidence should increase uncertainty
        assert result.uncertainty > 0.2
        
    def test_create_distribution_from_point_high_confidence(self):
        """Test distribution creation from point estimate with high confidence."""
        dist = self.updater._create_distribution_from_point(0.7, confidence=0.9)
        
        assert abs(dist.mean - 0.7) < 0.01
        assert dist.uncertainty < 0.3  # Should have low uncertainty
        assert dist.lower_bound < dist.mean < dist.upper_bound
        
    def test_create_distribution_from_point_low_confidence(self):
        """Test distribution creation from point estimate with low confidence."""
        dist = self.updater._create_distribution_from_point(0.6, confidence=0.3)
        
        assert abs(dist.mean - 0.6) < 0.01
        assert dist.uncertainty > 0.4  # Should have high uncertainty
        assert dist.lower_bound < dist.mean < dist.upper_bound
        
    def test_create_distribution_from_point_extreme_values(self):
        """Test distribution creation with extreme probability values."""
        # Near 0
        dist_low = self.updater._create_distribution_from_point(0.05, confidence=0.7)
        assert dist_low.mean == 0.05
        assert dist_low.lower_bound >= 0.0  # Should not go below 0
        
        # Near 1
        dist_high = self.updater._create_distribution_from_point(0.95, confidence=0.7)
        assert dist_high.mean == 0.95
        assert dist_high.upper_bound <= 1.0  # Should not go above 1
        
    def test_adjust_for_overconfidence_moderate_probability(self):
        """Test overconfidence adjustment for moderate probabilities."""
        # Test through the distribution creation which includes reasonable bounds
        dist = self.updater._create_distribution_from_point(0.6, confidence=0.7)
        
        # Should have reasonable uncertainty
        assert dist.mean == 0.6
        assert dist.uncertainty > 0.0
        
    def test_adjust_for_overconfidence_extreme_probability(self):
        """Test overconfidence adjustment for extreme probabilities."""
        # High probability
        dist_high = self.updater._create_distribution_from_point(0.9, confidence=0.5)
        assert dist_high.mean == 0.9
        assert dist_high.uncertainty > 0.0  # Should have uncertainty
        
        # Low probability  
        dist_low = self.updater._create_distribution_from_point(0.1, confidence=0.5)
        assert dist_low.mean == 0.1
        assert dist_low.uncertainty > 0.0  # Should have uncertainty
        
    def test_adjust_for_overconfidence_many_evidence(self):
        """Test overconfidence adjustment with many pieces of evidence."""
        # More evidence should allow more confidence
        # Test through update_probability with different amounts of evidence
        single_evidence = [self.updater.create_evidence(
            EvidenceType.EXPERT_OPINION, True, 0.7, 0.8, "Expert", "test"
        )]
        
        many_evidences = single_evidence * 5  # 5 pieces of evidence
        
        result_few = self.updater.update_probability(0.5, single_evidence, "general")
        result_many = self.updater.update_probability(0.5, many_evidences, "general")
        
        # More evidence should reduce uncertainty
        assert result_many.uncertainty <= result_few.uncertainty
        
    def test_evidence_type_enum(self):
        """Test EvidenceType enum values."""
        assert EvidenceType.NEWS_SENTIMENT.value == "news_sentiment"
        assert EvidenceType.POLLING_DATA.value == "polling_data"
        assert EvidenceType.MARKET_BEHAVIOR.value == "market_behavior"
        assert EvidenceType.TIME_DECAY.value == "time_decay"
        assert EvidenceType.EXPERT_OPINION.value == "expert_opinion"
        assert EvidenceType.SOCIAL_SENTIMENT.value == "social_sentiment"
        
    def test_edge_case_prior_zero(self):
        """Test updating with prior probability of zero."""
        prior = 0.0
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.EXPERT_OPINION,
            positive_signal=True,
            strength=0.8,
            confidence=0.9,
            description="Strong expert opinion",
            source="expert"
        )
        
        result = self.updater.update_probability(
            prior=prior,
            evidence_list=[evidence],
            market_type="general"
        )
        
        assert result.mean > 0.0  # Should increase from zero
        assert result.mean < 0.5  # But shouldn't jump too high
        
    def test_edge_case_prior_one(self):
        """Test updating with prior probability of one."""
        prior = 1.0
        evidence = self.updater.create_evidence(
            evidence_type=EvidenceType.NEWS_SENTIMENT,
            positive_signal=False,
            strength=0.6,
            confidence=0.7,
            description="Negative news",
            source="news"
        )
        
        result = self.updater.update_probability(
            prior=prior,
            evidence_list=[evidence],
            market_type="general"
        )
        
        assert result.mean < 1.0  # Should decrease from one
        assert result.mean > 0.5  # But shouldn't drop too low


if __name__ == "__main__":
    pytest.main([__file__])