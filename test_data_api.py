#!/usr/bin/env python3
"""
Test the Data API endpoints
"""

import httpx
import asyncio

async def test_data_api():
    """Test Data API endpoints."""
    
    print("=== TESTING DATA API (https://data-api.polymarket.com) ===\n")
    
    base_url = "https://data-api.polymarket.com"
    
    async with httpx.AsyncClient() as client:
        # Test various endpoints
        endpoints = [
            "/markets",
            "/events",
            "/positions",
            "/activity",
            "/",
        ]
        
        for endpoint in endpoints:
            try:
                print(f"\nTesting: {endpoint}")
                response = await client.get(
                    f"{base_url}{endpoint}",
                    timeout=10.0
                )
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response type: {type(data).__name__}")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())[:5]}")
                    elif isinstance(data, list):
                        print(f"List length: {len(data)}")
                
            except Exception as e:
                print(f"Error: {type(e).__name__} - {e}")
        
        # Also test if we need to use the gamma API differently
        print("\n\n=== RE-TESTING GAMMA API ===")
        
        gamma_url = "https://gamma-api.polymarket.com"
        
        # Maybe we need to check a different endpoint
        endpoints = [
            "/events",
            "/markets/lookup",
            "/search",
        ]
        
        for endpoint in endpoints:
            try:
                print(f"\nTesting: {gamma_url}{endpoint}")
                response = await client.get(
                    f"{gamma_url}{endpoint}",
                    timeout=10.0
                )
                print(f"Status: {response.status_code}")
                
            except Exception as e:
                print(f"Error: {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(test_data_api())