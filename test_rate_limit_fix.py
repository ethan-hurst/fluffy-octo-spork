#!/usr/bin/env python3
"""
Test script to verify NewsAPI rate limiting fix.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from src.clients.news.client import NewsClient
from src.config.settings import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_rate_limiting():
    """Test rate limiting behavior."""
    logger.info("Testing NewsAPI rate limiting and error handling...")
    
    async with NewsClient() as client:
        # Test 1: Single request (should work with rate limiter)
        logger.info("\n=== Test 1: Single request ===")
        try:
            response = await client.get_everything(
                query="technology",
                from_date=datetime.now(timezone.utc) - timedelta(hours=24),
                page_size=10
            )
            logger.info(f"✓ Single request successful: {response.total_results} articles")
        except Exception as e:
            logger.error(f"✗ Single request failed: {e}")
        
        # Test 2: Cached request (should return from cache)
        logger.info("\n=== Test 2: Cached request ===")
        try:
            response = await client.get_everything(
                query="technology",
                from_date=datetime.now(timezone.utc) - timedelta(hours=24),
                page_size=10
            )
            logger.info(f"✓ Cached request successful: {response.total_results} articles")
        except Exception as e:
            logger.error(f"✗ Cached request failed: {e}")
        
        # Test 3: Test get_relevant_news with rate limiting
        logger.info("\n=== Test 3: Get relevant news (multiple queries) ===")
        try:
            articles = await client.get_relevant_news(
                hours_back=12,
                max_articles=20
            )
            logger.info(f"✓ Get relevant news successful: {len(articles)} articles")
            if articles:
                logger.info(f"  Latest article: {articles[0].title}")
        except Exception as e:
            logger.error(f"✗ Get relevant news failed: {e}")
        
        # Test 4: Breaking news
        logger.info("\n=== Test 4: Breaking news ===")
        try:
            articles = await client.get_breaking_news(max_articles=5)
            logger.info(f"✓ Breaking news successful: {len(articles)} articles")
        except Exception as e:
            logger.error(f"✗ Breaking news failed: {e}")


async def test_rapid_requests():
    """Test rapid requests to trigger rate limiting."""
    logger.info("\n=== Test 5: Rapid requests (should be rate limited) ===")
    
    async with NewsClient() as client:
        queries = ["crypto", "AI", "election", "sports", "finance"]
        results = []
        
        for i, query in enumerate(queries):
            try:
                logger.info(f"Request {i+1}/5: Querying '{query}'...")
                response = await client.get_everything(
                    query=query,
                    from_date=datetime.now(timezone.utc) - timedelta(hours=6),
                    page_size=5
                )
                results.append(f"✓ {query}: {response.total_results} results")
                logger.info(f"  Success: {response.total_results} results")
            except Exception as e:
                results.append(f"✗ {query}: {str(e)}")
                logger.error(f"  Failed: {e}")
            
            # Small delay to see rate limiting in action
            await asyncio.sleep(0.5)
        
        logger.info("\nSummary:")
        for result in results:
            logger.info(f"  {result}")


async def main():
    """Run all tests."""
    logger.info("Starting NewsAPI rate limit tests...")
    logger.info(f"API Key configured: {'Yes' if settings.news_api_key else 'No'}")
    logger.info(f"Rate limit: 1 request per 2 seconds")
    
    await test_rate_limiting()
    await test_rapid_requests()
    
    logger.info("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())