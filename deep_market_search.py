#!/usr/bin/env python3
"""
Deep search for a specific market using various API endpoints
"""

import httpx
import asyncio
import json
from urllib.parse import quote

async def deep_search():
    """Search for the Israel-Hamas market using multiple methods."""
    
    slug = "israel-x-hamas-ceasefire-by-july-15"
    search_terms = ["israel hamas ceasefire", "israel", "hamas", "ceasefire july 15"]
    
    async with httpx.AsyncClient() as client:
        print("=== DEEP MARKET SEARCH ===\n")
        
        # Method 1: Direct slug lookup
        print("1. Trying direct slug lookup...")
        for endpoint in ["/markets", "/events"]:
            try:
                url = f"https://gamma-api.polymarket.com{endpoint}/{slug}"
                response = await client.get(url, timeout=10.0)
                print(f"   {endpoint}/{slug}: Status {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Found via {endpoint}!")
                    print(f"   Data: {json.dumps(data, indent=2)[:500]}...")
            except Exception as e:
                print(f"   Error: {e}")
        
        # Method 2: Search endpoint
        print("\n2. Trying search endpoint...")
        for term in search_terms:
            try:
                response = await client.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={"search": term, "limit": 100},
                    timeout=10.0
                )
                print(f"   Search '{term}': Status {response.status_code}")
                if response.status_code == 200:
                    markets = response.json()
                    print(f"   Found {len(markets)} markets")
                    for m in markets[:3]:
                        print(f"     - {m.get('question', 'No question')[:60]}...")
            except Exception as e:
                print(f"   Error: {e}")
        
        # Method 3: Get ALL markets with pagination
        print("\n3. Fetching ALL markets with pagination...")
        all_markets = []
        offset = 0
        
        while True:
            try:
                response = await client.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={"offset": offset, "limit": 100},
                    timeout=10.0
                )
                if response.status_code == 200:
                    markets = response.json()
                    if not markets:
                        break
                    all_markets.extend(markets)
                    print(f"   Fetched {len(markets)} markets (total: {len(all_markets)})")
                    
                    # Check if we found it
                    for m in markets:
                        if "israel" in m.get('slug', '').lower() and "hamas" in m.get('slug', '').lower():
                            print(f"   ✅ FOUND: {m.get('question')}")
                            print(f"      Slug: {m.get('slug')}")
                            print(f"      Active: {m.get('active')}, Closed: {m.get('closed')}")
                            return
                    
                    offset += 100
                    if offset > 2000:  # Safety limit
                        break
                else:
                    break
            except Exception as e:
                print(f"   Error: {e}")
                break
        
        print(f"\n   Total markets checked: {len(all_markets)}")
        
        # Method 4: Try the clob API
        print("\n4. Trying CLOB API...")
        try:
            response = await client.get(
                "https://clob.polymarket.com/markets",
                params={"next_cursor": "MA=="},
                timeout=10.0
            )
            print(f"   CLOB API: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:300]}...")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Method 5: Try strapi API
        print("\n5. Trying Strapi API...")
        try:
            # Try different condition IDs that might match
            condition_ids = [
                "0x" + "0" * 64,  # Placeholder
                slug,
            ]
            
            for cid in condition_ids:
                response = await client.get(
                    f"https://strapi-matic.poly.market/markets/{cid}",
                    timeout=10.0
                )
                print(f"   Strapi {cid[:20]}...: Status {response.status_code}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Method 6: Check if it's a multi-market event
        print("\n6. Checking for multi-market events...")
        try:
            response = await client.get(
                "https://gamma-api.polymarket.com/events",
                params={"active": True, "limit": 1000},
                timeout=10.0
            )
            if response.status_code == 200:
                events = response.json()
                print(f"   Found {len(events)} events")
                
                for event in events:
                    if "israel" in str(event).lower() and "hamas" in str(event).lower():
                        print(f"   Potential match: {event.get('title', 'No title')}")
                        print(f"   Markets: {event.get('markets', [])}")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(deep_search())