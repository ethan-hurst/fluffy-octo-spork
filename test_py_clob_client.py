#!/usr/bin/env python3
"""
Test the official py-clob-client for accessing current markets
"""

import asyncio
from typing import Optional

async def test_official_client():
    """Test using the official Polymarket Python client."""
    
    print("=== TESTING OFFICIAL PY-CLOB-CLIENT ===\n")
    
    try:
        # Try importing the client
        from py_clob_client import ClobClient
        print("✓ py-clob-client is installed")
        
    except ImportError:
        print("✗ py-clob-client not installed")
        print("\nTo install: pip install py-clob-client")
        print("\nLet's test the endpoints directly instead...")
        
        # Test the endpoints directly
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Test the markets endpoint with pagination
            print("\nTesting CLOB markets endpoint with pagination:")
            
            base_url = "https://clob.polymarket.com"
            next_cursor = "MA=="
            all_markets = []
            pages = 0
            
            while next_cursor and pages < 10:  # Limit to 10 pages
                response = await client.get(
                    f"{base_url}/markets",
                    params={"next_cursor": next_cursor},
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    markets = data.get('data', [])
                    all_markets.extend(markets)
                    
                    print(f"\nPage {pages + 1}:")
                    print(f"  Markets: {len(markets)}")
                    
                    # Check for Elon America Party market
                    for market in markets:
                        q = market.get('question', '').lower()
                        if 'elon' in q and 'america' in q and 'party' in q:
                            print(f"\n  🎯 FOUND IT!")
                            print(f"  Question: {market.get('question')}")
                            print(f"  Condition ID: {market.get('condition_id')}")
                            print(f"  Active: {market.get('active')}")
                            print(f"  Market Slug: {market.get('market_slug')}")
                            return market
                    
                    # Check for any 2024/2025 markets
                    recent_markets = [m for m in markets if '2024' in m.get('question', '') or '2025' in m.get('question', '')]
                    if recent_markets and pages == 0:
                        print(f"  Found {len(recent_markets)} markets with 2024/2025")
                        for m in recent_markets[:3]:
                            print(f"    - {m.get('question')[:60]}...")
                    
                    next_cursor = data.get('next_cursor')
                    pages += 1
                else:
                    print(f"Error: {response.status_code}")
                    break
            
            print(f"\n\nTotal markets checked: {len(all_markets)}")
            
            # Check date distribution
            print("\nChecking market dates:")
            years = {}
            for market in all_markets:
                q = market.get('question', '')
                for year in ['2020', '2021', '2022', '2023', '2024', '2025', '2026']:
                    if year in q:
                        years[year] = years.get(year, 0) + 1
            
            for year, count in sorted(years.items()):
                print(f"  {year}: {count} markets")
            
            # Try direct lookup with condition ID format
            print("\n\nTesting direct market lookup:")
            # Polymarket condition IDs are 66-character hex strings (0x + 64 hex chars)
            # Let's try to construct one from the slug
            
            import hashlib
            slug = "will-elon-register-the-america-party-by"
            
            # This is a guess - they might hash the slug or use a different method
            test_ids = [
                hashlib.sha256(slug.encode()).hexdigest(),
                hashlib.sha256(f"polymarket:{slug}".encode()).hexdigest(),
            ]
            
            for test_id in test_ids:
                condition_id = f"0x{test_id}"
                print(f"\nTrying condition ID: {condition_id[:20]}...")
                
                response = await client.get(
                    f"{base_url}/markets/{condition_id}",
                    timeout=10.0
                )
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    market = response.json()
                    print(f"Found: {market.get('question')}")


if __name__ == "__main__":
    asyncio.run(test_official_client())