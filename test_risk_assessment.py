"""
Test the improved risk assessment system.
"""

from datetime import datetime
from src.analyzers.models import MarketOpportunity, OpportunityScore


def test_risk_assessment():
    """Test that risk assessment properly reflects probability of loss."""
    
    print("Testing Improved Risk Assessment System\n")
    
    # Test Case 1: X/Truth Social merger (should be EXTREME risk)
    extreme_risk_opp = MarketOpportunity(
        condition_id="x_truth_social_merger",
        question="X and Truth Social merger announced before August?",
        current_yes_price=0.006,  # 0.6% market price
        current_no_price=0.994,   # 99.4% market price
        current_spread=0.0,
        fair_yes_price=0.05,      # 5% fair value (after sanity check)
        fair_no_price=0.95,       # 95% fair value
        expected_return=733.0,    # Large expected return
        recommended_position="YES",
        score=OpportunityScore(
            value_score=0.9,      # High value score due to large discrepancy
            confidence_score=0.35, # Low confidence due to sanity check penalty
            volume_score=0.3,     # Medium volume
            time_score=0.1,       # Short timeline
            news_relevance_score=0.1
        ),
        reasoning="High uncertainty merger prediction with sanity check warnings"
    )
    
    print("Case 1: X/Truth Social Merger")
    print(f"  Current Price: {extreme_risk_opp.current_yes_price:.1%}")
    print(f"  Fair Price: {extreme_risk_opp.fair_yes_price:.1%}")
    print(f"  Position: {extreme_risk_opp.recommended_position}")
    print(f"  Probability of Loss: {(1.0 - extreme_risk_opp.fair_yes_price):.1%}")
    print(f"  Confidence: {extreme_risk_opp.score.confidence_score:.1%}")
    print(f"  Risk Level: {extreme_risk_opp.risk_level}")
    print(f"  Expected: EXTREME (due to 95% chance of total loss)")
    print()
    
    # Test Case 2: Reasonable market (should be LOW-MEDIUM risk)
    reasonable_opp = MarketOpportunity(
        condition_id="fed_rates",
        question="Will the Fed raise rates in March 2025?",
        current_yes_price=0.65,   # 65% market price
        current_no_price=0.35,    # 35% market price
        current_spread=0.0,
        fair_yes_price=0.70,      # 70% fair value
        fair_no_price=0.30,       # 30% fair value
        expected_return=7.7,      # Reasonable expected return
        recommended_position="YES",
        score=OpportunityScore(
            value_score=0.3,      # Small value difference
            confidence_score=0.8, # High confidence
            volume_score=0.9,     # High volume
            time_score=0.7,       # Good timeline
            news_relevance_score=0.6
        ),
        reasoning="Fed rate decision based on economic data"
    )
    
    print("Case 2: Fed Rate Decision")
    print(f"  Current Price: {reasonable_opp.current_yes_price:.1%}")
    print(f"  Fair Price: {reasonable_opp.fair_yes_price:.1%}")
    print(f"  Position: {reasonable_opp.recommended_position}")
    print(f"  Probability of Loss: {(1.0 - reasonable_opp.fair_yes_price):.1%}")
    print(f"  Confidence: {reasonable_opp.score.confidence_score:.1%}")
    print(f"  Risk Level: {reasonable_opp.risk_level}")
    print(f"  Expected: LOW (due to 30% chance of total loss with high confidence)")
    print()
    
    # Test Case 3: High probability bet (should be MINIMAL risk)
    safe_opp = MarketOpportunity(
        condition_id="safe_bet",
        question="Will the sun rise tomorrow?",
        current_yes_price=0.95,   # 95% market price
        current_no_price=0.05,    # 5% market price
        current_spread=0.0,
        fair_yes_price=0.99,      # 99% fair value
        fair_no_price=0.01,       # 1% fair value
        expected_return=4.2,      # Small expected return
        recommended_position="YES",
        score=OpportunityScore(
            value_score=0.2,      # Small value difference
            confidence_score=0.95, # Very high confidence
            volume_score=0.8,     # High volume
            time_score=0.9,       # Good timeline
            news_relevance_score=0.1
        ),
        reasoning="Very high probability event"
    )
    
    print("Case 3: Very High Probability Event")
    print(f"  Current Price: {safe_opp.current_yes_price:.1%}")
    print(f"  Fair Price: {safe_opp.fair_yes_price:.1%}")
    print(f"  Position: {safe_opp.recommended_position}")
    print(f"  Probability of Loss: {(1.0 - safe_opp.fair_yes_price):.1%}")
    print(f"  Confidence: {safe_opp.score.confidence_score:.1%}")
    print(f"  Risk Level: {safe_opp.risk_level}")
    print(f"  Expected: MINIMAL (due to 1% chance of total loss)")
    print()


if __name__ == "__main__":
    test_risk_assessment()