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
        default="https://clob.polymarket.com",
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()