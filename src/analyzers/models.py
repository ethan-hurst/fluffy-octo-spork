"""
Pydantic models for market analysis.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OpportunityScore(BaseModel):
    """
    Score for a market opportunity.
    """
    
    value_score: float = Field(..., ge=0, le=1, description="Value opportunity score (0-1)")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in analysis (0-1)")
    volume_score: float = Field(..., ge=0, le=1, description="Market volume score (0-1)")
    time_score: float = Field(..., ge=0, le=1, description="Time until resolution score (0-1)")
    news_relevance_score: float = Field(..., ge=0, le=1, description="News relevance score (0-1)")
    
    @property
    def overall_score(self) -> float:
        """
        Calculate overall opportunity score.
        
        Returns:
            float: Weighted overall score (0-1)
        """
        weights = {
            "value": 0.3,
            "confidence": 0.25,
            "volume": 0.2,
            "time": 0.15,
            "news": 0.1
        }
        
        return (
            self.value_score * weights["value"] +
            self.confidence_score * weights["confidence"] +
            self.volume_score * weights["volume"] +
            self.time_score * weights["time"] +
            self.news_relevance_score * weights["news"]
        )


class MarketOpportunity(BaseModel):
    """
    Identified market opportunity.
    """
    
    condition_id: str = Field(..., description="Market condition ID")
    question: str = Field(..., description="Market question")
    description: Optional[str] = Field(None, description="Market description")
    category: Optional[str] = Field(None, description="Market category")
    
    # Market data
    current_yes_price: float = Field(..., description="Current YES price")
    current_no_price: float = Field(..., description="Current NO price")
    current_spread: float = Field(..., description="Current price spread")
    volume: Optional[float] = Field(None, description="Market volume")
    liquidity: Optional[float] = Field(None, description="Market liquidity")
    
    # Analysis
    fair_yes_price: float = Field(..., description="Estimated fair YES price")
    fair_no_price: float = Field(..., description="Estimated fair NO price")
    expected_return: float = Field(..., description="Expected return percentage")
    recommended_position: str = Field(..., description="Recommended position (YES/NO)")
    
    # Scoring
    score: OpportunityScore = Field(..., description="Opportunity scoring")
    
    # Metadata
    end_date: Optional[datetime] = Field(None, description="Market end date")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    reasoning: str = Field(..., description="Analysis reasoning")
    related_news: List[str] = Field(default_factory=list, description="Related news headlines")
    
    @property
    def profit_potential(self) -> float:
        """
        Calculate profit potential in dollars per dollar invested.
        
        Returns:
            float: Profit potential
        """
        if self.recommended_position == "YES":
            if self.current_yes_price > 0:
                return (self.fair_yes_price - self.current_yes_price) / self.current_yes_price
        else:
            if self.current_no_price > 0:
                return (self.fair_no_price - self.current_no_price) / self.current_no_price
        return 0.0
        
    @property
    def risk_level(self) -> str:
        """
        Categorize risk level based on scores.
        
        Returns:
            str: Risk level (LOW/MEDIUM/HIGH)
        """
        if self.score.confidence_score >= 0.8 and self.score.volume_score >= 0.7:
            return "LOW"
        elif self.score.confidence_score >= 0.6 and self.score.volume_score >= 0.5:
            return "MEDIUM"
        else:
            return "HIGH"


class AnalysisResult(BaseModel):
    """
    Complete analysis result.
    """
    
    opportunities: List[MarketOpportunity] = Field(..., description="Identified opportunities")
    total_markets_analyzed: int = Field(..., description="Total markets analyzed")
    analysis_duration_seconds: float = Field(..., description="Analysis duration")
    news_articles_processed: int = Field(..., description="News articles processed")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    
    @property
    def top_opportunities(self) -> List[MarketOpportunity]:
        """
        Get top opportunities sorted by overall score.
        
        Returns:
            List[MarketOpportunity]: Top opportunities
        """
        return sorted(
            self.opportunities, 
            key=lambda x: x.score.overall_score, 
            reverse=True
        )[:10]
        
    @property
    def high_confidence_opportunities(self) -> List[MarketOpportunity]:
        """
        Get opportunities with high confidence scores.
        
        Returns:
            List[MarketOpportunity]: High confidence opportunities
        """
        return [
            opp for opp in self.opportunities 
            if opp.score.confidence_score >= 0.7
        ]