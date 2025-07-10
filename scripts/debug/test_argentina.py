#!/usr/bin/env python3
"""
Test Argentina election market
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analyzers.multi_outcome_researcher import MultiOutcomeResearcher


async def test_argentina():
    """Test Argentina multi-outcome market."""
    
    researcher = MultiOutcomeResearcher()
    
    print("Testing Argentina election market...")
    
    try:
        # Test finding related markets
        slug = "will-lla-win-the-most-seats-in-the-chamber-of-deputies-following-the-2025-argentina-election"
        
        print(f"\n1. Finding related markets for: {slug[:50]}...")
        related = await researcher._find_related_markets(slug)
        
        print(f"Found {len(related)} related markets:")
        for market in related[:5]:
            print(f"  - {market.question}")
            print(f"    Price: {market.last_trade_price:.1%}")
        
        if related:
            print("\n2. Creating multi-outcome market...")
            multi_market = researcher._create_multi_outcome_market(related)
            
            print(f"Title: {multi_market.title}")
            print(f"Options: {len(multi_market.options)}")
            print(f"Total Volume: ${multi_market.total_volume:,.0f}")
            
            print("\n3. Analyzing market...")
            analysis = researcher._analyze_multi_outcome(multi_market)
            
            efficiency = analysis['market_efficiency']
            print(f"Total Probability: {efficiency['total_probability']:.1%}")
            print(f"Arbitrage Possible: {efficiency['arbitrage_possible']}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_argentina())