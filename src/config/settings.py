"""
Configuration settings for Polymarket Analyzer.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # Polymarket CLOB API
    polymarket_clob_api_url: str = Field(
        default="https://gamma-api.polymarket.com",
        description="Polymarket CLOB API base URL"
    )
    polymarket_api_key: Optional[str] = Field(
        default=None,
        description="Polymarket API key (if required)"
    )
    
    # NewsAPI Configuration
    news_api_key: str = Field(
        ...,
        description="NewsAPI.org API key"
    )
    news_api_url: str = Field(
        default="https://newsapi.org/v2",
        description="NewsAPI base URL"
    )
    
    # Claude API Configuration
    claude_api_key: Optional[str] = Field(
        default=None,
        description="Claude API key for LLM-powered news analysis"
    )
    
    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    cache_ttl_seconds: int = Field(
        default=300,
        description="Cache TTL in seconds"
    )
    rate_limit_calls: int = Field(
        default=10,
        description="Rate limit calls per period"
    )
    rate_limit_period: int = Field(
        default=60,
        description="Rate limit period in seconds"
    )
    
    # Analysis Configuration
    min_market_volume: float = Field(
        default=1000.0,
        description="Minimum market volume to consider"
    )
    min_probability_spread: float = Field(
        default=0.1,
        description="Minimum probability spread for opportunities"
    )
    max_markets_to_analyze: int = Field(
        default=100,
        description="Maximum number of markets to analyze"
    )
    
    # Market Selection Filters
    market_categories: Optional[str] = Field(
        default=None,
        description="Comma-separated list of categories to include (e.g., 'politics,crypto,sports')"
    )
    market_keywords: Optional[str] = Field(
        default=None,
        description="Comma-separated list of keywords to search for (e.g., 'trump,bitcoin,election')"
    )
    sort_by_volume: bool = Field(
        default=True,
        description="Sort markets by volume (highest first)"
    )
    time_horizon_filter: Optional[str] = Field(
        default=None,
        description="Time horizon filter: 'closing_soon' (≤30 days), 'medium_term' (30-90 days), 'long_term' (>90 days)"
    )
    max_days_to_resolution: Optional[int] = Field(
        default=None,
        description="Maximum days until market resolution (None for no limit)"
    )
    min_days_to_resolution: Optional[int] = Field(
        default=None,
        description="Minimum days until market resolution (None for no limit)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()