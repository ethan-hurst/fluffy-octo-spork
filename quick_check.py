#!/usr/bin/env python3
"""Quick check of current market data."""

import asyncio
import json
from src.clients.polymarket.client import PolymarketClient
from src.analyzers.fair_value_engine import FairValueEngine
from src.config.settings import settings

async def quick_check():
    """Quick check of market data."""
    client = PolymarketClient()
    fair_value_engine = FairValueEngine()
    
    print(f"\nSettings:")
    print(f"- Min volume: ${settings.min_market_volume:,.0f}")
    print(f"- Min spread: {settings.min_probability_spread:.1%}")
    
    async with client:
        # Get markets - the issue is we're using CLOB API instead of Gamma
        # Let's use the get_all_active_markets method which handles both APIs
        markets = await client.get_all_active_markets(max_markets=20)
        
        print(f"\nFetched {len(markets)} active markets\n")
        
        opportunities = []
        
        for i, market in enumerate(markets[:10]):
            price = await client.get_market_prices(market)
            if not price:
                continue
                
            print(f"{i+1}. {market.question[:80]}...")
            print(f"   Volume: ${market.volume:,.0f}")
            print(f"   Current: YES {price.yes_price:.2%}, NO {price.no_price:.2%}")
            
            # Quick fair value check
            try:
                fair_yes, fair_no, reasoning = await fair_value_engine.calculate_fair_value(market, [])
                print(f"   Fair:    YES {fair_yes:.2%}, NO {fair_no:.2%}")
                
                # Check for opportunity
                yes_diff = abs(fair_yes - price.yes_price)
                no_diff = abs(fair_no - price.no_price)
                max_diff = max(yes_diff, no_diff)
                
                print(f"   Max difference: {max_diff:.2%}")
                
                if max_diff >= settings.min_probability_spread:
                    opportunities.append((market, max_diff))
                    print(f"   ✓ OPPORTUNITY!")
                else:
                    print(f"   ✗ Difference too small")
                    
            except Exception as e:
                print(f"   Error calculating fair value: {e}")
            
            print()
        
        print(f"\nSummary: Found {len(opportunities)} opportunities out of {len(markets[:10])} markets checked")
        
        if not opportunities and settings.min_probability_spread > 0.05:
            print("\nTip: Try lowering min_probability_spread in settings")

if __name__ == "__main__":
    asyncio.run(quick_check())