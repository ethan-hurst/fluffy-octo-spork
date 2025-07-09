#!/usr/bin/env python3
"""
Comprehensive opportunity finder with expanded patterns.
"""

import asyncio
import sys
from typing import List

# Add project root to Python path
sys.path.append('.')

from src.clients.polymarket.client import PolymarketClient
from src.analyzers.flexible_analyzer import FlexibleAnalyzer
from src.utils.market_filters import MarketFilter
from src.clients.polymarket.models import Market, MarketPrice
from src.config.settings import settings

async def find_opportunities():
    """Find opportunities using the improved analyzer."""
    
    # Temporarily adjust settings
    settings.min_market_volume = 100.0  # Very low threshold
    settings.min_probability_spread = 0.03  # 3% minimum
    settings.max_markets_to_analyze = 500  # Analyze more markets
    
    client = PolymarketClient()
    analyzer = FlexibleAnalyzer()
    analyzer.min_edge = 0.03  # Lower edge requirement
    analyzer.min_volume = 100  # Lower volume requirement
    
    print("Fetching markets...")
    markets = await client.get_all_active_markets(
        max_markets=500  # Get more markets
    )
    
    print(f"Analyzing {len(markets)} markets...\n")
    
    opportunities = []
    patterns_count = {}
    
    for market in markets:
        try:
            # Create mock price object
            price = MarketPrice(
                condition_id=market.condition_id,
                yes_price=market.last_trade_price or 0.5,
                no_price=1.0 - (market.last_trade_price or 0.5),
                spread=0.02  # Assume 2% spread
            )
            
            opportunity = analyzer.analyze_market(market, price)
            
            if opportunity:
                opportunities.append({
                    'market': market,
                    'opportunity': opportunity,
                    'price': price
                })
                
                # Count patterns
                pattern = opportunity.pattern_type
                patterns_count[pattern] = patterns_count.get(pattern, 0) + 1
                
        except Exception as e:
            print(f"Error analyzing {market.question}: {e}")
            continue
    
    # Sort by edge * volume
    opportunities.sort(
        key=lambda x: x['opportunity'].edge * min(x['market'].volume or 0, 100000),
        reverse=True
    )
    
    print(f"\n=== FOUND {len(opportunities)} OPPORTUNITIES ===\n")
    
    # Show pattern distribution
    print("Pattern Distribution:")
    for pattern, count in sorted(patterns_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern}: {count} opportunities")
    
    print("\n=== TOP OPPORTUNITIES BY PATTERN ===\n")
    
    # Group by pattern and show top 3 of each
    by_pattern = {}
    for opp in opportunities:
        pattern = opp['opportunity'].pattern_type
        if pattern not in by_pattern:
            by_pattern[pattern] = []
        by_pattern[pattern].append(opp)
    
    for pattern, opps in sorted(by_pattern.items()):
        print(f"\n{pattern}:")
        print("-" * 80)
        
        for i, opp_data in enumerate(opps[:3]):
            market = opp_data['market']
            opp = opp_data['opportunity']
            print(f"\n{i+1}. {market.question}")
            print(f"   Price: {opp.current_price:.1%} | Volume: ${market.volume:,.0f}")
            print(f"   Edge: {opp.edge:.1%} | Confidence: {opp.confidence:.0%}")
            print(f"   Action: {opp.recommended_action} | {opp.reason}")
            print(f"   URL: https://polymarket.com/event/{market.market_slug}")
    
    # Show top 10 overall
    print("\n\n=== TOP 10 OPPORTUNITIES BY EDGE ===")
    print("-" * 80)
    
    for i, opp_data in enumerate(opportunities[:10]):
        market = opp_data['market']
        opp = opp_data['opportunity']
        print(f"\n{i+1}. {market.question}")
        print(f"   Pattern: {opp.pattern_type} | Edge: {opp.edge:.1%}")
        print(f"   Price: {opp.current_price:.1%} | Volume: ${market.volume:,.0f}")
        print(f"   Action: {opp.recommended_action} | {opp.reason}")
        print(f"   URL: https://polymarket.com/event/{market.market_slug}")
    
    return opportunities


async def main():
    try:
        opportunities = await find_opportunities()
        
        # Summary
        print(f"\n\n=== SUMMARY ===")
        print(f"Total opportunities found: {len(opportunities)}")
        
        if opportunities:
            avg_edge = sum(o['opportunity'].edge for o in opportunities) / len(opportunities)
            total_volume = sum(o['market'].volume or 0 for o in opportunities)
            print(f"Average edge: {avg_edge:.1%}")
            print(f"Total volume: ${total_volume:,.0f}")
            
            # Quick picks
            print(f"\n=== QUICK PICKS (HIGH CONFIDENCE + GOOD VOLUME) ===")
            quick_picks = [
                o for o in opportunities 
                if o['opportunity'].confidence >= 0.7 
                and (o['market'].volume or 0) > 10000
                and o['opportunity'].edge >= 0.05
            ]
            
            for i, pick in enumerate(quick_picks[:5]):
                market = pick['market']
                opp = pick['opportunity']
                print(f"\n{i+1}. {market.question[:60]}...")
                print(f"   {opp.recommended_action} at {opp.current_price:.0%} (Edge: {opp.edge:.0%})")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())