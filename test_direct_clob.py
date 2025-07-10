#!/usr/bin/env python3
"""
Test CLOB API directly with the condition ID we found
"""

import httpx
import asyncio

async def test_clob():
    """Test CLOB API with known condition ID."""
    
    condition_id = "0xd1cb040420a6877ec2b3e5e0901ed2029d85b42d5c1b939cecc27071c8536b0e"
    
    async with httpx.AsyncClient() as client:
        print(f"Testing CLOB API with condition ID: {condition_id}\n")
        
        # Try different endpoints
        endpoints = [
            f"https://clob.polymarket.com/markets/{condition_id}",
            f"https://clob.polymarket.com/markets?condition_id={condition_id}",
            f"https://gamma-api.polymarket.com/markets?conditionId={condition_id}",
            f"https://data-api.polymarket.com/markets/{condition_id}"
        ]
        
        for url in endpoints:
            print(f"Trying: {url}")
            try:
                response = await client.get(url, timeout=10.0)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, dict):
                        if 'data' in data and isinstance(data['data'], list):
                            # List response
                            print(f"  Found {len(data['data'])} markets")
                            for market in data['data'][:1]:  # First market only
                                print(f"  Market: {market.get('question', market.get('title', 'N/A'))[:60]}...")
                                print(f"  Condition ID: {market.get('condition_id', market.get('conditionId', 'N/A'))}")
                        else:
                            # Direct market response
                            print(f"  Market: {data.get('question', data.get('title', 'N/A'))[:60]}...")
                            print(f"  Active: {data.get('active', 'N/A')}")
                            print(f"  Volume: {data.get('volume', 'N/A')}")
                    elif isinstance(data, list):
                        print(f"  Found {len(data)} markets")
                        for market in data[:1]:
                            print(f"  Market: {market.get('question', 'N/A')[:60]}...")
                else:
                    print(f"  Error: {response.text[:100]}...")
            except Exception as e:
                print(f"  Exception: {str(e)}")
            print()


if __name__ == "__main__":
    asyncio.run(test_clob())