"""
Rate limiter utility for API calls.
"""

import asyncio
import time
from typing import Dict, Optional

from src.config.settings import settings


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    """
    
    def __init__(self, calls_per_period: int, period_seconds: int):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_period: Number of calls allowed per period
            period_seconds: Period duration in seconds
        """
        self.calls_per_period = calls_per_period
        self.period_seconds = period_seconds
        self.tokens = calls_per_period
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
        
    async def acquire(self) -> None:
        """
        Acquire a token from the bucket.
        
        Blocks until a token is available.
        """
        async with self._lock:
            await self._wait_for_token()
            self.tokens -= 1
            
    async def _wait_for_token(self) -> None:
        """
        Wait for a token to become available.
        """
        while True:
            self._refill_tokens()
            
            if self.tokens > 0:
                return
                
            # Calculate sleep time until next refill
            time_since_refill = time.time() - self.last_refill
            sleep_time = max(0, self.period_seconds - time_since_refill)
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                
    def _refill_tokens(self) -> None:
        """
        Refill tokens based on elapsed time.
        """
        now = time.time()
        time_passed = now - self.last_refill
        
        if time_passed >= self.period_seconds:
            # Full refill
            self.tokens = self.calls_per_period
            self.last_refill = now
        else:
            # Partial refill based on time passed
            tokens_to_add = int(
                (time_passed / self.period_seconds) * self.calls_per_period
            )
            self.tokens = min(self.calls_per_period, self.tokens + tokens_to_add)
            
            if tokens_to_add > 0:
                self.last_refill = now


class APIRateLimiters:
    """
    Collection of rate limiters for different APIs.
    """
    
    def __init__(self):
        """Initialize rate limiters for different APIs."""
        self.polymarket = RateLimiter(
            calls_per_period=settings.rate_limit_calls,
            period_seconds=settings.rate_limit_period
        )
        
        self.newsapi = RateLimiter(
            calls_per_period=1000,  # NewsAPI allows 1000 requests per day
            period_seconds=86400    # 24 hours
        )
        
    def get_limiter(self, api_name: str) -> Optional[RateLimiter]:
        """
        Get rate limiter for a specific API.
        
        Args:
            api_name: Name of the API
            
        Returns:
            Optional[RateLimiter]: Rate limiter instance
        """
        return getattr(self, api_name, None)


# Global instance
rate_limiters = APIRateLimiters()