#!/usr/bin/env python3
"""Test fetching real Polymarket markets."""

import asyncio
import httpx
from datetime import datetime

async def test_real_markets():
    """Test fetching real active markets from Polymarket."""
    
    # Try gamma API
    print("Testing Polymarket Gamma API...")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "closed": "false", "limit": 50}
        )
        
        if response.status_code == 200:
            markets = response.json()
            
            # Filter for markets with actual volume and future dates
            active_markets = []
            for m in markets:
                if (m.get('active') and 
                    not m.get('closed') and 
                    not m.get('archived') and
                    float(m.get('volume', 0) or 0) > 1000):
                    
                    # Check end date
                    end_date_str = m.get('endDate')
                    if end_date_str:
                        try:
                            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                            if end_date > datetime.now(end_date.tzinfo):
                                active_markets.append(m)
                        except:
                            pass
            
            print(f"\nFound {len(active_markets)} active markets with volume > $1000")
            
            # Sort by volume
            active_markets.sort(key=lambda x: float(x.get('volume', 0) or 0), reverse=True)
            
            # Show top 10
            print("\nTop 10 Active Markets by Volume:")
            print("-" * 100)
            for i, m in enumerate(active_markets[:10]):
                print(f"\n{i+1}. {m.get('question', 'No question')}")
                print(f"   URL: https://polymarket.com/event/{m.get('slug')}")
                print(f"   Volume: ${float(m.get('volume', 0)):,.2f}")
                print(f"   End Date: {m.get('endDate', 'N/A')}")
                
                # Check if URL is accessible
                if i < 3:  # Only check first 3
                    try:
                        check_response = await client.head(
                            f"https://polymarket.com/event/{m.get('slug')}",
                            follow_redirects=True
                        )
                        if check_response.status_code == 200:
                            print(f"   ✅ URL is valid")
                        else:
                            print(f"   ❌ URL returned status {check_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ URL check failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_markets())