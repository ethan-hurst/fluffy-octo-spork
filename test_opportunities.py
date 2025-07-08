#!/usr/bin/env python3
"""Test finding opportunities with current markets."""

import asyncio
from src.clients.polymarket.client import PolymarketClient
from src.analyzers.fair_value_engine import FairValueEngine
from src.config.settings import settings

async def test_opportunities():
    """Test finding opportunities."""
    client = PolymarketClient()
    fair_value_engine = FairValueEngine()
    
    print(f"\nSettings:")
    print(f"- Min volume: ${settings.min_market_volume:,.0f}")
    print(f"- Min spread: {settings.min_probability_spread:.1%}")
    print(f"- Max markets: {settings.max_markets_to_analyze}")
    
    async with client:
        print("\nFetching markets...")
        markets = await client.get_all_active_markets(max_markets=30)
        print(f"Found {len(markets)} active markets")
        
        if not markets:
            print("No active markets found!")
            return
        
        print("\nAnalyzing first 5 markets:")
        opportunities = []
        
        for i, market in enumerate(markets[:5]):
            price = await client.get_market_prices(market)
            if not price:
                print(f"\n{i+1}. {market.question[:60]}... - NO PRICE DATA")
                continue
                
            print(f"\n{i+1}. {market.question[:60]}...")
            print(f"   Volume: ${market.volume:,.0f}")
            print(f"   Current: YES {price.yes_price:.2%}, NO {price.no_price:.2%}")
            
            # Calculate fair value
            try:
                fair_yes, fair_no, reasoning = await fair_value_engine.calculate_fair_value(market, [])
                print(f"   Fair:    YES {fair_yes:.2%}, NO {fair_no:.2%}")
                
                # Check opportunity
                yes_diff = abs(fair_yes - price.yes_price)
                no_diff = abs(fair_no - price.no_price)
                max_diff = max(yes_diff, no_diff)
                
                print(f"   Max difference: {max_diff:.2%}")
                print(f"   Reasoning: {reasoning[:100]}...")
                
                if max_diff >= settings.min_probability_spread:
                    opportunities.append({
                        'market': market,
                        'diff': max_diff,
                        'fair_yes': fair_yes,
                        'fair_no': fair_no,
                        'current_yes': price.yes_price,
                        'current_no': price.no_price
                    })
                    print(f"   ✓ OPPORTUNITY FOUND!")
                    
            except Exception as e:
                print(f"   ERROR: {e}")
        
        print(f"\n\nSummary:")
        print(f"- Markets analyzed: 5")
        print(f"- Opportunities found: {len(opportunities)}")
        
        if opportunities:
            print("\nOpportunities:")
            for opp in opportunities:
                market = opp['market']
                print(f"\n- {market.question}")
                print(f"  Current: YES {opp['current_yes']:.2%}, NO {opp['current_no']:.2%}")
                print(f"  Fair:    YES {opp['fair_yes']:.2%}, NO {opp['fair_no']:.2%}")
                print(f"  Difference: {opp['diff']:.2%}")

if __name__ == "__main__":
    asyncio.run(test_opportunities())