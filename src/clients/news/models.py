"""
Pydantic models for NewsAPI responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NewsSource(BaseModel):
    """
    News source information.
    """
    
    id: Optional[str] = Field(None, description="Source ID")
    name: str = Field(..., description="Source name")


class NewsArticle(BaseModel):
    """
    News article information.
    """
    
    source: NewsSource = Field(..., description="Article source")
    author: Optional[str] = Field(None, description="Article author")
    title: str = Field(..., description="Article title")
    description: Optional[str] = Field(None, description="Article description")
    url: str = Field(..., description="Article URL")
    url_to_image: Optional[str] = Field(None, description="Article image URL")
    published_at: datetime = Field(..., description="Publication date")
    content: Optional[str] = Field(None, description="Article content")
    
    @property
    def relevance_keywords(self) -> List[str]:
        """
        Extract potential keywords for market relevance.
        
        Returns:
            List[str]: Keywords that might be relevant to prediction markets
        """
        text = f"{self.title} {self.description or ''}"
        
        # Common prediction market keywords
        keywords = [
            "election", "vote", "poll", "candidate", "president", "congress",
            "cryptocurrency", "bitcoin", "ethereum", "crypto", "blockchain",
            "market", "stock", "price", "inflation", "economy", "recession",
            "climate", "weather", "temperature", "hurricane", "earthquake",
            "sports", "game", "championship", "tournament", "olympics",
            "technology", "ai", "artificial intelligence", "tech", "startup",
            "policy", "regulation", "law", "legislation", "court", "ruling"
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
                
        return found_keywords


class NewsResponse(BaseModel):
    """
    Response from NewsAPI.
    """
    
    status: str = Field(..., description="Response status")
    total_results: Optional[int] = Field(None, alias="totalResults", description="Total number of results")
    articles: List[NewsArticle] = Field(..., description="List of articles")
    
    @property
    def relevant_articles(self) -> List[NewsArticle]:
        """
        Filter articles that might be relevant to prediction markets.
        
        Returns:
            List[NewsArticle]: Articles with market-relevant keywords
        """
        return [article for article in self.articles if article.relevance_keywords]