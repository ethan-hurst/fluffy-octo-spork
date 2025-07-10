#!/usr/bin/env python3
"""
Test multi-outcome market functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analyzers.market_researcher import MarketResearcher


async def test_multi_outcome():
    """Test multi-outcome market research."""
    
    researcher = MarketResearcher()
    
    # Test URLs - try different election/multi-outcome markets
    test_urls = [
        "https://polymarket.com/event/new-york-city-mayoral-election",
        "https://polymarket.com/event/2024-presidential-election",
        "https://polymarket.com/event/republican-nominee-2024",
        "https://polymarket.com/event/democratic-nominee-2024",
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print('='*60)
        
        result = await researcher.research_market(url)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        elif result.get('multi_outcome'):
            print("✅ Multi-outcome market detected!")
            market = result['market']
            print(f"Title: {market.title}")
            print(f"Options: {len(market.options)}")
            print(f"Total Volume: ${market.total_volume:,.0f}")
            
            print("\nTop 3 Options:")
            for i, option in enumerate(market.options[:3]):
                print(f"{i+1}. {option['name']}: {option['price']:.1%} (${option['volume']:,.0f})")
        else:
            print("Single market found")
            market = result['market']
            print(f"Question: {market.question}")
            print(f"Price: {market.last_trade_price:.1%}")


if __name__ == "__main__":
    asyncio.run(test_multi_outcome())