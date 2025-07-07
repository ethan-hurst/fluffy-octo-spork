"""
News correlator for matching news articles with prediction markets.
"""

import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple

from src.clients.news.models import NewsArticle
from src.clients.polymarket.models import Market

logger = logging.getLogger(__name__)


class NewsCorrelator:
    """
    Correlates news articles with prediction markets.
    """
    
    def __init__(self):
        """Initialize news correlator."""
        self.keyword_categories = self._build_keyword_categories()
        
    def _build_keyword_categories(self) -> Dict[str, Set[str]]:
        """
        Build keyword categories for matching.
        
        Returns:
            Dict[str, Set[str]]: Keyword categories
        """
        return {
            "politics": {
                "election", "vote", "voting", "poll", "polls", "candidate", "president",
                "presidential", "congress", "senate", "house", "republican", "democrat",
                "biden", "trump", "harris", "campaign", "primary", "ballot", "electoral"
            },
            "crypto": {
                "bitcoin", "ethereum", "crypto", "cryptocurrency", "blockchain", "btc",
                "eth", "coinbase", "binance", "crypto", "defi", "nft", "token", "mining",
                "wallet", "exchange", "satoshi", "altcoin", "dogecoin", "litecoin"
            },
            "economy": {
                "economy", "economic", "inflation", "recession", "gdp", "unemployment",
                "jobs", "employment", "fed", "federal reserve", "interest rate", "stock",
                "market", "trading", "nasdaq", "dow", "s&p", "wall street", "bull", "bear"
            },
            "climate": {
                "climate", "global warming", "carbon", "emissions", "renewable", "solar",
                "wind", "temperature", "weather", "hurricane", "tornado", "flood",
                "drought", "wildfire", "glacier", "ice", "sea level", "greenhouse"
            },
            "technology": {
                "ai", "artificial intelligence", "machine learning", "openai", "chatgpt",
                "google", "apple", "microsoft", "amazon", "facebook", "meta", "tesla",
                "tech", "technology", "startup", "silicon valley", "software", "hardware"
            },
            "sports": {
                "nfl", "nba", "mlb", "nhl", "soccer", "football", "basketball", "baseball",
                "hockey", "olympics", "world cup", "super bowl", "championship", "playoffs",
                "tournament", "game", "match", "team", "player", "coach", "sport"
            },
            "health": {
                "covid", "coronavirus", "pandemic", "vaccine", "health", "medical",
                "doctor", "hospital", "disease", "virus", "medicine", "drug", "fda",
                "cdc", "who", "outbreak", "epidemic", "treatment", "therapy"
            },
            "geopolitics": {
                "war", "military", "defense", "nato", "ukraine", "russia", "china",
                "conflict", "peace", "treaty", "sanctions", "diplomacy", "embassy",
                "international", "foreign", "security", "terrorism", "nuclear"
            }
        }
        
    def correlate_news_with_markets(
        self,
        news_articles: List[NewsArticle],
        markets: List[Market]
    ) -> Dict[str, List[NewsArticle]]:
        """
        Correlate news articles with markets.
        
        Args:
            news_articles: Available news articles
            markets: Available markets
            
        Returns:
            Dict[str, List[NewsArticle]]: Market ID to related news mapping
        """
        correlations = defaultdict(list)
        
        for market in markets:
            related_articles = self.find_related_articles(market, news_articles)
            if related_articles:
                correlations[market.condition_id] = related_articles
                
        return dict(correlations)
        
    def find_related_articles(
        self,
        market: Market,
        news_articles: List[NewsArticle],
        max_articles: int = 10
    ) -> List[NewsArticle]:
        """
        Find news articles related to a specific market.
        
        Args:
            market: Market to find news for
            news_articles: Available news articles
            max_articles: Maximum number of articles to return
            
        Returns:
            List[NewsArticle]: Related news articles, sorted by relevance
        """
        market_keywords = self._extract_market_keywords(market)
        market_category = self._categorize_market(market)
        
        scored_articles = []
        
        for article in news_articles:
            relevance_score = self._calculate_relevance_score(
                article, market_keywords, market_category
            )
            
            if relevance_score > 0.1:  # Minimum relevance threshold
                scored_articles.append((article, relevance_score))
                
        # Sort by relevance score (descending)
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        
        return [article for article, _ in scored_articles[:max_articles]]
        
    def _extract_market_keywords(self, market: Market) -> List[str]:
        """
        Extract keywords from market question and description.
        
        Args:
            market: Market to extract keywords from
            
        Returns:
            List[str]: Extracted keywords
        """
        text = market.question
        if market.description:
            text += " " + market.description
            
        # Clean and normalize text
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        
        # Split into words
        words = text.split()
        
        # Remove common stop words
        stop_words = {
            "will", "be", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "is", "are", "was", "were", "been", "have", "has",
            "had", "do", "does", "did", "can", "could", "should", "would", "may", "might",
            "must", "shall", "this", "that", "these", "those", "i", "you", "he", "she",
            "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his",
            "her", "its", "our", "their", "if", "then", "else", "when", "where", "why",
            "how", "what", "who", "which", "than", "more", "most", "less", "least",
            "before", "after", "during", "while", "until", "since", "from", "into",
            "through", "over", "under", "above", "below", "up", "down", "out", "off",
            "on", "in", "as", "like", "unlike", "such", "so", "too", "very", "quite",
            "rather", "just", "only", "even", "still", "yet", "already", "soon", "now",
            "then", "here", "there", "where", "everywhere", "anywhere", "somewhere",
            "nowhere", "all", "any", "some", "no", "none", "both", "either", "neither",
            "each", "every", "other", "another", "same", "different", "new", "old",
            "first", "last", "next", "previous", "former", "latter", "above", "below"
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for keyword in keywords:
            if keyword not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword)
                
        return unique_keywords[:20]  # Return top 20 keywords
        
    def _categorize_market(self, market: Market) -> str:
        """
        Categorize market based on its content.
        
        Args:
            market: Market to categorize
            
        Returns:
            str: Market category
        """
        if market.category:
            category = market.category.lower()
            
            # Map known categories
            category_mapping = {
                "politics": "politics",
                "crypto": "crypto",
                "sports": "sports",
                "economics": "economy",
                "climate": "climate",
                "technology": "technology",
                "health": "health"
            }
            
            for key, value in category_mapping.items():
                if key in category:
                    return value
                    
        # Fallback: categorize based on question content
        question = market.question.lower()
        
        for category, keywords in self.keyword_categories.items():
            for keyword in keywords:
                if keyword in question:
                    return category
                    
        return "general"
        
    def _calculate_relevance_score(
        self,
        article: NewsArticle,
        market_keywords: List[str],
        market_category: str
    ) -> float:
        """
        Calculate relevance score between article and market.
        
        Args:
            article: News article
            market_keywords: Market keywords
            market_category: Market category
            
        Returns:
            float: Relevance score (0-1)
        """
        score = 0.0
        
        # Article text for matching
        article_text = f"{article.title} {article.description or ''}".lower()
        
        # 1. Direct keyword matching (40% weight)
        keyword_matches = 0
        for keyword in market_keywords:
            if keyword in article_text:
                keyword_matches += 1
                
        if market_keywords:
            keyword_score = keyword_matches / len(market_keywords)
            score += keyword_score * 0.4
            
        # 2. Category keyword matching (30% weight)
        category_keywords = self.keyword_categories.get(market_category, set())
        category_matches = 0
        
        for keyword in category_keywords:
            if keyword in article_text:
                category_matches += 1
                
        if category_keywords:
            category_score = min(1.0, category_matches / 5)  # Normalize by 5 keywords
            score += category_score * 0.3
            
        # 3. Article freshness (20% weight)
        hours_old = (datetime.now() - article.published_at.replace(tzinfo=None)).total_seconds() / 3600
        freshness_score = max(0, 1 - hours_old / 168)  # Decay over 1 week
        score += freshness_score * 0.2
        
        # 4. Source quality (10% weight)
        high_quality_sources = {
            "reuters", "associated press", "bbc", "bloomberg", "wall street journal",
            "new york times", "washington post", "financial times", "cnbc", "cnn"
        }
        
        source_name = article.source.name.lower()
        source_score = 1.0 if any(source in source_name for source in high_quality_sources) else 0.5
        score += source_score * 0.1
        
        return min(1.0, score)  # Cap at 1.0
        
    def find_emerging_opportunities(
        self,
        news_articles: List[NewsArticle],
        time_window_hours: int = 6
    ) -> List[Tuple[str, List[NewsArticle]]]:
        """
        Find emerging opportunities based on news clustering.
        
        Args:
            news_articles: Recent news articles
            time_window_hours: Time window for "breaking" news
            
        Returns:
            List[Tuple[str, List[NewsArticle]]]: Topic clusters with articles
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_articles = [
            article for article in news_articles 
            if article.published_at.replace(tzinfo=None) > cutoff_time
        ]
        
        if not recent_articles:
            return []
            
        # Cluster articles by topic
        topic_clusters = defaultdict(list)
        
        for article in recent_articles:
            # Categorize article
            article_category = self._categorize_article(article)
            topic_clusters[article_category].append(article)
            
        # Filter clusters with multiple articles (indicating trending topics)
        emerging_topics = []
        for topic, articles in topic_clusters.items():
            if len(articles) >= 2:  # At least 2 articles on the topic
                # Sort by publication time (newest first)
                articles.sort(key=lambda x: x.published_at, reverse=True)
                emerging_topics.append((topic, articles))
                
        # Sort by cluster size (most articles first)
        emerging_topics.sort(key=lambda x: len(x[1]), reverse=True)
        
        return emerging_topics
        
    def _categorize_article(self, article: NewsArticle) -> str:
        """
        Categorize a news article.
        
        Args:
            article: Article to categorize
            
        Returns:
            str: Article category
        """
        article_text = f"{article.title} {article.description or ''}".lower()
        
        # Score each category
        category_scores = {}
        
        for category, keywords in self.keyword_categories.items():
            score = 0
            for keyword in keywords:
                if keyword in article_text:
                    score += 1
                    
            if score > 0:
                category_scores[category] = score
                
        if category_scores:
            # Return category with highest score
            return max(category_scores.items(), key=lambda x: x[1])[0]
        else:
            return "general"