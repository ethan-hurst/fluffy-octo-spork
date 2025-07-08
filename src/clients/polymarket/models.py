"""
Pydantic models for Polymarket CLOB API responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """
    Token information for a market.
    """
    
    token_id: str = Field(..., description="Token ID")
    outcome: str = Field(..., description="Outcome description")
    price: Optional[float] = Field(None, description="Current price")
    


class Rewards(BaseModel):
    """
    Rewards information for a market.
    """
    
    min_size: Optional[float] = Field(None, description="Minimum order size for rewards")
    max_spread: Optional[float] = Field(None, description="Maximum spread for rewards")
    

class Market(BaseModel):
    """
    Polymarket market information.
    """
    
    condition_id: str = Field(..., description="Market condition ID")
    question_id: Optional[str] = Field(None, description="Question ID")
    question: str = Field(..., description="Market question")
    description: Optional[str] = Field(None, description="Market description")
    market_slug: Optional[str] = Field(None, description="Market URL slug")
    tokens: List[Token] = Field(..., description="Binary token pair")
    rewards: Optional[Rewards] = Field(None, description="Rewards information")
    minimum_order_size: float = Field(..., description="Minimum order size")
    category: Optional[str] = Field(None, description="Market category")
    end_date_iso: Optional[datetime] = Field(None, description="Market end date")
    active: bool = Field(..., description="Whether market is active")
    closed: bool = Field(..., description="Whether market is closed")
    volume: Optional[float] = Field(None, description="Total volume")
    liquidity: Optional[float] = Field(None, description="Total liquidity")
    

class MarketsResponse(BaseModel):
    """
    Response from markets endpoint.
    """
    
    limit: int = Field(..., description="Results per page")
    count: int = Field(..., description="Total results")
    next_cursor: Optional[str] = Field(None, description="Pagination cursor")
    data: List[Market] = Field(..., description="List of markets")


class MarketPrice(BaseModel):
    """
    Market price information.
    """
    
    condition_id: str = Field(..., description="Market condition ID")
    yes_price: float = Field(..., description="Yes outcome price")
    no_price: float = Field(..., description="No outcome price")
    spread: float = Field(..., description="Price spread")
    
    @property
    def implied_probability(self) -> float:
        """
        Calculate implied probability from yes price.
        
        Returns:
            float: Implied probability (0-1)
        """
        return self.yes_price