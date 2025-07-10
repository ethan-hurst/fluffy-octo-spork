#!/usr/bin/env python3
"""
Debug slug lookup issue
"""

import httpx
import asyncio
import json

async def debug_slug():
    """Debug the slug lookup."""
    
    slug = "will-elon-register-the-america-party-by"
    
    async with httpx.AsyncClient() as client:
        print(f"1. Testing direct slug lookup: {slug}")
        
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"slug": slug},
            timeout=30.0
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   URL: {response.url}")
        
        if response.status_code == 200:
            markets = response.json()
            print(f"   Response: {len(markets)} markets")
            
            if markets:
                print(f"   Found market: {markets[0].get('question')}")
            else:
                print("   No markets returned for this slug")
        
        # Now test the fuzzy matching that's happening
        print(f"\n2. Testing what happens in fallback search...")
        
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "closed": "false", "limit": 500},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            
            # Find any Elon markets
            elon_markets = []
            for market in markets:
                if 'elon' in market.get('question', '').lower():
                    elon_markets.append(market)
            
            print(f"   Found {len(elon_markets)} Elon-related markets")
            
            # Check which one would match with our fuzzy logic
            from src.analyzers.market_researcher import MarketResearcher
            researcher = MarketResearcher()
            
            for market in elon_markets[:5]:
                matches = researcher._check_market_match(market, slug, None)
                print(f"\n   Market: {market.get('question')[:50]}...")
                print(f"   Slug: {market.get('slug')}")
                print(f"   Would match: {matches}")
                
                if matches:
                    # Debug why it matches
                    market_slug = market.get('slug', '').lower()
                    slug_parts = set(slug.split('-'))
                    market_parts = set(market_slug.split('-'))
                    overlap = slug_parts.intersection(market_parts)
                    print(f"   Overlap: {overlap}")
                    print(f"   Required: {max(3, int(len(slug_parts) * 0.6))}")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    asyncio.run(debug_slug())