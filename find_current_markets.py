#!/usr/bin/env python3
"""Find any current markets in the API."""

import asyncio
import httpx
from datetime import datetime

async def find_current_markets():
    """Search for current markets."""
    async with httpx.AsyncClient() as client:
        print("Searching for current markets...")
        
        # Try to get more markets
        url = "https://gamma-api.polymarket.com/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 100  # Get more markets
        }
        
        response = await client.get(url, params=params, timeout=30.0)
        
        if response.status_code == 200:
            markets = response.json()
            print(f"Total markets returned: {len(markets)}")
            
            # Filter for future markets
            current_markets = []
            now = datetime.now()
            
            for market in markets:
                if market.get('endDate'):
                    try:
                        end_date = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                        if end_date > now.replace(tzinfo=end_date.tzinfo):
                            current_markets.append(market)
                    except:
                        pass
            
            print(f"Current/future markets: {len(current_markets)}")
            
            if current_markets:
                print("\nFirst 5 current markets:")
                for i, market in enumerate(current_markets[:5]):
                    print(f"\n{i+1}. {market['question'][:80]}...")
                    print(f"   End date: {market['endDate']}")
                    volume = float(market.get('volume', 0) or 0)
                    print(f"   Volume: ${volume:,.0f}")
            else:
                print("\nNo current markets found!")
                print("\nChecking if there are any markets with volume > 0...")
                
                markets_with_volume = [m for m in markets if float(m.get('volume', 0)) > 0]
                print(f"Markets with volume > 0: {len(markets_with_volume)}")
                
                if markets_with_volume:
                    print("\nFirst 3 markets with volume:")
                    for market in markets_with_volume[:3]:
                        volume = float(market.get('volume', 0) or 0)
                        print(f"- {market['question'][:60]}... (${volume:,.0f})")

if __name__ == "__main__":
    asyncio.run(find_current_markets())