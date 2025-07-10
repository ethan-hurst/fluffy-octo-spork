#!/usr/bin/env python3
"""
Trace the market fetch process
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analyzers.market_researcher import MarketResearcher


async def trace_fetch():
    """Trace the fetch process."""
    
    researcher = MarketResearcher()
    
    # Test the exact URL
    url = "https://polymarket.com/event/will-elon-register-the-america-party-by?tid=1752033239940"
    
    print(f"1. Extracting info from URL: {url}")
    slug, condition_id = researcher.extract_market_info(url)
    print(f"   Slug: {slug}")
    print(f"   Condition ID: {condition_id}")
    
    print(f"\n2. Fetching market data...")
    market = await researcher.fetch_market_data(slug, condition_id)
    
    if market:
        print(f"\n3. Found market:")
        print(f"   Question: {market.question}")
        print(f"   Slug: {market.market_slug}")
        print(f"   Volume: ${market.volume:,.0f}")
        print(f"   Price: {market.last_trade_price:.1%}")
    else:
        print("   No market found")
    
    # Now let's manually check the API response
    import httpx
    async with httpx.AsyncClient() as client:
        print(f"\n4. Manual API check with slug: {slug}")
        
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"slug": slug},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Direct API response: {len(data)} markets")
            if data:
                print(f"   First market: {data[0].get('question')}")


if __name__ == "__main__":
    asyncio.run(trace_fetch())