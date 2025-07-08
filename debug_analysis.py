#!/usr/bin/env python3
"""Debug script to investigate why no opportunities are found."""

import asyncio
import logging
from datetime import datetime

from src.clients.polymarket.client import PolymarketClient
from src.clients.news.client import NewsClient
from src.analyzers.market_analyzer import MarketAnalyzer
from src.analyzers.news_correlator import NewsCorrelator
from src.config.settings import settings

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def debug_analysis():
    """Run analysis with debug output."""
    print("\n=== DEBUG ANALYSIS ===\n")
    
    # Initialize clients
    polymarket_client = PolymarketClient()
    news_client = NewsClient()
    analyzer = MarketAnalyzer()
    correlator = NewsCorrelator()
    
    try:
        # 1. Fetch markets
        print("1. Fetching markets...")
        async with polymarket_client:
            markets = await polymarket_client.get_all_active_markets(max_markets=10)
            print(f"   - Found {len(markets)} active markets")
            
            # Show first few markets
            for i, market in enumerate(markets[:3]):
                print(f"\n   Market {i+1}:")
                print(f"   - Question: {market.question}")
                print(f"   - Volume: ${market.volume:,.2f}")
                print(f"   - Tokens: {len(market.tokens)} tokens")
                if market.tokens:
                    for token in market.tokens:
                        print(f"     - {token.outcome}: ${token.price:.2f}")
            
            # 2. Get market prices
            print("\n2. Getting market prices...")
            market_prices = []
            for market in markets:
                price = await polymarket_client.get_market_prices(market)
                if price:
                    market_prices.append(price)
                    if len(market_prices) <= 3:
                        print(f"   - {market.question[:50]}...")
                        print(f"     YES: ${price.yes_price:.2f}, NO: ${price.no_price:.2f}, Spread: ${price.spread:.2f}")
        
        # 3. Fetch news (skip if no API key)
        print("\n3. Fetching news...")
        news_articles = []
        if settings.news_api_key and settings.news_api_key != "your_newsapi_key_here":
            async with news_client:
                news_articles = await news_client.get_relevant_news(hours_back=24, max_articles=20)
                print(f"   - Found {len(news_articles)} relevant news articles")
        else:
            print("   - Skipping news (no API key configured)")
        
        # 4. Run analysis
        print("\n4. Running analysis...")
        print(f"   - Min volume threshold: ${settings.min_market_volume:,.2f}")
        print(f"   - Min probability spread: {settings.min_probability_spread:.2%}")
        
        result = await analyzer.analyze_markets(markets, market_prices, news_articles)
        
        print(f"\n5. Analysis Results:")
        print(f"   - Total markets analyzed: {result.total_markets_analyzed}")
        print(f"   - Opportunities found: {len(result.opportunities)}")
        print(f"   - Analysis duration: {result.analysis_duration_seconds:.2f} seconds")
        
        if result.opportunities:
            print("\n   Found opportunities:")
            for opp in result.opportunities:
                print(f"\n   - {opp.question}")
                print(f"     Current: YES ${opp.current_yes_price:.2f}, NO ${opp.current_no_price:.2f}")
                print(f"     Fair: YES ${opp.fair_yes_price:.2f}, NO ${opp.fair_no_price:.2f}")
                print(f"     Recommendation: {opp.recommended_position}")
                print(f"     Expected return: {opp.expected_return:.1f}%")
        else:
            print("\n   No opportunities found!")
            print("\n   Possible reasons:")
            print("   - Markets are efficiently priced")
            print("   - Spread threshold too high (current: {:.2%})".format(settings.min_probability_spread))
            print("   - Volume threshold too high (current: ${:,.2f})".format(settings.min_market_volume))
            print("   - Fair value engine being too conservative")
            
            # Let's check why markets were filtered
            print("\n6. Checking why markets were filtered...")
            for i, market in enumerate(markets[:5]):
                print(f"\n   Market {i+1}: {market.question[:60]}...")
                
                # Check volume
                if market.volume and market.volume < settings.min_market_volume:
                    print(f"   ❌ Volume too low: ${market.volume:,.2f} < ${settings.min_market_volume:,.2f}")
                else:
                    print(f"   ✓ Volume OK: ${market.volume:,.2f}")
                
                # Get price
                price = next((p for p in market_prices if p.condition_id == market.condition_id), None)
                if price:
                    print(f"   - Current prices: YES ${price.yes_price:.2f}, NO ${price.no_price:.2f}")
                    print(f"   - Spread: ${price.spread:.2f}")
                else:
                    print("   ❌ No price data available")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(debug_analysis())