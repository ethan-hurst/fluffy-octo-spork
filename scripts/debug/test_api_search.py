#!/usr/bin/env python3
"""
Test Polymarket API search capabilities
"""

import httpx
import asyncio

async def test_search():
    """Test different search methods with the API."""
    
    base_url = "https://gamma-api.polymarket.com/markets"
    
    async with httpx.AsyncClient() as client:
        print("=== POLYMARKET API SEARCH CAPABILITIES ===\n")
        
        # Test 1: Search parameter
        print("1. Using 'search' parameter:")
        searches = [
            "elon america party",
            "america party",
            "elon register",
            "register america"
        ]
        
        for term in searches:
            response = await client.get(base_url, params={"search": term, "limit": 5})
            if response.status_code == 200:
                markets = response.json()
                print(f"\n   Search: '{term}' -> {len(markets)} results")
                for m in markets[:2]:
                    print(f"     - {m.get('question', 'No question')[:60]}...")
        
        # Test 2: Direct slug lookup
        print("\n\n2. Using 'slug' parameter:")
        slugs = [
            "will-elon-register-the-america-party-by",
            "will-elon-register-the-america-party",
            "elon-america-party"
        ]
        
        for slug in slugs:
            response = await client.get(base_url, params={"slug": slug})
            if response.status_code == 200:
                markets = response.json()
                print(f"   Slug: '{slug}' -> {len(markets)} results")
                if markets:
                    print(f"     Found: {markets[0].get('question')}")
        
        # Test 3: Filter parameters
        print("\n\n3. Other filter parameters available:")
        print("   - active: true/false")
        print("   - closed: true/false")
        print("   - tag: filter by tag")
        print("   - category: filter by category")
        print("   - limit: number of results")
        print("   - offset: pagination")
        
        # Test tag filter
        response = await client.get(base_url, params={"tag": "Politics", "limit": 3})
        if response.status_code == 200:
            markets = response.json()
            print(f"\n   Tag='Politics' -> {len(markets)} results")


if __name__ == "__main__":
    asyncio.run(test_search())