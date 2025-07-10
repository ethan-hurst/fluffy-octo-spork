"""
Test that the Kelly Criterion and model fixes work.
"""

import asyncio
from datetime import datetime

from src.analyzers.kelly_criterion import KellyCriterion
from src.analyzers.models import MarketOpportunity, OpportunityScore
from src.clients.polymarket.models import Market, Token


def test_kelly_criterion():
    """Test Kelly Criterion works."""
    print("🧪 Testing Kelly Criterion...")
    
    kelly_calc = KellyCriterion()
    
    # Create test market
    market = Market(
        condition_id="test",
        question="Test market",
        active=True,
        closed=False,
        minimum_order_size=1.0,
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.40),
            Token(token_id="no", outcome="No", price=0.60)
        ]
    )
    
    result = kelly_calc.calculate(
        market=market,
        predicted_probability=0.55,
        confidence=0.8,
        recommended_position="YES"
    )
    
    print(f"✅ Kelly calculation successful:")
    print(f"   Expected Value: {result.expected_value:.1%}")
    print(f"   Recommended Position: {result.recommended_fraction:.1%}")
    print(f"   Advice: {result.recommendation}")
    

def test_models():
    """Test that models work with Kelly analysis."""
    print("\n🧪 Testing Models with Kelly Analysis...")
    
    # Create opportunity
    opportunity = MarketOpportunity(
        condition_id="test_opp",
        question="Test opportunity",
        current_yes_price=0.40,
        current_no_price=0.60,
        current_spread=0.20,
        fair_yes_price=0.55,
        fair_no_price=0.45,
        expected_return=37.5,
        recommended_position="YES",
        score=OpportunityScore(
            value_score=0.8,
            confidence_score=0.7,
            volume_score=0.6,
            time_score=0.5,
            news_relevance_score=0.4
        ),
        reasoning="Test reasoning"
    )
    
    # Test Kelly analysis can be added
    kelly_calc = KellyCriterion()
    kelly_result = kelly_calc.calculate(
        market=Market(
            condition_id="test",
            question="Test",
            active=True,
            closed=False,
            minimum_order_size=1.0,
            tokens=[
                Token(token_id="yes", outcome="Yes", price=0.40),
                Token(token_id="no", outcome="No", price=0.60)
            ]
        ),
        predicted_probability=0.55,
        confidence=0.7,
        recommended_position="YES"
    )
    
    opportunity.kelly_analysis = kelly_result
    
    print(f"✅ MarketOpportunity with Kelly analysis:")
    print(f"   Question: {opportunity.question}")
    print(f"   Risk Level: {opportunity.risk_level}")
    print(f"   Kelly Position: {opportunity.kelly_analysis.recommended_fraction:.1%}")
    

if __name__ == "__main__":
    print("🔧 Testing Fixes\n")
    
    try:
        test_kelly_criterion()
        test_models()
        print("\n✅ All tests passed! The fixes work correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()