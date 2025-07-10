#!/usr/bin/env python3
"""
Analyze multi-outcome market structure
"""

import httpx
import asyncio
import json

async def analyze_multi_outcome():
    """Analyze the NYC mayoral election market structure."""
    
    slug = "new-york-city-mayoral-election"
    
    async with httpx.AsyncClient() as client:
        print("=== ANALYZING MULTI-OUTCOME MARKET ===\n")
        
        # Get market by slug
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"slug": slug},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            print(f"Found {len(markets)} markets for slug: {slug}\n")
            
            if markets:
                # First, check if it's a single market with multiple outcomes
                first_market = markets[0]
                print("First market structure:")
                print(f"Question: {first_market.get('question')}")
                print(f"Market Type: {first_market.get('marketType')}")
                print(f"Outcome Prices: {first_market.get('outcomePrices')}")
                print(f"Outcomes: {first_market.get('outcomes')}")
                print(f"Condition ID: {first_market.get('conditionId')}")
                print(f"Group Slug: {first_market.get('groupSlug')}")
                
                # Check for tokens/outcomes structure
                if 'tokens' in first_market:
                    print(f"\nTokens found: {len(first_market['tokens'])}")
                    for i, token in enumerate(first_market['tokens'][:5]):
                        print(f"  Token {i}: {token.get('outcome')} - ID: {token.get('token_id')}")
                
                # If multiple markets, they might be related
                if len(markets) > 1:
                    print(f"\n\nMultiple markets found ({len(markets)} total):")
                    for i, market in enumerate(markets[:10]):  # Show first 10
                        print(f"\n{i+1}. {market.get('question')}")
                        print(f"   Slug: {market.get('slug')}")
                        print(f"   Group Slug: {market.get('groupSlug')}")
                        print(f"   Last Price: {market.get('lastTradePrice')}")
                        print(f"   Volume: ${float(market.get('volume', 0)):,.0f}")
                
                # Try to get group info if available
                if first_market.get('groupSlug'):
                    print(f"\n\nTrying to get group info for: {first_market['groupSlug']}")
                    group_response = await client.get(
                        f"https://gamma-api.polymarket.com/events/{first_market['groupSlug']}",
                        timeout=30.0
                    )
                    if group_response.status_code == 200:
                        group_data = group_response.json()
                        print("Group data found!")
                        print(json.dumps(group_data, indent=2)[:500] + "...")
                
                # Save full structure for analysis
                with open('multi_outcome_structure.json', 'w') as f:
                    json.dump(markets, f, indent=2)
                print("\n\nFull market structure saved to multi_outcome_structure.json")

if __name__ == "__main__":
    asyncio.run(analyze_multi_outcome())