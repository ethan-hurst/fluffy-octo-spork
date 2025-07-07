"""
Simple in-memory caching mechanism for API responses.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional

from src.config.settings import settings


class CacheEntry:
    """
    Cache entry with expiration time.
    """
    
    def __init__(self, data: Any, ttl_seconds: int):
        """
        Initialize cache entry.
        
        Args:
            data: Data to cache
            ttl_seconds: Time to live in seconds
        """
        self.data = data
        self.expires_at = time.time() + ttl_seconds
        
    def is_expired(self) -> bool:
        """
        Check if cache entry is expired.
        
        Returns:
            bool: True if expired
        """
        return time.time() > self.expires_at


class AsyncCache:
    """
    Async in-memory cache with TTL support.
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default TTL in seconds
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found/expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
                
            if entry.is_expired():
                del self._cache[key]
                return None
                
            return entry.data
            
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (defaults to default_ttl)
        """
        ttl = ttl or self.default_ttl
        
        async with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key was found and deleted
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
            
    async def clear(self) -> None:
        """
        Clear all cache entries.
        """
        async with self._lock:
            self._cache.clear()
            
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            int: Number of expired entries removed
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                
            return len(expired_keys)
            
    def _make_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """
        Create cache key from arguments.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            str: Cache key
        """
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
            
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
            
        return ":".join(key_parts)


class APICache:
    """
    Cache specifically for API responses.
    """
    
    def __init__(self):
        """Initialize API cache."""
        self.cache = AsyncCache(default_ttl=settings.cache_ttl_seconds)
        
    async def get_markets(self, next_cursor: Optional[str] = None) -> Optional[Any]:
        """
        Get cached markets response.
        
        Args:
            next_cursor: Pagination cursor
            
        Returns:
            Optional[Any]: Cached response or None
        """
        key = self.cache._make_key("markets", next_cursor=next_cursor)
        return await self.cache.get(key)
        
    async def set_markets(
        self, 
        response: Any, 
        next_cursor: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache markets response.
        
        Args:
            response: Markets response
            next_cursor: Pagination cursor
            ttl: TTL in seconds
        """
        key = self.cache._make_key("markets", next_cursor=next_cursor)
        await self.cache.set(key, response, ttl)
        
    async def get_news(self, query: str, hours_back: int = 24) -> Optional[Any]:
        """
        Get cached news response.
        
        Args:
            query: News query
            hours_back: Hours back to search
            
        Returns:
            Optional[Any]: Cached response or None
        """
        key = self.cache._make_key("news", query=query, hours_back=hours_back)
        return await self.cache.get(key)
        
    async def set_news(
        self, 
        response: Any, 
        query: str, 
        hours_back: int = 24,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache news response.
        
        Args:
            response: News response
            query: News query
            hours_back: Hours back to search
            ttl: TTL in seconds
        """
        key = self.cache._make_key("news", query=query, hours_back=hours_back)
        await self.cache.set(key, response, ttl)
        
    async def cleanup(self) -> int:
        """
        Clean up expired entries.
        
        Returns:
            int: Number of expired entries removed
        """
        return await self.cache.cleanup_expired()


# Global instance
api_cache = APICache()