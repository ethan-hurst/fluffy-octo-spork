#!/usr/bin/env python3
"""
Debug script to test market fetching
"""

import httpx
import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analyzers.market_researcher import MarketResearcher


def test_url_parsing():
    """Test URL parsing."""
    researcher = MarketResearcher()
    
    test_urls = [
        "https://polymarket.com/event/bitcoin-150k-2025",
        "https://polymarket.com/event/will-bitcoin-reach-150k-2025",
        "https://polymarket.com/event/bitcoin-etf-approved-2025/will-bitcoin-etf-be-approved",
        "https://polymarket.com/market/0x123456",
    ]
    
    print("Testing URL parsing:")
    print("-" * 50)
    for url in test_urls:
        slug, condition_id = researcher.extract_market_info(url)
        print(f"URL: {url}")
        print(f"  Slug: {slug}")
        print(f"  Condition ID: {condition_id}")
        print()


def fetch_active_markets():
    """Fetch some active markets to see their structure."""
    print("Fetching active markets:")
    print("-" * 50)
    
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "active": "true",
            "closed": "false",
            "limit": 5
        }
    )
    
    if response.status_code == 200:
        markets = response.json()
        print(f"Found {len(markets)} markets\n")
        
        for i, market in enumerate(markets[:3]):
            print(f"Market {i+1}:")
            print(f"  Question: {market.get('question')}")
            print(f"  Slug: {market.get('slug')}")
            print(f"  Group Slug: {market.get('groupSlug')}")
            print(f"  Condition ID: {market.get('conditionId')}")
            print(f"  ID: {market.get('id')}")
            volume = float(market.get('volume', 0))
            print(f"  Volume: ${volume:,.0f}")
            print()
            
            # Generate example URLs
            if market.get('groupSlug'):
                print(f"  Example URL: https://polymarket.com/event/{market['groupSlug']}")
            if market.get('slug'):
                print(f"  Alt URL: https://polymarket.com/event/{market['slug']}")
            print()
    else:
        print(f"Error: {response.status_code}")


async def test_market_fetch(url):
    """Test fetching a specific market."""
    print(f"\nTesting market fetch for: {url}")
    print("-" * 50)
    
    researcher = MarketResearcher()
    slug, condition_id = researcher.extract_market_info(url)
    
    print(f"Extracted - Slug: {slug}, Condition ID: {condition_id}")
    
    # Try to fetch
    market = await researcher.fetch_market_data(slug, condition_id)
    
    if market:
        print("✅ Market found!")
        print(f"  Question: {market.question}")
        print(f"  Volume: ${market.volume:,.0f}")
    else:
        print("❌ Market not found")
        
        # Try to find similar markets
        print("\nSearching for similar markets...")
        response = httpx.get(
            "https://gamma-api.polymarket.com/markets",
            params={
                "active": "true",
                "closed": "false",
                "limit": 100
            }
        )
        
        if response.status_code == 200:
            markets = response.json()
            # Search for bitcoin markets
            bitcoin_markets = [m for m in markets if 'bitcoin' in m.get('question', '').lower()]
            
            if bitcoin_markets:
                print(f"\nFound {len(bitcoin_markets)} Bitcoin-related markets:")
                for m in bitcoin_markets[:5]:
                    print(f"  - {m.get('question')}")
                    print(f"    https://polymarket.com/event/{m.get('groupSlug', m.get('slug', ''))}")


async def main():
    print("=== POLYMARKET URL DEBUG ===\n")
    
    # Test URL parsing
    test_url_parsing()
    
    # Fetch active markets
    fetch_active_markets()
    
    # Test specific URL
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = "https://polymarket.com/event/bitcoin-150k-2025"
    
    await test_market_fetch(test_url)


if __name__ == "__main__":
    asyncio.run(main())