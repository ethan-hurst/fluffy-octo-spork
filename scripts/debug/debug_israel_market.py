#!/usr/bin/env python3
"""
Debug script for Israel market URL
"""

import httpx
import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analyzers.market_researcher import MarketResearcher


async def debug_israel_market():
    """Debug the Israel-Hamas ceasefire market."""
    
    url = "https://polymarket.com/event/israel-x-hamas-ceasefire-by-july-15?tid=1752029678911"
    
    researcher = MarketResearcher()
    
    # Test URL parsing
    print("1. Testing URL parsing:")
    print(f"   URL: {url}")
    slug, condition_id = researcher.extract_market_info(url)
    print(f"   Extracted slug: {slug}")
    print(f"   Extracted condition_id: {condition_id}")
    
    # Search for similar markets
    print("\n2. Searching for markets with 'israel' or 'hamas':")
    
    # First check active markets
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "active": "true",
            "closed": "false", 
            "limit": 500
        }
    )
    
    if response.status_code == 200:
        markets = response.json()
        
        # Find markets with israel or hamas
        matching_markets = []
        for market in markets:
            question = market.get('question', '').lower()
            slug_m = market.get('slug', '').lower()
            
            if 'israel' in question or 'hamas' in question or 'israel' in slug_m or 'hamas' in slug_m:
                matching_markets.append(market)
        
        print(f"   Found {len(matching_markets)} related markets:")
        
        for i, market in enumerate(matching_markets[:5]):
            print(f"\n   Market {i+1}:")
            print(f"   Question: {market.get('question')}")
            print(f"   Slug: {market.get('slug')}")
            print(f"   Group Slug: {market.get('groupSlug')}")
            print(f"   URL: https://polymarket.com/event/{market.get('slug', '')}")
            
            # Check if our slug would match
            market_slug = market.get('slug', '').lower()
            if slug:
                slug_clean = slug.lower().strip()
                if slug_clean in market_slug or market_slug in slug_clean:
                    print(f"   ✓ WOULD MATCH with partial matching")
                elif slug_clean.replace('-x-', '-') in market_slug.replace('-x-', '-'):
                    print(f"   ✓ WOULD MATCH with x/× normalization")
                else:
                    # Check fuzzy match
                    slug_parts = set(slug_clean.split('-'))
                    market_parts = set(market_slug.split('-'))
                    overlap = len(slug_parts.intersection(market_parts))
                    print(f"   Fuzzy match overlap: {overlap} parts")
                    if overlap >= min(3, len(slug_parts) - 1):
                        print(f"   ✓ WOULD MATCH with fuzzy matching")
    
    # Now check ALL markets (including closed)
    print("\n   Checking ALL markets (including closed)...")
    response2 = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "limit": 1000
        }
    )
    
    if response2.status_code == 200:
        all_markets = response2.json()
        
        # Find markets with the exact slug we're looking for
        for market in all_markets:
            market_slug = market.get('slug', '').lower()
            if slug and slug.lower() in market_slug:
                print(f"\n   Found potential match:")
                print(f"   Question: {market.get('question')}")
                print(f"   Slug: {market.get('slug')}")
                print(f"   Active: {market.get('active')}")
                print(f"   Closed: {market.get('closed')}")
                print(f"   End Date: {market.get('endDate')}")
    
    # Test actual fetch
    print("\n3. Testing market fetch:")
    market = await researcher.fetch_market_data(slug, condition_id)
    
    if market:
        print("   ✅ Market found!")
        print(f"   Question: {market.question}")
        print(f"   Volume: ${market.volume:,.0f}")
    else:
        print("   ❌ Market not found")
        print("\n   Possible reasons:")
        print("   - Market might be closed or inactive")
        print("   - Slug format might have changed")
        print("   - Market might use different slug than URL")


if __name__ == "__main__":
    asyncio.run(debug_israel_market())