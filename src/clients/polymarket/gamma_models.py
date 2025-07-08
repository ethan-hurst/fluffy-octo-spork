"""
Pydantic models for Polymarket Gamma API responses.
"""

from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class GammaMarket(BaseModel):
    """
    Market model for Gamma API response.
    """
    
    id: str = Field(..., description="Market ID")
    question: str = Field(..., description="Market question")
    conditionId: Optional[str] = Field(None, description="Condition ID")
    slug: str = Field(..., description="Market slug")
    description: Optional[str] = Field(None, description="Market description")
    active: bool = Field(..., description="Whether market is active")
    closed: bool = Field(..., description="Whether market is closed")
    archived: bool = Field(False, description="Whether market is archived")
    
    # Dates
    endDate: Optional[str] = Field(None, description="Market end date")
    startDate: Optional[str] = Field(None, description="Market start date")
    
    # Volume fields (different variations)
    volume: Optional[Union[float, str]] = Field(None, description="Total volume")
    volume24hrClob: Optional[Union[float, str]] = Field(None, description="24hr CLOB volume")
    volumeClob: Optional[Union[float, str]] = Field(None, description="Total CLOB volume")
    volume1wk: Optional[Union[float, str]] = Field(None, description="1 week volume")
    
    # Liquidity
    liquidityClob: Optional[Union[float, str]] = Field(None, description="CLOB liquidity")
    
    # Price data
    bestBid: Optional[Union[float, str]] = Field(None, description="Best bid price")
    bestAsk: Optional[Union[float, str]] = Field(None, description="Best ask price")
    lastTradePrice: Optional[Union[float, str]] = Field(None, description="Last trade price")
    
    # Other fields
    negRisk: bool = Field(False, description="Negative risk market")
    outcomes: Optional[str] = Field(None, description="Market outcomes")
    
    @field_validator('volume', 'volume24hrClob', 'volumeClob', 'volume1wk', 
                    'liquidityClob', 'bestBid', 'bestAsk', 'lastTradePrice', mode='before')
    def convert_to_float(cls, v):
        """Convert string numbers to float."""
        if isinstance(v, str):
            try:
                return float(v)
            except (ValueError, TypeError):
                return None
        return v
    
    def get_total_volume(self) -> float:
        """Get the highest volume from all volume fields."""
        volumes = [
            self.volume or 0,
            self.volume24hrClob or 0,
            self.volumeClob or 0,
            self.volume1wk or 0
        ]
        return max(volumes)
    
    def to_clob_market(self):
        """Convert Gamma market to CLOB market format."""
        from src.clients.polymarket.models import Market, Token
        
        # Parse outcomes to create tokens
        tokens = []
        if self.outcomes:
            try:
                import json
                outcomes = json.loads(self.outcomes)
                for i, outcome in enumerate(outcomes):
                    # Use best bid/ask as proxy for prices
                    if i == 0:  # Assume first outcome is YES
                        price = self.bestBid or self.lastTradePrice or 0.5
                    else:  # Assume second outcome is NO
                        price = 1 - (self.bestBid or self.lastTradePrice or 0.5)
                    
                    tokens.append(Token(
                        token_id=f"{self.id}_{i}",
                        outcome=outcome,
                        price=price
                    ))
            except:
                # Default binary outcomes
                yes_price = self.bestBid or self.lastTradePrice or 0.5
                tokens = [
                    Token(token_id=f"{self.id}_0", outcome="Yes", price=yes_price),
                    Token(token_id=f"{self.id}_1", outcome="No", price=1 - yes_price)
                ]
        
        # Parse end date
        end_date = None
        if self.endDate:
            try:
                end_date = datetime.fromisoformat(self.endDate.replace('Z', '+00:00'))
            except:
                pass
        
        return Market(
            condition_id=self.conditionId or self.id,
            question=self.question,
            description=self.description,
            market_slug=self.slug,
            tokens=tokens,
            minimum_order_size=5.0,  # Default value
            end_date_iso=end_date,
            active=self.active,
            closed=self.closed,
            volume=self.get_total_volume(),
            liquidity=self.liquidityClob
        )