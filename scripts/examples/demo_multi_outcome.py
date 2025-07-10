#!/usr/bin/env python3
"""
Demo multi-outcome market functionality
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analyzers.multi_outcome_researcher import MultiOutcomeResearcher, MultiOutcomeMarket, SimpleMarket


async def demo_multi_outcome():
    """Demo multi-outcome functionality with mock data."""
    
    print("=== MULTI-OUTCOME MARKET DEMO ===\n")
    
    # Create mock Argentina election markets
    mock_markets = [
        SimpleMarket(
            condition_id="0x001",
            question="Will LLA win the most seats in the Chamber of Deputies following the 2025 Argentina election?",
            description=None,
            market_slug="will-lla-win-argentina-2025",
            category="Politics",
            volume=132651,
            liquidity=50000,
            last_trade_price=0.83,
            end_date_iso=datetime(2025, 10, 27)
        ),
        SimpleMarket(
            condition_id="0x002",
            question="Will UP win the most seats in the Chamber of Deputies following the 2025 Argentina election?",
            description=None,
            market_slug="will-up-win-argentina-2025",
            category="Politics",
            volume=11991,
            liquidity=10000,
            last_trade_price=0.16,
            end_date_iso=datetime(2025, 10, 27)
        ),
        SimpleMarket(
            condition_id="0x003",
            question="Will PRO win the most seats in the Chamber of Deputies following the 2025 Argentina election?",
            description=None,
            market_slug="will-pro-win-argentina-2025",
            category="Politics",
            volume=383870,
            liquidity=80000,
            last_trade_price=0.006,
            end_date_iso=datetime(2025, 10, 27)
        ),
        SimpleMarket(
            condition_id="0x004",
            question="Will UCR win the most seats in the Chamber of Deputies following the 2025 Argentina election?",
            description=None,
            market_slug="will-ucr-win-argentina-2025",
            category="Politics",
            volume=292631,
            liquidity=60000,
            last_trade_price=0.006,
            end_date_iso=datetime(2025, 10, 27)
        ),
        SimpleMarket(
            condition_id="0x005",
            question="Will HNP win the most seats in the Chamber of Deputies following the 2025 Argentina election?",
            description=None,
            market_slug="will-hnp-win-argentina-2025",
            category="Politics",
            volume=258981,
            liquidity=40000,
            last_trade_price=0.004,
            end_date_iso=datetime(2025, 10, 27)
        )
    ]
    
    researcher = MultiOutcomeResearcher()
    
    # Create multi-outcome market
    print("Creating multi-outcome market from related markets...")
    multi_market = researcher._create_multi_outcome_market(mock_markets)
    
    print(f"\nMarket: {multi_market.title}")
    print(f"Total Volume: ${multi_market.total_volume:,.0f}")
    print(f"Options: {len(multi_market.options)}")
    
    # Analyze
    print("\nAnalyzing market...")
    analysis = researcher._analyze_multi_outcome(multi_market)
    
    # Display results
    print("\n=== MARKET EFFICIENCY ===")
    efficiency = analysis['market_efficiency']
    print(f"Total Probability: {efficiency['total_probability']:.1%}")
    print(f"Efficiency Score: {efficiency['efficiency']:.1%}")
    print(f"Is Efficient: {efficiency['is_efficient']}")
    print(f"Arbitrage Possible: {efficiency['arbitrage_possible']}")
    
    print("\n=== CANDIDATES/OPTIONS ===")
    for i, option in enumerate(multi_market.options):
        print(f"{i+1}. {option['name']}: {option['price']:.1%} (${option['volume']:,.0f})")
    
    if analysis.get('arbitrage'):
        arb = analysis['arbitrage']
        print(f"\n=== ARBITRAGE OPPORTUNITY ===")
        print(f"Type: {arb['type']}")
        print(f"Total Cost: ${arb['total_cost']:.3f}")
        print(f"Guaranteed Return: ${arb['guaranteed_return']:.3f}")
        print(f"Profit: ${arb['profit']:.3f} ({arb['profit_percentage']:.1f}%)")
    
    print("\n=== DISPLAY IN APP ===")
    print("This would show as a multi-outcome market with:")
    print("- A table of all candidates/options with prices")
    print("- Market efficiency analysis")
    print("- Arbitrage opportunities if they exist")
    print("- Individual trading opportunities for each option")


if __name__ == "__main__":
    asyncio.run(demo_multi_outcome())