"""
Example of how to integrate sanity checking into the fair value engine.

This shows how we could prevent extreme predictions like the X/Truth Social merger.
"""

import asyncio
from datetime import datetime, timedelta

from src.analyzers.fair_value_engine import FairValueEngine
from src.analyzers.sanity_checker import SanityChecker
from src.clients.polymarket.models import Market, Token


async def analyze_with_sanity_check():
    """Demonstrate sanity checking on the X/Truth Social merger market."""
    
    # Create the problematic market
    merger_market = Market(
        condition_id="x_truth_social_merger",
        question="X and Truth Social merger announced before August?",
        description="Will X and Truth Social merge before July 31, 2025",
        category="Technology",
        active=True,
        closed=False,
        volume=50000.0,
        end_date_iso=datetime(2025, 7, 31),
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.006),  # 0.6%
            Token(token_id="no", outcome="No", price=0.994)     # 99.4%
        ],
        minimum_order_size=1.0
    )
    
    # Initialize components
    engine = FairValueEngine()
    sanity_checker = SanityChecker()
    
    # Get original prediction
    fair_value, confidence, reasoning = await engine.calculate_fair_value(merger_market, [])
    
    print("Original Analysis:")
    print(f"  Fair Value: {fair_value:.1%}")
    print(f"  Confidence: {confidence:.1%}")
    print(f"  Market Price: {merger_market.tokens[0].price:.1%}")
    print(f"  Reasoning: {reasoning[:200]}...")
    print()
    
    # Apply sanity checks
    sanity_result = sanity_checker.check_prediction(
        merger_market,
        fair_value,
        confidence,
        reasoning
    )
    
    print("Sanity Check Results:")
    print(f"  Passes Checks: {sanity_result.is_sane}")
    print(f"  Warnings: {len(sanity_result.warnings)}")
    for warning in sanity_result.warnings:
        print(f"    - {warning}")
    
    if sanity_result.adjusted_probability:
        print(f"  Adjusted Probability: {sanity_result.adjusted_probability:.1%}")
        
    # Apply confidence penalty
    adjusted_confidence = max(0.3, confidence - sanity_result.confidence_penalty)
    print(f"  Adjusted Confidence: {adjusted_confidence:.1%} (penalty: {sanity_result.confidence_penalty:.1%})")
    
    # Generate user warning
    warning = sanity_checker.generate_recommendation_warning(sanity_result)
    if warning:
        print("\nUser Warning:")
        print(warning)
        
    # Show what a more reasonable analysis might look like
    print("\n" + "="*80)
    print("After Sanity Checking:")
    print(f"  Fair Value: {sanity_result.adjusted_probability or fair_value:.1%}")
    print(f"  Confidence: {adjusted_confidence:.1%}")
    print(f"  Risk Level: HIGH (was MEDIUM)")
    print(f"  Recommendation: AVOID or SMALL POSITION ONLY")


def demonstrate_edge_cases():
    """Show how sanity checker handles various edge cases."""
    
    checker = SanityChecker()
    
    # Case 1: Reasonable prediction close to market
    print("\nCase 1: Reasonable Prediction")
    print("-" * 40)
    normal_market = Market(
        condition_id="test1",
        question="Will the Fed raise rates in March?",
        description="Federal Reserve rate decision",
        category="Economics",
        active=True, closed=False, volume=100000,
        end_date_iso=datetime.now() + timedelta(days=60),
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.65),
            Token(token_id="no", outcome="No", price=0.35)
        ],
        minimum_order_size=1.0
    )
    
    result = checker.check_prediction(normal_market, 0.70, 0.8, "Strong economic data suggests rate hike likely")
    print(f"Prediction: 70%, Market: 65%")
    print(f"Sane: {result.is_sane}, Warnings: {len(result.warnings)}")
    
    # Case 2: Extreme deviation
    print("\nCase 2: Extreme Deviation")
    print("-" * 40)
    result = checker.check_prediction(normal_market, 0.95, 0.9, "Limited news coverage")
    print(f"Prediction: 95%, Market: 65%")
    print(f"Sane: {result.is_sane}, Warnings: {len(result.warnings)}")
    for w in result.warnings:
        print(f"  - {w}")
    
    # Case 3: Low liquidity market
    print("\nCase 3: Low Liquidity")
    print("-" * 40)
    low_volume_market = Market(
        condition_id="test3",
        question="Will obscure event happen?",
        description="Some random event",
        category="Other",
        active=True, closed=False, volume=500,  # Very low
        end_date_iso=datetime.now() + timedelta(days=30),
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.10),
            Token(token_id="no", outcome="No", price=0.90)
        ],
        minimum_order_size=1.0
    )
    
    result = checker.check_prediction(low_volume_market, 0.50, 0.8, "Model predicts 50% chance")
    print(f"Volume: $500")
    print(f"Warnings: {len(result.warnings)}")
    for w in result.warnings:
        print(f"  - {w}")


if __name__ == "__main__":
    # Run the X/Truth Social merger example
    asyncio.run(analyze_with_sanity_check())
    
    # Show other edge cases
    demonstrate_edge_cases()