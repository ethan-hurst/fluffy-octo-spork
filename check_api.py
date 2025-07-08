#!/usr/bin/env python3
"""Check Polymarket API response."""

import asyncio
import httpx
import json

async def check_api():
    """Check raw API response."""
    async with httpx.AsyncClient() as client:
        print("Checking Polymarket CLOB API...")
        
        # Try the main endpoint
        url = "https://clob.polymarket.com/markets"
        response = await client.get(url, params={"limit": 10})
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse keys: {list(data.keys())}")
            print(f"Count: {data.get('count', 'N/A')}")
            print(f"Data length: {len(data.get('data', []))}")
            
            # Show first market if available
            if data.get('data'):
                market = data['data'][0]
                print(f"\nFirst market:")
                print(f"- Question: {market.get('question', 'N/A')}")
                print(f"- Active: {market.get('active', 'N/A')}")
                print(f"- Closed: {market.get('closed', 'N/A')}")
                print(f"- Volume: {market.get('volume', 'N/A')}")
                print(f"- Tokens: {len(market.get('tokens', []))}")
                
                # Save full response for inspection
                with open('api_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("\nFull response saved to api_response.json")
            else:
                print("\nNo markets in response!")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(check_api())