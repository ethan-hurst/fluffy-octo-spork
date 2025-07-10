#!/usr/bin/env python3
"""
Test the correct CLOB API endpoints
"""

import httpx
import asyncio
import json

async def test_clob_api():
    """Test CLOB API endpoints based on documentation."""
    
    print("=== TESTING CLOB API (https://clob.polymarket.com) ===\n")
    
    base_url = "https://clob.polymarket.com"
    
    async with httpx.AsyncClient() as client:
        # Test different endpoints
        endpoints = [
            "/markets",
            "/markets?limit=10",
            "/markets?active=true",
            "/markets?search=elon",
        ]
        
        for endpoint in endpoints:
            try:
                print(f"\nTesting: {endpoint}")
                response = await client.get(
                    f"{base_url}{endpoint}",
                    timeout=15.0
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if it's paginated
                    if isinstance(data, dict) and 'data' in data:
                        markets = data.get('data', [])
                        print(f"Markets returned: {len(markets)}")
                        print(f"Has next_cursor: {'next_cursor' in data}")
                        
                        # Show first market
                        if markets:
                            market = markets[0]
                            print(f"\nFirst market:")
                            print(f"  Question: {market.get('question', 'N/A')[:60]}...")
                            print(f"  Active: {market.get('active')}")
                            print(f"  Condition ID: {market.get('condition_id', 'N/A')[:20]}...")
                            
                            # Check for Elon markets
                            elon_markets = [m for m in markets if 'elon' in m.get('question', '').lower()]
                            if elon_markets:
                                print(f"\nFound {len(elon_markets)} Elon markets:")
                                for m in elon_markets[:3]:
                                    print(f"  - {m.get('question')}")
                    
                    elif isinstance(data, list):
                        print(f"Direct list of markets: {len(data)}")
                
            except Exception as e:
                print(f"Error: {e}")
        
        # Try specific market lookup methods
        print("\n\n=== TESTING SPECIFIC MARKET LOOKUP ===")
        
        # Test condition ID format (from our previous findings)
        test_condition_id = "0x9deb0baac40648821f96f01339229a422e2f5c877de55dc4dbf981f95a1e709c"
        
        try:
            print(f"\nTesting direct market lookup: /markets/{test_condition_id[:20]}...")
            response = await client.get(
                f"{base_url}/markets/{test_condition_id}",
                timeout=10.0
            )
            print(f"Status: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test search with specific terms
        print("\n\n=== TESTING SEARCH ===")
        
        search_terms = [
            "elon america party",
            "will-elon-register-the-america-party-by",
            "america party july"
        ]
        
        for term in search_terms:
            try:
                print(f"\nSearching for: '{term}'")
                response = await client.get(
                    f"{base_url}/markets",
                    params={"search": term},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        markets = data['data']
                        print(f"Found {len(markets)} markets")
                        
                        # Check for matches
                        for market in markets[:3]:
                            q = market.get('question', '')
                            if 'elon' in q.lower() or 'america' in q.lower():
                                print(f"  - {q}")
                
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_clob_api())