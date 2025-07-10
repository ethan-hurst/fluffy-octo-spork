#!/usr/bin/env python3
"""
Test the complete scraping flow
"""

import asyncio
import sys
sys.path.append('.')

from src.analyzers.market_researcher import MarketResearcher

async def test_scraper():
    """Test scraping with condition ID extraction."""
    
    researcher = MarketResearcher()
    url = "https://polymarket.com/event/will-elon-register-the-america-party-by?tid=1752033239940"
    
    print(f"Testing scraper on: {url}\n")
    
    # Test the scraping method directly
    result = await researcher._scrape_market_page(url)
    
    if result:
        print("✅ Scraping successful!")
        print(f"\nMarket: {result['market'].question}")
        print(f"Condition ID: {result['market'].condition_id}")
        print(f"Price: {result['price'].yes_price:.2%}")
        print(f"Volume: ${result['market'].volume:,.2f}")
        print(f"Note: {result.get('note', '')}")
        
        if result.get('recommendation'):
            rec = result['recommendation']
            print(f"\nRecommendation: {rec['position']}")
            print(f"Confidence: {rec['confidence']:.2%}")
            print(f"Reasons: {', '.join(rec['reasons'])}")
    else:
        print("❌ Scraping failed")
        
        # Try the full research flow
        print("\nTrying full research flow...")
        full_result = await researcher.research_market(url)
        
        if full_result.get('success'):
            print("✅ Full research successful!")
            print(f"Market: {full_result['market'].question}")
        else:
            print(f"❌ Full research failed: {full_result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(test_scraper())