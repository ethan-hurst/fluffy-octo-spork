#!/usr/bin/env python3
"""
Debug Argentina search
"""

import httpx
import asyncio

async def debug_search():
    """Debug the search."""
    
    async with httpx.AsyncClient() as client:
        searches = [
            "chamber deputies argentina",
            "argentina election",
            "LLA argentina",
            "argentina 2025",
            "win most seats"
        ]
        
        for search_term in searches:
            print(f"\nSearching for: '{search_term}'")
            
            response = await client.get(
                "https://gamma-api.polymarket.com/markets",
                params={"search": search_term, "active": "true", "limit": 10},
                timeout=30.0
            )
            
            if response.status_code == 200:
                markets = response.json()
                print(f"Found {len(markets)} markets")
                
                for market in markets[:3]:
                    print(f"  - {market.get('question', 'No question')}")
                    
                    # Check if it's the Argentina election
                    if "Chamber of Deputies" in market.get('question', ''):
                        print(f"    ✓ FOUND ARGENTINA MARKET!")
                        print(f"    Slug: {market.get('slug')}")


if __name__ == "__main__":
    asyncio.run(debug_search())