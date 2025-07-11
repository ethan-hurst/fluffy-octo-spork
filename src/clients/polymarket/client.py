"""
Polymarket CLOB API client.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from httpx import AsyncClient

from src.config.settings import settings
from src.clients.polymarket.models import Market, MarketsResponse, MarketPrice
from src.clients.polymarket.gamma_models import GammaMarket
from src.utils.rate_limiter import rate_limiters

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
            # Apply rate limiting
            await rate_limiters.polymarket.acquire()
            
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
        Get all active markets with advanced filtering, handling pagination.
        
        Args:
            max_markets: Maximum number of markets to fetch (before filtering)
            
        Returns:
            List[Market]: List of filtered and sorted active markets
        """
        max_markets = max_markets or settings.max_markets_to_analyze
        all_markets = []
        
        # Use Gamma API if base URL is gamma-api
        if "gamma-api" in self.base_url:
            return await self._get_gamma_markets(max_markets)
        
        # Original CLOB API logic
        next_cursor = None
        
        # Fetch more markets initially to ensure we have enough after filtering
        fetch_limit = max_markets * 3  # Fetch 3x more to account for filtering
        
        while len(all_markets) < fetch_limit:
            response = await self.get_markets(next_cursor=next_cursor, limit=100)
            
            # Filter active markets and ensure they haven't ended
            now = datetime.now(timezone.utc)
            active_markets = []
            for m in response.data:
                if m.active and not m.closed:
                    # Check if market has ended
                    if m.end_date_iso:
                        # Make datetime comparison timezone-aware
                        end_date = m.end_date_iso
                        # If end_date is timezone-naive, assume UTC
                        if end_date.tzinfo is None:
                            end_date = end_date.replace(tzinfo=timezone.utc)
                        
                        # Only include if end date is in the future
                        if end_date > now:
                            active_markets.append(m)
                    else:
                        # No end date, include it
                        active_markets.append(m)
            
            all_markets.extend(active_markets)
            
            # Check if we have more pages
            if not response.next_cursor:
                break
            next_cursor = response.next_cursor
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.1)
            
        logger.debug(f"Fetched {len(all_markets)} active markets before filtering")
        
        # Apply advanced filtering
        from src.utils.market_filters import market_filter
        filtered_markets = market_filter.filter_markets(all_markets)
        
        # Return up to max_markets after filtering
        final_markets = filtered_markets[:max_markets]
        
        logger.debug(f"Returning {len(final_markets)} markets after filtering and limiting")
        logger.debug(f"Filter summary: {market_filter.get_filter_summary()}")
        
        return final_markets
    
    async def _get_gamma_markets(self, max_markets: int) -> List[Market]:
        """
        Get markets from Gamma API.
        
        Note: The API has a hard limit of ~500 unique active markets regardless
        of pagination attempts.
        
        Args:
            max_markets: Maximum number of markets to return
            
        Returns:
            List[Market]: List of active markets
        """
        try:
            params = {
                "active": "true",
                "closed": "false",
                "limit": 500  # API max limit
            }
            
            # Apply rate limiting
            await rate_limiters.polymarket.acquire()
            
            response = await self._client.get("/markets", params=params)
            response.raise_for_status()
            
            all_gamma_markets = []
            for market_data in response.json():
                    try:
                        gamma_market = GammaMarket(**market_data)
                        # Filter out archived or truly inactive markets
                        if (gamma_market.active and 
                            not gamma_market.closed and 
                            not gamma_market.archived and
                            gamma_market.get_total_volume() > settings.min_market_volume):
                            # Check if market has ended
                            if gamma_market.endDate:
                                try:
                                    end_date = datetime.fromisoformat(gamma_market.endDate.replace('Z', '+00:00'))
                                    if end_date > datetime.now(end_date.tzinfo):
                                        all_gamma_markets.append(gamma_market)
                                except:
                                    # If date parsing fails, skip the market
                                    logger.debug(f"Failed to parse end date for {gamma_market.question[:50]}")
                            else:
                                # No end date, include it
                                all_gamma_markets.append(gamma_market)
                    except Exception as e:
                        logger.debug(f"Skipping invalid market: {e}")
                        continue
                
            
            # Convert to CLOB format and sort by volume
            clob_markets = [gm.to_clob_market() for gm in all_gamma_markets]
            clob_markets.sort(key=lambda m: m.volume or 0, reverse=True)
            
            # Apply filters
            from src.utils.market_filters import market_filter
            filtered_markets = market_filter.filter_markets(clob_markets[:max_markets])
            
            logger.debug(f"Fetched {len(all_gamma_markets)} gamma markets, returning {len(filtered_markets)} after filtering")
            
            return filtered_markets
            
        except Exception as e:
            logger.error(f"Error fetching gamma markets: {e}")
            return []
        
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
    
    def _parse_market(self, data: Dict) -> Optional[Market]:
        """Parse market data from API response."""
        try:
            return Market(**data)
        except Exception as e:
            logger.error(f"Error parsing market data: {e}")
            return None