"""
Market filtering utilities for advanced market selection.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from src.clients.polymarket.models import Market
from src.config.settings import settings

logger = logging.getLogger(__name__)


class MarketFilter:
    """
    Advanced market filtering with multiple criteria.
    """
    
    def __init__(self):
        """Initialize market filter with settings."""
        self.categories = self._parse_comma_separated(settings.market_categories)
        self.keywords = self._parse_comma_separated(settings.market_keywords)
        self.sort_by_volume = settings.sort_by_volume
        self.time_horizon_filter = settings.time_horizon_filter
        self.max_days_to_resolution = settings.max_days_to_resolution
        self.min_days_to_resolution = settings.min_days_to_resolution
        
    def _parse_comma_separated(self, value: Optional[str]) -> List[str]:
        """
        Parse comma-separated string into list.
        
        Args:
            value: Comma-separated string
            
        Returns:
            List[str]: Parsed list
        """
        if not value:
            return []
        return [item.strip().lower() for item in value.split(',') if item.strip()]
        
    def filter_markets(self, markets: List[Market]) -> List[Market]:
        """
        Apply all filters to markets.
        
        Args:
            markets: List of markets to filter
            
        Returns:
            List[Market]: Filtered markets
        """
        logger.debug(f"Starting with {len(markets)} markets")
        
        # Apply filters
        filtered = markets
        
        # Category filter
        if self.categories:
            filtered = self._filter_by_category(filtered)
            logger.debug(f"After category filter: {len(filtered)} markets")
            
        # Keyword filter
        if self.keywords:
            filtered = self._filter_by_keywords(filtered)
            logger.debug(f"After keyword filter: {len(filtered)} markets")
            
        # Time horizon filter
        if self.time_horizon_filter or self.max_days_to_resolution or self.min_days_to_resolution:
            filtered = self._filter_by_time_horizon(filtered)
            logger.debug(f"After time filter: {len(filtered)} markets")
            
        # Sort by volume if requested
        if self.sort_by_volume:
            filtered = self._sort_by_volume(filtered)
            logger.debug("Markets sorted by volume (highest first)")
            
        logger.debug(f"Final filtered result: {len(filtered)} markets")
        return filtered
        
    def _filter_by_category(self, markets: List[Market]) -> List[Market]:
        """
        Filter markets by category.
        
        Args:
            markets: Markets to filter
            
        Returns:
            List[Market]: Filtered markets
        """
        filtered = []
        for market in markets:
            if market.category:
                category_lower = market.category.lower()
                if any(cat in category_lower for cat in self.categories):
                    filtered.append(market)
        return filtered
        
    def _filter_by_keywords(self, markets: List[Market]) -> List[Market]:
        """
        Filter markets by keywords in question or description.
        
        Args:
            markets: Markets to filter
            
        Returns:
            List[Market]: Filtered markets
        """
        filtered = []
        for market in markets:
            text_to_search = f"{market.question} {market.description or ''}".lower()
            if any(keyword in text_to_search for keyword in self.keywords):
                filtered.append(market)
        return filtered
        
    def _filter_by_time_horizon(self, markets: List[Market]) -> List[Market]:
        """
        Filter markets by time horizon.
        
        Args:
            markets: Markets to filter
            
        Returns:
            List[Market]: Filtered markets
        """
        filtered = []
        now = datetime.now(timezone.utc)
        
        for market in markets:
            if not market.end_date_iso:
                # If no end date and we have time filters, skip this market
                if self.time_horizon_filter or self.max_days_to_resolution or self.min_days_to_resolution:
                    continue
                else:
                    filtered.append(market)
                    continue
                    
            # Calculate days to resolution
            end_date = market.end_date_iso
            if end_date.tzinfo is not None:
                # Already timezone aware
                pass
            else:
                # Make timezone aware
                end_date = end_date.replace(tzinfo=timezone.utc)
                
            days_to_resolution = (end_date - now).days
            
            # Apply time horizon filter
            if self.time_horizon_filter:
                if self.time_horizon_filter == "closing_soon" and days_to_resolution > 30:
                    continue
                elif self.time_horizon_filter == "medium_term" and (days_to_resolution <= 30 or days_to_resolution > 90):
                    continue
                elif self.time_horizon_filter == "long_term" and days_to_resolution <= 90:
                    continue
                    
            # Apply min/max days filters
            if self.max_days_to_resolution and days_to_resolution > self.max_days_to_resolution:
                continue
            if self.min_days_to_resolution and days_to_resolution < self.min_days_to_resolution:
                continue
                
            filtered.append(market)
            
        return filtered
        
    def _sort_by_volume(self, markets: List[Market]) -> List[Market]:
        """
        Sort markets by volume (highest first).
        
        Args:
            markets: Markets to sort
            
        Returns:
            List[Market]: Sorted markets
        """
        return sorted(markets, key=lambda m: m.volume or 0, reverse=True)
        
    def get_filter_summary(self) -> str:
        """
        Get a summary of active filters.
        
        Returns:
            str: Filter summary
        """
        filters = []
        
        if self.categories:
            filters.append(f"Categories: {', '.join(self.categories)}")
            
        if self.keywords:
            filters.append(f"Keywords: {', '.join(self.keywords)}")
            
        if self.time_horizon_filter:
            filters.append(f"Time horizon: {self.time_horizon_filter}")
            
        if self.max_days_to_resolution:
            filters.append(f"Max days: {self.max_days_to_resolution}")
            
        if self.min_days_to_resolution:
            filters.append(f"Min days: {self.min_days_to_resolution}")
            
        if self.sort_by_volume:
            filters.append("Sorted by volume (highest first)")
            
        if not filters:
            return "No filters active - analyzing all markets"
            
        return "Active filters: " + " | ".join(filters)


# Global filter instance
market_filter = MarketFilter()