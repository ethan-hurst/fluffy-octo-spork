#!/usr/bin/env python3
"""
Test Elon America party market
"""

import httpx
import asyncio

async def test_elon():
    """Test the Elon market."""
    
    slug = "will-elon-register-the-america-party-by"
    
    async with httpx.AsyncClient() as client:
        print(f"Searching for slug: {slug}\n")
        
        # Try direct slug search
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"slug": slug},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            print(f"Found {len(markets)} markets with exact slug")
            
            for market in markets:
                print(f"\nQuestion: {market.get('question')}")
                print(f"Slug: {market.get('slug')}")
                print(f"Active: {market.get('active')}")
                print(f"Volume: ${float(market.get('volume', 0)):,.0f}")
                print(f"Price: {market.get('lastTradePrice', 0):.1%}")
        
        # Try search
        print("\n\nTrying search for 'america party'...")
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"search": "america party", "limit": 20},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            print(f"Found {len(markets)} markets")
            
            for market in markets[:5]:
                q = market.get('question', '')
                if 'america' in q.lower() or 'party' in q.lower():
                    print(f"\n- {q}")
                    print(f"  Slug: {market.get('slug')}")
        
        # Try search for "elon register"
        print("\n\nTrying search for 'elon register'...")
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"search": "elon register", "limit": 20},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            for market in markets[:5]:
                q = market.get('question', '')
                if 'elon' in q.lower():
                    print(f"\n- {q}")
                    print(f"  Slug: {market.get('slug')}")


if __name__ == "__main__":
    asyncio.run(test_elon())