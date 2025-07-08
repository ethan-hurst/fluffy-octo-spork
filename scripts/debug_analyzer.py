#!/usr/bin/env python3
"""
Debug script to see why we're not finding opportunities.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.polymarket.client import PolymarketClient
from src.analyzers.refined_simple_analyzer import RefinedSimpleAnalyzer
from src.utils.market_filters import MarketFilter

async def debug_analyzer():
    """Debug why we're not finding opportunities."""
    
    async with PolymarketClient() as client:
        # Get markets using gamma API
        print("=== FETCHING MARKETS ===")
        markets = await client._get_gamma_markets(max_markets=50)
        
        print(f"Got {len(markets)} markets from gamma API")
        
        # Get prices
        prices = await client.get_prices()
        print(f"Got prices for {len(prices)} markets")
        
        # Initialize analyzer
        analyzer = RefinedSimpleAnalyzer()
        
        print("\n=== ANALYZING TOP 10 MARKETS ===")
        opportunities_found = 0
        
        for i, market in enumerate(markets[:10]):
            if market.condition_id not in prices:
                continue
                
            price = prices[market.condition_id]
            
            print(f"\n{i+1}. {market.question[:80]}...")
            print(f"   Volume: ${market.volume:,.0f}" if market.volume else "   Volume: Unknown")
            print(f"   Price: YES={price.yes_price:.2%}, NO={price.no_price:.2%}")
            
            # Calculate days left
            days_left = None
            if market.end_date_iso:
                days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
                print(f"   Days until resolution: {days_left}")
            
            # Check why it might be filtered
            print("   Filters:")
            
            # Volume check
            if market.volume and market.volume < analyzer.min_volume:
                print(f"   ❌ Volume too low: ${market.volume:,.0f} < ${analyzer.min_volume:,.0f}")
                continue
            else:
                print(f"   ✓ Volume OK: ${market.volume:,.0f}")
            
            # Price extremes check
            if price.yes_price <= 0.01 or price.yes_price >= 0.99:
                print(f"   ❌ Price at extreme: {price.yes_price:.2%}")
                continue
            else:
                print(f"   ✓ Price OK: {price.yes_price:.2%}")
            
            # Time decay check
            if days_left and 1 <= days_left <= 7:
                print(f"   ✓ Good for time decay: {days_left} days")
                
                # Check for volatile keywords
                question_lower = market.question.lower()
                volatile_found = [kw for kw in analyzer.volatile_keywords if kw in question_lower]
                if volatile_found:
                    print(f"   ❌ Volatile keywords found: {', '.join(volatile_found)}")
                else:
                    print(f"   ✓ No volatile keywords")
                    
                # Check for stable keywords
                stable_found = [kw for kw in analyzer.stable_keywords if kw in question_lower]
                if stable_found:
                    print(f"   ✓ Stable keywords found: {', '.join(stable_found)}")
                else:
                    print(f"   ❌ No stable keywords found")
            else:
                print(f"   ❌ Not in time decay window (need 1-7 days, have {days_left})")
            
            # Try analyzing
            opportunity = analyzer.analyze_market(market, price)
            if opportunity:
                print(f"   🎯 OPPORTUNITY FOUND: {opportunity.pattern_type}")
                print(f"      Action: {opportunity.recommended_action}")
                print(f"      Edge: {opportunity.edge:.2%}")
                print(f"      Reason: {opportunity.reason}")
                opportunities_found += 1
            else:
                print(f"   ✗ No opportunity detected")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total opportunities found: {opportunities_found}")
        
        # Check thresholds
        print(f"\nCurrent thresholds:")
        print(f"- Min volume: ${analyzer.min_volume:,.0f}")
        print(f"- Min edge: {analyzer.min_edge:.2%}")
        
        # Look for ANY market with time decay potential
        print(f"\n=== MARKETS WITH TIME DECAY POTENTIAL ===")
        time_decay_count = 0
        for market in markets:
            if market.end_date_iso:
                days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
                if 1 <= days_left <= 7 and market.volume and market.volume >= 5000:
                    if market.condition_id in prices:
                        price = prices[market.condition_id]
                        if 0.15 < price.yes_price < 0.85:
                            print(f"- {market.question[:60]}... ({days_left} days, {price.yes_price:.0%})")
                            time_decay_count += 1
                            if time_decay_count >= 5:
                                break
        
        if time_decay_count == 0:
            print("No markets found with time decay potential")

if __name__ == "__main__":
    asyncio.run(debug_analyzer())