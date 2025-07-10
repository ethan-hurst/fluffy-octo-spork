#!/usr/bin/env python3
"""
Analyze NYC mayoral market structure
"""

import httpx
import asyncio
import json

async def analyze_nyc():
    """Analyze NYC mayoral market."""
    
    # The URL suggests it might be a group of markets
    base_url = "https://gamma-api.polymarket.com"
    
    async with httpx.AsyncClient() as client:
        print("=== ANALYZING NYC MAYORAL MARKET ===\n")
        
        # Try different search approaches
        searches = [
            "new-york-city-mayoral",
            "nyc mayoral",
            "new york mayor",
            "NYC mayor 2025",
            "mayor",
        ]
        
        for search in searches:
            print(f"\nSearching for: {search}")
            response = await client.get(
                f"{base_url}/markets",
                params={"search": search, "limit": 20},
                timeout=30.0
            )
            
            if response.status_code == 200:
                markets = response.json()
                if markets:
                    print(f"Found {len(markets)} markets")
                    for market in markets[:5]:
                        print(f"  - {market.get('question')[:60]}...")
                        print(f"    Slug: {market.get('slug')}")
        
        # Try to get events/groups
        print("\n\nSearching for event groups...")
        response = await client.get(
            f"{base_url}/events",
            params={"search": "mayor", "limit": 100},
            timeout=30.0
        )
        
        if response.status_code == 200:
            events = response.json()
            print(f"Found {len(events)} events")
            
            for event in events[:10]:
                if event:
                    print(f"\nEvent: {event.get('title', 'No title')}")
                    print(f"Slug: {event.get('slug')}")
                    if 'markets' in event:
                        print(f"Markets: {len(event.get('markets', []))}")
        
        # Look for grouped markets by checking all markets
        print("\n\nChecking for mayoral candidate markets...")
        response = await client.get(
            f"{base_url}/markets",
            params={"active": "true", "limit": 1000},
            timeout=30.0
        )
        
        if response.status_code == 200:
            all_markets = response.json()
            
            # Common NYC mayoral candidates
            candidates = ['Adams', 'Yang', 'Garcia', 'Stringer', 'Donovan', 'Morales', 'McGuire']
            mayoral_markets = []
            
            for market in all_markets:
                question = market.get('question', '')
                slug = market.get('slug', '')
                
                # Check for NYC mayor related
                if any(term in question.lower() for term in ['nyc mayor', 'new york mayor', 'new york city mayor']):
                    mayoral_markets.append(market)
                elif any(name in question for name in candidates) and ('mayor' in question.lower() or 'nyc' in question.lower()):
                    mayoral_markets.append(market)
            
            if mayoral_markets:
                print(f"\nFound {len(mayoral_markets)} NYC mayoral related markets:")
                for market in mayoral_markets:
                    print(f"\n- {market.get('question')}")
                    print(f"  Slug: {market.get('slug')}")
                    print(f"  Group: {market.get('groupSlug')}")
                    print(f"  Price: {market.get('lastTradePrice')}")
                    print(f"  Volume: ${float(market.get('volume', 0)):,.0f}")

if __name__ == "__main__":
    asyncio.run(analyze_nyc())