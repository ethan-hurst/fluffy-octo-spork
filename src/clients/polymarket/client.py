"""
Polymarket CLOB API client.
"""

import asyncio
import logging
from typing import Dict, List, Optional

import httpx
from httpx import AsyncClient

from src.config.settings import settings
from src.clients.polymarket.models import Market, MarketsResponse, MarketPrice

logger = logging.getLogger(__name__)


class PolymarketClient:
    """
    Client for interacting with Polymarket CLOB API.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Polymarket client.
        
        Args:
            base_url: API base URL (defaults to settings)
            api_key: API key (defaults to settings)
        """
        self.base_url = base_url or settings.polymarket_clob_api_url
        self.api_key = api_key or settings.polymarket_api_key
        self._client: Optional[AsyncClient] = None
        
    async def __aenter__(self) -> "PolymarketClient":
        """Async context manager entry."""
        self._client = AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=30.0
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers.
        
        For Polymarket CLOB API, authentication requires:
        - L1: Private key authentication with EIP-712 signatures
        - L2: API key authentication with HMAC signatures
        
        For now, we'll use minimal headers for public endpoints.
        
        Returns:
            Dict[str, str]: Request headers
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        # TODO: Implement proper Polymarket authentication
        # This would require either:
        # 1. L1 auth: POLY_ADDRESS, POLY_SIGNATURE, POLY_TIMESTAMP, POLY_NONCE
        # 2. L2 auth: POLY_ADDRESS, POLY_SIGNATURE, POLY_TIMESTAMP, POLY_API_KEY, POLY_PASSPHRASE
        
        if self.api_key:
            # Basic API key header (may not be sufficient for all endpoints)
            headers["POLY_API_KEY"] = self.api_key
            
        return headers
        
    async def get_markets(
        self, 
        next_cursor: Optional[str] = None,
        limit: int = 100
    ) -> MarketsResponse:
        """
        Get markets from Polymarket.
        
        Args:
            next_cursor: Pagination cursor
            limit: Number of results to return
            
        Returns:
            MarketsResponse: Markets data
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
            
        params = {}
        if next_cursor:
            params["next_cursor"] = next_cursor
        if limit:
            params["limit"] = limit
            
        try:
            response = await self._client.get("/markets", params=params)
            response.raise_for_status()
            data = response.json()
            return MarketsResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting markets: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting markets: {e}")
            raise
            
    async def get_all_active_markets(self, max_markets: Optional[int] = None) -> List[Market]:
        """
        Get all active markets, handling pagination.
        
        Args:
            max_markets: Maximum number of markets to fetch
            
        Returns:
            List[Market]: List of active markets
        """
        max_markets = max_markets or settings.max_markets_to_analyze
        all_markets = []
        next_cursor = None
        
        while len(all_markets) < max_markets:
            response = await self.get_markets(next_cursor=next_cursor)
            
            # Filter active markets
            active_markets = [m for m in response.data if m.active and not m.closed]
            all_markets.extend(active_markets)
            
            # Check if we have more pages
            if not response.next_cursor:
                break
            next_cursor = response.next_cursor
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.1)
            
        return all_markets[:max_markets]
        
    async def get_market_prices(self, market: Market) -> Optional[MarketPrice]:
        """
        Extract price information from a market.
        
        Args:
            market: Market object
            
        Returns:
            Optional[MarketPrice]: Price information
        """
        if len(market.tokens) < 2:
            logger.warning(f"Market {market.condition_id} has insufficient tokens")
            return None
            
        # Find YES and NO tokens (try multiple patterns)
        yes_token = None
        no_token = None
        
        for token in market.tokens:
            outcome_lower = token.outcome.lower()
            if any(keyword in outcome_lower for keyword in ["yes", "true", "will happen", "win"]):
                yes_token = token
            elif any(keyword in outcome_lower for keyword in ["no", "false", "will not happen", "lose"]):
                no_token = token
                
        # If still not found, use first two tokens if exactly 2 tokens exist
        if not yes_token or not no_token:
            if len(market.tokens) == 2:
                yes_token = market.tokens[0]  # Assume first is YES
                no_token = market.tokens[1]   # Assume second is NO
            else:
                logger.warning(f"Market {market.condition_id} missing YES/NO tokens")
                return None
            
        if yes_token.price is None or no_token.price is None:
            logger.warning(f"Market {market.condition_id} missing price data")
            return None
            
        return MarketPrice(
            condition_id=market.condition_id,
            yes_price=yes_token.price,
            no_price=no_token.price,
            spread=abs(yes_token.price - no_token.price)
        )