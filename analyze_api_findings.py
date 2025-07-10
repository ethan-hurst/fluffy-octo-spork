#!/usr/bin/env python3
"""
Analyze API findings
"""

import httpx
import asyncio
from datetime import datetime

async def analyze_findings():
    """Analyze what we've learned about the API."""
    
    print("=== API FINDINGS ANALYSIS ===\n")
    
    print("1. Key Findings:")
    print("   • Gamma API returns max 500 markets per request")
    print("   • CLOB API has more markets (2500+ found)")
    print("   • Most recent markets in Gamma API are from 2021")
    print("   • The APIs seem to be showing different/outdated data")
    
    print("\n2. Why the Elon America Party market might not be found:")
    print("   • Market is too new (created after API's last update)")
    print("   • API is showing cached/outdated data")
    print("   • Market might be on a different API version")
    print("   • Market might use different infrastructure")
    
    # Check if we can find ANY 2024/2025 markets
    print("\n3. Checking for recent markets (2024/2025):")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 500},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            
            recent_count = 0
            for market in markets:
                question = market.get('question', '')
                # Check for year references
                if '2024' in question or '2025' in question:
                    recent_count += 1
                    if recent_count <= 5:
                        print(f"   • {question[:60]}...")
            
            print(f"\n   Found {recent_count} markets mentioning 2024/2025")
            
            # Check active vs closed
            active_count = sum(1 for m in markets if m.get('active'))
            closed_count = sum(1 for m in markets if m.get('closed'))
            
            print(f"\n   Market status:")
            print(f"   • Active: {active_count}")
            print(f"   • Closed: {closed_count}")
            print(f"   • Neither: {len(markets) - active_count - closed_count}")
    
    print("\n4. Possible Solutions:")
    print("   • Use a different API endpoint (if available)")
    print("   • Contact Polymarket about API access")
    print("   • The market might only be available on their website")
    print("   • Web scraping might be necessary for newest markets")
    
    # Try one more thing - check if there's a GraphQL endpoint
    print("\n5. Checking for other endpoints:")
    
    endpoints = [
        "https://polymarket.com/api/markets",
        "https://api.polymarket.com/markets", 
        "https://gamma-api.polymarket.com/graphql",
        "https://polymarket.com/graphql",
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            try:
                response = await client.get(endpoint, timeout=5.0)
                print(f"   {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"   {endpoint}: Failed - {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(analyze_findings())