#!/usr/bin/env python3
"""
Check what markets are available with specific keywords
"""

import httpx
import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def check_markets():
    """Check available markets."""
    
    print("Searching for markets...\n")
    
    # Search for markets
    async with httpx.AsyncClient() as client:
        # Get all markets (including closed)
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={
                "limit": 1000
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            print(f"Total markets found: {len(markets)}")
            
            # Filter markets containing certain keywords
            keywords = ['israel', 'hamas', 'ceasefire', 'gaza', 'bitcoin', '120k']
            
            for keyword in keywords:
                print(f"\n--- Markets with '{keyword}' ---")
                matching = [m for m in markets if keyword.lower() in m.get('question', '').lower() or keyword.lower() in m.get('slug', '').lower()]
                
                for market in matching[:5]:  # Show first 5
                    print(f"\nQuestion: {market.get('question')}")
                    print(f"Slug: {market.get('slug')}")
                    print(f"Active: {market.get('active')}")
                    print(f"Closed: {market.get('closed')}")
                    print(f"Volume: ${float(market.get('volume', 0)):,.0f}")
                    print(f"End Date: {market.get('endDate')}")
                    print(f"URL: https://polymarket.com/event/{market.get('slug')}")
            
            # Check for the specific slug
            specific_slug = "israel-x-hamas-ceasefire-by-july-15"
            print(f"\n--- Searching for specific slug: {specific_slug} ---")
            
            found = False
            for market in markets:
                if specific_slug in market.get('slug', '').lower():
                    print(f"\nFOUND!")
                    print(f"Question: {market.get('question')}")
                    print(f"Slug: {market.get('slug')}")
                    print(f"Active: {market.get('active')}")
                    print(f"Closed: {market.get('closed')}")
                    found = True
                    break
            
            if not found:
                print("NOT FOUND - This market is not available in the API")
                
                # Check variations
                print("\n--- Checking slug variations ---")
                variations = [
                    "israel-hamas-ceasefire",
                    "israel-ceasefire",
                    "hamas-ceasefire",
                    "ceasefire-july",
                    "israel-x-hamas"
                ]
                
                for variation in variations:
                    matches = [m for m in markets if variation in m.get('slug', '').lower()]
                    if matches:
                        print(f"\nFound {len(matches)} markets with '{variation}':")
                        for m in matches[:3]:
                            print(f"  - {m.get('slug')}")


if __name__ == "__main__":
    asyncio.run(check_markets())