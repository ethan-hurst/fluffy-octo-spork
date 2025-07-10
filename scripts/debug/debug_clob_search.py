#!/usr/bin/env python3
"""
Debug CLOB search to understand why the market isn't found
"""

import httpx
import asyncio

async def debug_search():
    """Debug the CLOB API search."""
    
    target_slug = "will-elon-register-the-america-party-by"
    
    async with httpx.AsyncClient() as client:
        print(f"Searching for slug: {target_slug}\n")
        
        # Check a few pages and look for similar markets
        next_cursor = "MA=="
        pages_to_check = 3
        
        for page in range(pages_to_check):
            response = await client.get(
                "https://clob.polymarket.com/markets",
                params={"next_cursor": next_cursor},
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('data', [])
                
                print(f"Page {page + 1}: {len(markets)} markets")
                
                # Look for Elon markets
                elon_markets = []
                america_markets = []
                party_markets = []
                
                for market in markets:
                    question = market.get('question', '').lower()
                    slug = market.get('market_slug', '').lower()
                    
                    if 'elon' in question or 'elon' in slug:
                        elon_markets.append(market)
                    if 'america' in question or 'america' in slug:
                        america_markets.append(market)
                    if 'party' in question or 'party' in slug:
                        party_markets.append(market)
                
                print(f"  Elon markets: {len(elon_markets)}")
                print(f"  America markets: {len(america_markets)}")
                print(f"  Party markets: {len(party_markets)}")
                
                # Show some Elon markets
                if elon_markets and page == 0:
                    print("\n  Sample Elon markets:")
                    for m in elon_markets[:3]:
                        print(f"    Q: {m.get('question')[:60]}...")
                        print(f"    Slug: {m.get('market_slug')}")
                        print(f"    Active: {m.get('active')}")
                        print()
                
                next_cursor = data.get('next_cursor')
                if not next_cursor:
                    break
        
        # Try more specific search approaches
        print("\n\nTrying different search approaches:")
        
        # Maybe the market is archived or has special status
        special_params = [
            {"archived": "true"},
            {"closed": "true"},
            {"active": "false"},
        ]
        
        for params in special_params:
            print(f"\nChecking with params: {params}")
            response = await client.get(
                "https://clob.polymarket.com/markets",
                params={**params, "next_cursor": "MA=="},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    markets = data['data']
                    print(f"  Found {len(markets)} markets")
                    
                    # Quick check for our market
                    for market in markets[:100]:  # Check first 100
                        if 'elon' in market.get('question', '').lower() and 'america' in market.get('question', '').lower():
                            print(f"  Found potential match: {market.get('question')}")


if __name__ == "__main__":
    asyncio.run(debug_search())