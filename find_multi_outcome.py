#!/usr/bin/env python3
"""
Find multi-outcome markets in the API
"""

import httpx
import asyncio
import json

async def find_multi_outcome():
    """Find multi-outcome markets."""
    
    async with httpx.AsyncClient() as client:
        print("=== FINDING MULTI-OUTCOME MARKETS ===\n")
        
        # Get active markets
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "limit": 500},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            
            # Look for markets with special characteristics
            multi_outcome_markets = []
            election_markets = []
            
            for market in markets:
                # Check for election/multiple choice indicators
                question = market.get('question', '').lower()
                
                # Election markets
                if any(word in question for word in ['election', 'president', 'mayor', 'governor', 'nominee']):
                    election_markets.append(market)
                
                # Markets with outcomes field
                if market.get('outcomes') and len(market.get('outcomes', [])) > 2:
                    multi_outcome_markets.append(market)
                
                # Markets with marketType
                if market.get('marketType') == 'MULTIPLE_CHOICE':
                    multi_outcome_markets.append(market)
                
                # Group markets
                if market.get('groupSlug'):
                    group_slug = market.get('groupSlug', '')
                    if 'election' in group_slug or 'winner' in group_slug:
                        election_markets.append(market)
            
            print(f"Found {len(election_markets)} election-related markets")
            print(f"Found {len(multi_outcome_markets)} multi-outcome markets\n")
            
            # Show some examples
            print("Election Markets:")
            for market in election_markets[:5]:
                print(f"\n- {market.get('question')}")
                print(f"  Slug: {market.get('slug')}")
                print(f"  Group: {market.get('groupSlug')}")
                print(f"  Type: {market.get('marketType')}")
                print(f"  Outcomes: {market.get('outcomes')}")
            
            # Look for NYC mayoral specifically
            print("\n\nSearching for NYC mayoral...")
            nyc_markets = [m for m in markets if 'nyc' in m.get('question', '').lower() or 'new york' in m.get('question', '').lower()]
            
            for market in nyc_markets:
                print(f"\n- {market.get('question')}")
                print(f"  Slug: {market.get('slug')}")
                print(f"  URL: https://polymarket.com/event/{market.get('slug')}")
            
            # Check for grouped markets
            print("\n\nChecking for grouped markets...")
            groups = {}
            for market in markets:
                group = market.get('groupSlug')
                if group:
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(market)
            
            # Show groups with multiple markets
            multi_market_groups = {k: v for k, v in groups.items() if len(v) > 1}
            print(f"\nFound {len(multi_market_groups)} groups with multiple markets")
            
            for group, group_markets in list(multi_market_groups.items())[:3]:
                print(f"\n\nGroup: {group}")
                print(f"Markets in group: {len(group_markets)}")
                for market in group_markets[:3]:
                    print(f"  - {market.get('question')}")
                    print(f"    Price: {market.get('lastTradePrice')}")

if __name__ == "__main__":
    asyncio.run(find_multi_outcome())