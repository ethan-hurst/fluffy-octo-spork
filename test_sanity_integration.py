"""
Test the sanity checking integration with the X/Truth Social merger example.
"""

import asyncio
from datetime import datetime, timedelta

from src.analyzers.fair_value_engine import FairValueEngine
from src.clients.polymarket.models import Market, Token


async def test_sanity_checking():
    """Test that sanity checking prevents extreme predictions."""
    
    # Create the X/Truth Social merger market
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
    
    # Initialize engine
    engine = FairValueEngine()
    
    # Get prediction with sanity checking
    yes_prob, no_prob, reasoning = await engine.calculate_fair_value(merger_market, [])
    
    print("Sanity-Checked Analysis:")
    print(f"  Fair Value (YES): {yes_prob:.1%}")
    print(f"  Fair Value (NO): {no_prob:.1%}")
    print(f"  Market Price (YES): {merger_market.tokens[0].price:.1%}")
    print(f"\nReasoning:")
    print(f"  {reasoning}")
    
    # Check if warnings were added
    if "Important Considerations" in reasoning:
        print("\n✅ SUCCESS: Sanity checking added warnings!")
    else:
        print("\n⚠️ WARNING: No sanity check warnings found")
        
    # Check if probability was adjusted
    if yes_prob < 0.1:  # Should be capped well below 30%
        print(f"✅ SUCCESS: Probability adjusted from ~30% to {yes_prob:.1%}")
    else:
        print(f"⚠️ WARNING: Probability still high at {yes_prob:.1%}")
        
    return yes_prob, reasoning


async def test_normal_market():
    """Test that sanity checking doesn't interfere with reasonable predictions."""
    
    # Create a reasonable market
    normal_market = Market(
        condition_id="fed_rates",
        question="Will the Fed raise rates in March 2025?",
        description="Federal Reserve interest rate decision",
        category="Economics",
        active=True,
        closed=False,
        volume=500000.0,
        end_date_iso=datetime(2025, 3, 31),
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.65),
            Token(token_id="no", outcome="No", price=0.35)
        ],
        minimum_order_size=1.0
    )
    
    engine = FairValueEngine()
    yes_prob, no_prob, reasoning = await engine.calculate_fair_value(normal_market, [])
    
    print("\n" + "="*60)
    print("Normal Market Analysis:")
    print(f"  Fair Value (YES): {yes_prob:.1%}")
    print(f"  Market Price (YES): {normal_market.tokens[0].price:.1%}")
    print(f"  Difference: {abs(yes_prob - normal_market.tokens[0].price):.1%}")
    
    # Should not have extreme warnings
    if "Important Considerations" not in reasoning:
        print("✅ SUCCESS: No warnings for reasonable prediction")
    else:
        print("⚠️ Unexpected warnings added")
        

if __name__ == "__main__":
    print("Testing Sanity Checking Integration\n")
    asyncio.run(test_sanity_checking())
    asyncio.run(test_normal_market())