#!/usr/bin/env python3
"""Check Gamma API response."""

import asyncio
import httpx
import json
from datetime import datetime

async def check_gamma_api():
    """Check Gamma API response."""
    async with httpx.AsyncClient() as client:
        print("Checking Polymarket Gamma API...")
        
        # Try the gamma endpoint
        url = "https://gamma-api.polymarket.com/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 10
        }
        
        response = await client.get(url, params=params)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse type: {type(data)}")
            print(f"Number of markets: {len(data) if isinstance(data, list) else 'N/A'}")
            
            if isinstance(data, list) and data:
                market = data[0]
                print(f"\nFirst market:")
                print(f"- Question: {market.get('question', 'N/A')[:80]}...")
                print(f"- Active: {market.get('active', 'N/A')}")
                print(f"- Closed: {market.get('closed', 'N/A')}")
                print(f"- Volume: ${market.get('volume', 0):,.0f}")
                print(f"- End date: {market.get('endDate', 'N/A')}")
                
                # Check if it's a current market
                if market.get('endDate'):
                    try:
                        end_date = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                        now = datetime.now(end_date.tzinfo)
                        if end_date > now:
                            print(f"- Status: FUTURE (ends in {(end_date - now).days} days)")
                        else:
                            print(f"- Status: PAST (ended {(now - end_date).days} days ago)")
                    except:
                        pass
                
                # Save for inspection
                with open('gamma_response.json', 'w') as f:
                    json.dump(data[:5], f, indent=2)
                print("\nFirst 5 markets saved to gamma_response.json")
            else:
                print("\nNo markets in response!")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(check_gamma_api())