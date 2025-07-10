#!/usr/bin/env python3
"""
Investigate why certain markets aren't available via API
"""

import httpx
import asyncio
import json
from datetime import datetime

async def investigate():
    """Investigate API coverage and market availability."""
    
    print("=== INVESTIGATING POLYMARKET API ===\n")
    
    async with httpx.AsyncClient() as client:
        # 1. Check total market count
        print("1. Checking API market coverage:")
        
        endpoints = [
            ("Active markets", {"active": "true", "closed": "false"}),
            ("Closed markets", {"active": "false", "closed": "true"}),
            ("All markets (no filter)", {}),
            ("With high limit", {"limit": 2000}),
        ]
        
        for name, params in endpoints:
            params["limit"] = params.get("limit", 1000)
            response = await client.get(
                "https://gamma-api.polymarket.com/markets",
                params=params,
                timeout=30.0
            )
            if response.status_code == 200:
                markets = response.json()
                print(f"   {name}: {len(markets)} markets")
                
                # Check if we hit the limit
                if len(markets) == params["limit"]:
                    print(f"     ⚠️  Hit limit of {params['limit']} - there may be more")
        
        # 2. Check different API endpoints
        print("\n2. Testing different API endpoints:")
        
        # Try CLOB API
        try:
            response = await client.get(
                "https://clob.polymarket.com/markets",
                params={"next_cursor": "MA=="},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   CLOB API: {response.status_code}")
                if 'data' in data:
                    print(f"   Markets in response: {len(data.get('data', []))}")
        except Exception as e:
            print(f"   CLOB API: Error - {e}")
        
        # Try Strapi API
        try:
            response = await client.get(
                "https://strapi-matic.poly.market/markets",
                timeout=10.0
            )
            print(f"   Strapi API: {response.status_code}")
        except Exception as e:
            print(f"   Strapi API: Error - {e}")
        
        # 3. Search for newest markets
        print("\n3. Checking market recency:")
        
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "limit": 100},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            
            # Check creation dates if available
            recent_markets = []
            for market in markets:
                # Look for date fields
                created = market.get('createdAt') or market.get('created_at')
                if created:
                    recent_markets.append((created, market.get('question', 'Unknown')))
            
            if recent_markets:
                recent_markets.sort(reverse=True)
                print("   Most recent markets:")
                for date, question in recent_markets[:5]:
                    print(f"     {date}: {question[:50]}...")
            else:
                print("   No creation date information available")
        
        # 4. Check pagination
        print("\n4. Testing pagination:")
        
        total_markets = set()
        for offset in [0, 500, 1000, 1500]:
            response = await client.get(
                "https://gamma-api.polymarket.com/markets",
                params={"offset": offset, "limit": 500},
                timeout=30.0
            )
            if response.status_code == 200:
                markets = response.json()
                print(f"   Offset {offset}: {len(markets)} markets")
                
                # Track unique markets
                for m in markets:
                    total_markets.add(m.get('conditionId', m.get('question', '')))
                
                if len(markets) < 500:
                    print(f"   Reached end at offset {offset}")
                    break
        
        print(f"   Total unique markets found: {len(total_markets)}")
        
        # 5. Search for Elon markets specifically
        print("\n5. Searching for Elon markets:")
        
        # Get a large batch and search manually
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 2000},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            elon_markets = []
            america_markets = []
            
            for market in markets:
                question = market.get('question', '').lower()
                slug = market.get('slug', '').lower()
                
                if 'elon' in question or 'elon' in slug:
                    elon_markets.append(market)
                if 'america' in question or 'america' in slug:
                    america_markets.append(market)
            
            print(f"   Found {len(elon_markets)} Elon-related markets")
            print(f"   Found {len(america_markets)} America-related markets")
            
            # Check for our specific market
            target_slug = "will-elon-register-the-america-party-by"
            found = False
            for market in markets:
                if target_slug in market.get('slug', '').lower():
                    found = True
                    print(f"\n   ✅ FOUND TARGET MARKET!")
                    print(f"   Question: {market.get('question')}")
                    print(f"   Active: {market.get('active')}")
                    print(f"   Closed: {market.get('closed')}")
                    break
            
            if not found:
                print(f"\n   ❌ Target market '{target_slug}' NOT found in {len(markets)} markets")
                
                # Check if it might be under a different slug
                for market in markets:
                    q = market.get('question', '').lower()
                    if 'elon' in q and 'america' in q and 'party' in q:
                        print(f"\n   Possible match:")
                        print(f"   Question: {market.get('question')}")
                        print(f"   Slug: {market.get('slug')}")


if __name__ == "__main__":
    asyncio.run(investigate())