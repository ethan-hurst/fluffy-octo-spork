#!/usr/bin/env python3
"""
Test research function directly
"""

import asyncio
import sys
import logging
sys.path.append('.')

# Enable logging
logging.basicConfig(level=logging.INFO)

from src.analyzers.market_researcher import MarketResearcher

async def test():
    researcher = MarketResearcher()
    url = "https://polymarket.com/event/will-elon-register-the-america-party-by"
    
    print(f"Testing research on: {url}\n")
    
    result = await researcher.research_market(url)
    
    if result.get('success'):
        print("✅ Success!")
        print(f"Market: {result['market'].question}")
        print(f"Price: {result['price'].yes_price:.2%}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Test scraping directly
        print("\nTesting scraper directly...")
        scraped = await researcher._scrape_market_page(url)
        if scraped:
            print("✅ Scraping worked!")
        else:
            print("❌ Scraping failed")

if __name__ == "__main__":
    asyncio.run(test())