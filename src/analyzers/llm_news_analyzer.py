"""
LLM-powered news analysis for sophisticated sentiment and relevance scoring.
Replaces primitive keyword-based analysis with intelligent understanding.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.clients.polymarket.models import Market
from src.clients.news.models import NewsArticle
from src.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class NewsAnalysisResult:
    """Result of LLM news analysis."""
    sentiment_score: float  # -1.0 to 1.0
    relevance_score: float  # 0.0 to 1.0
    confidence_level: float  # 0.0 to 1.0
    key_insights: List[str]
    bias_detected: bool
    source_credibility: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class MarketNewsAnalysis:
    """Complete news analysis for a market."""
    overall_sentiment: float  # -1.0 to 1.0
    sentiment_confidence: float  # 0.0 to 1.0
    news_impact_score: float  # 0.0 to 1.0
    credible_sources_count: int
    total_articles_analyzed: int
    key_findings: List[str]
    probability_adjustment: float  # -0.20 to +0.20
    reasoning: str


class LLMNewsAnalyzer:
    """
    Advanced news analysis using Claude for sophisticated sentiment analysis,
    bias detection, and market impact assessment.
    """
    
    def __init__(self):
        """Initialize the LLM news analyzer."""
        self.claude_available = bool(settings.claude_api_key)
        if not self.claude_available:
            logger.warning("Claude API key not configured - falling back to enhanced keyword analysis")
    
    async def analyze_market_news(
        self,
        market: Market,
        news_articles: List[NewsArticle]
    ) -> MarketNewsAnalysis:
        """
        Analyze news articles for market impact using LLM.
        
        Args:
            market: Market to analyze
            news_articles: Related news articles
            
        Returns:
            MarketNewsAnalysis: Comprehensive analysis
        """
        if not news_articles:
            return MarketNewsAnalysis(
                overall_sentiment=0.0,
                sentiment_confidence=0.0,
                news_impact_score=0.0,
                credible_sources_count=0,
                total_articles_analyzed=0,
                key_findings=["No news coverage found"],
                probability_adjustment=0.0,
                reasoning="No news articles available for analysis"
            )
        
        # Filter relevant articles
        relevant_articles = self._filter_relevant_articles(market, news_articles)
        
        if not relevant_articles:
            return MarketNewsAnalysis(
                overall_sentiment=0.0,
                sentiment_confidence=0.1,
                news_impact_score=0.0,
                credible_sources_count=0,
                total_articles_analyzed=len(news_articles),
                key_findings=["No relevant news coverage found"],
                probability_adjustment=0.0,
                reasoning=f"Analyzed {len(news_articles)} articles but none were relevant to market question"
            )
        
        # Analyze each article
        article_analyses = []
        for article in relevant_articles[:10]:  # Limit to top 10 for performance
            try:
                analysis = await self._analyze_single_article(market, article)
                article_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing article {article.title}: {e}")
                continue
        
        # Aggregate results
        return self._aggregate_analyses(relevant_articles, article_analyses)
    
    def _filter_relevant_articles(
        self,
        market: Market,
        news_articles: List[NewsArticle]
    ) -> List[NewsArticle]:
        """Filter articles relevant to the market question."""
        market_keywords = self._extract_market_keywords(market)
        relevant_articles = []
        
        for article in news_articles:
            relevance_score = self._calculate_relevance_score(article, market_keywords)
            if relevance_score > 0.3:  # Minimum relevance threshold
                relevant_articles.append(article)
        
        # Sort by relevance and recency
        relevant_articles.sort(
            key=lambda x: (
                self._calculate_relevance_score(x, market_keywords),
                x.published_at.timestamp() if x.published_at else 0
            ),
            reverse=True
        )
        
        return relevant_articles
    
    def _extract_market_keywords(self, market: Market) -> List[str]:
        """Extract key terms from market question."""
        question = market.question.lower()
        
        # Remove common words and extract meaningful terms
        stop_words = {
            "will", "be", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "been", "have", "has", "had",
            "do", "does", "did", "can", "could", "should", "would", "may", "might", "must",
            "than", "more", "most", "before", "after", "above", "below", "up", "down"
        }
        
        # Extract key terms
        words = question.replace("?", "").split()
        keywords = []
        
        for word in words:
            clean_word = word.strip(".,!?;:()[]{}\"'")
            if len(clean_word) > 2 and clean_word not in stop_words:
                keywords.append(clean_word)
        
        # Add market-specific compound terms
        if "most seats" in question:
            keywords.append("election")
        if "etf" in question and "approved" in question:
            keywords.extend(["etf", "sec", "approval"])
        if "tariff" in question:
            keywords.extend(["trade", "tariff", "import"])
        
        return keywords[:15]  # Limit to most important terms
    
    def _calculate_relevance_score(self, article: NewsArticle, keywords: List[str]) -> float:
        """Calculate how relevant an article is to the market."""
        article_text = f"{article.title} {article.description or ''}".lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in article_text)
        max_possible = len(keywords)
        
        if max_possible == 0:
            return 0.0
            
        # Base relevance score
        relevance = matches / max_possible
        
        # Boost for title matches
        title_matches = sum(1 for keyword in keywords if keyword in article.title.lower())
        title_boost = title_matches * 0.2
        
        # Boost for recent articles
        if article.published_at:
            days_old = (datetime.now() - article.published_at).days
            recency_boost = max(0, (7 - days_old) / 7) * 0.1
        else:
            recency_boost = 0
        
        return min(1.0, relevance + title_boost + recency_boost)
    
    async def _analyze_single_article(
        self,
        market: Market,
        article: NewsArticle
    ) -> NewsAnalysisResult:
        """Analyze a single news article."""
        if self.claude_available:
            return await self._llm_analyze_article(market, article)
        else:
            return self._enhanced_keyword_analysis(market, article)
    
    async def _llm_analyze_article(
        self,
        market: Market,
        article: NewsArticle
    ) -> NewsAnalysisResult:
        """Use Claude to analyze article sentiment and relevance."""
        try:
            # For now, import anthropic here to avoid dependency issues
            # In production, this would be properly configured
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.claude_api_key)
            except ImportError:
                logger.warning("Anthropic library not available, falling back to keyword analysis")
                return self._enhanced_keyword_analysis(market, article)
            
            # Construct analysis prompt
            prompt = f"""
Analyze this news article for its impact on the prediction market question:

Market Question: {market.question}
Market Category: {market.category or 'Unknown'}

Article Title: {article.title}
Article Content: {article.description or 'No description available'}
Source: {article.source.name if article.source else 'Unknown'}
Published: {article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Unknown'}

Please provide a structured analysis:

1. SENTIMENT SCORE (-1.0 to 1.0): How positive/negative is this for the market question?
2. RELEVANCE SCORE (0.0 to 1.0): How relevant is this article to the market question?
3. CONFIDENCE LEVEL (0.0 to 1.0): How confident are you in this analysis?
4. KEY INSIGHTS: List 2-3 key insights from the article
5. BIAS DETECTED: Does the article show clear bias? (yes/no)
6. SOURCE CREDIBILITY (0.0 to 1.0): How credible is the news source?
7. REASONING: Brief explanation of your analysis

Format your response as JSON with these exact keys:
sentiment_score, relevance_score, confidence_level, key_insights, bias_detected, source_credibility, reasoning
"""
            
            # Get LLM analysis
            response = client.messages.create(
                model="claude-3-haiku-20240307",  # Fast model for news analysis
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent analysis
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            import json
            try:
                analysis_data = json.loads(response.content[0].text)
                
                return NewsAnalysisResult(
                    sentiment_score=float(analysis_data.get("sentiment_score", 0.0)),
                    relevance_score=float(analysis_data.get("relevance_score", 0.5)),
                    confidence_level=float(analysis_data.get("confidence_level", 0.5)),
                    key_insights=analysis_data.get("key_insights", []),
                    bias_detected=analysis_data.get("bias_detected", False),
                    source_credibility=float(analysis_data.get("source_credibility", 0.5)),
                    reasoning=analysis_data.get("reasoning", "LLM analysis")
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Error parsing LLM response: {e}")
                return self._enhanced_keyword_analysis(market, article)
                
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._enhanced_keyword_analysis(market, article)
    
    def _enhanced_keyword_analysis(
        self,
        market: Market,
        article: NewsArticle
    ) -> NewsAnalysisResult:
        """Enhanced keyword-based analysis as fallback."""
        article_text = f"{article.title} {article.description or ''}".lower()
        
        # Market-specific keyword sets
        positive_keywords = self._get_positive_keywords(market)
        negative_keywords = self._get_negative_keywords(market)
        
        # Count occurrences
        positive_count = sum(1 for keyword in positive_keywords if keyword in article_text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in article_text)
        
        # Calculate sentiment
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
        else:
            sentiment_score = 0.0
        
        # Calculate relevance
        market_keywords = self._extract_market_keywords(market)
        relevance_score = self._calculate_relevance_score(article, market_keywords)
        
        # Source credibility
        source_credibility = self._assess_source_credibility(article.source.name if article.source else "Unknown")
        
        # Bias detection (simple heuristic)
        bias_indicators = ["reportedly", "allegedly", "sources claim", "insider says", "rumored"]
        bias_detected = any(indicator in article_text for indicator in bias_indicators)
        
        return NewsAnalysisResult(
            sentiment_score=sentiment_score,
            relevance_score=relevance_score,
            confidence_level=0.6 if total_sentiment_words > 2 else 0.3,
            key_insights=[f"Keyword analysis: {positive_count} positive, {negative_count} negative terms"],
            bias_detected=bias_detected,
            source_credibility=source_credibility,
            reasoning=f"Enhanced keyword analysis with {total_sentiment_words} sentiment indicators"
        )
    
    def _get_positive_keywords(self, market: Market) -> List[str]:
        """Get positive keywords specific to market type."""
        question = market.question.lower()
        
        # Base positive keywords
        positive = [
            "approved", "success", "win", "victory", "positive", "good", "strong", 
            "growth", "increase", "improve", "better", "up", "gain", "likely",
            "confirmed", "secured", "achieved", "accomplished", "breakthrough"
        ]
        
        # Market-specific keywords
        if "etf" in question:
            positive.extend(["regulatory approval", "sec approval", "cleared", "authorized"])
        elif "election" in question or "seats" in question:
            positive.extend(["leading", "ahead", "polling well", "momentum", "support"])
        elif "tariff" in question:
            positive.extend(["implementing", "announced", "proceeding", "committed"])
        elif "crypto" in question:
            positive.extend(["adoption", "institutional", "mainstream", "regulatory clarity"])
        
        return positive
    
    def _get_negative_keywords(self, market: Market) -> List[str]:
        """Get negative keywords specific to market type."""
        question = market.question.lower()
        
        # Base negative keywords
        negative = [
            "rejected", "denied", "fail", "lose", "defeat", "negative", "bad", "weak",
            "decline", "decrease", "worse", "down", "loss", "drop", "unlikely",
            "blocked", "cancelled", "postponed", "delayed", "suspended"
        ]
        
        # Market-specific keywords
        if "etf" in question:
            negative.extend(["regulatory concerns", "sec rejection", "compliance issues"])
        elif "election" in question or "seats" in question:
            negative.extend(["trailing", "behind", "losing support", "scandal"])
        elif "tariff" in question:
            negative.extend(["backing down", "reconsidering", "opposition"])
        elif "crypto" in question:
            negative.extend(["crackdown", "ban", "regulatory uncertainty", "volatility"])
        
        return negative
    
    def _assess_source_credibility(self, source_name: str) -> float:
        """Assess credibility of news source."""
        source_lower = source_name.lower()
        
        # Tier 1: Highly credible sources
        tier1_sources = [
            "reuters", "associated press", "bbc", "bloomberg", "wall street journal",
            "financial times", "new york times", "washington post", "npr", "pbs"
        ]
        
        # Tier 2: Credible sources
        tier2_sources = [
            "cnn", "abc news", "nbc news", "cbs news", "fox news", "the guardian",
            "usa today", "politico", "axios", "the hill", "cnbc", "marketwatch"
        ]
        
        # Tier 3: Moderate credibility
        tier3_sources = [
            "yahoo", "msn", "huffpost", "buzzfeed news", "vox", "slate",
            "salon", "the daily beast", "mother jones", "reason"
        ]
        
        if any(source in source_lower for source in tier1_sources):
            return 0.9
        elif any(source in source_lower for source in tier2_sources):
            return 0.7
        elif any(source in source_lower for source in tier3_sources):
            return 0.5
        else:
            return 0.3  # Unknown or low-credibility source
    
    def _aggregate_analyses(
        self,
        articles: List[NewsArticle],
        analyses: List[NewsAnalysisResult]
    ) -> MarketNewsAnalysis:
        """Aggregate individual article analyses."""
        if not analyses:
            return MarketNewsAnalysis(
                overall_sentiment=0.0,
                sentiment_confidence=0.0,
                news_impact_score=0.0,
                credible_sources_count=0,
                total_articles_analyzed=len(articles),
                key_findings=["No successful analyses completed"],
                probability_adjustment=0.0,
                reasoning="All article analyses failed"
            )
        
        # Weight analyses by relevance and source credibility
        weighted_sentiment = 0.0
        total_weight = 0.0
        
        for analysis in analyses:
            weight = analysis.relevance_score * analysis.source_credibility * analysis.confidence_level
            weighted_sentiment += analysis.sentiment_score * weight
            total_weight += weight
        
        overall_sentiment = weighted_sentiment / total_weight if total_weight > 0 else 0.0
        
        # Calculate confidence based on number of high-quality analyses
        high_quality_analyses = [a for a in analyses if a.confidence_level > 0.6 and a.relevance_score > 0.5]
        sentiment_confidence = min(1.0, len(high_quality_analyses) / 5)  # Max confidence with 5+ quality analyses
        
        # Calculate news impact score
        credible_sources_count = sum(1 for a in analyses if a.source_credibility > 0.6)
        news_impact_score = min(1.0, credible_sources_count / 3)  # Max impact with 3+ credible sources
        
        # Calculate probability adjustment
        # Strong sentiment with high confidence gets larger adjustment
        max_adjustment = 0.20  # ±20% maximum
        adjustment_magnitude = abs(overall_sentiment) * sentiment_confidence * news_impact_score
        probability_adjustment = overall_sentiment * adjustment_magnitude * max_adjustment
        
        # Key findings
        key_findings = []
        if credible_sources_count > 0:
            key_findings.append(f"{credible_sources_count} credible sources analyzed")
        if abs(overall_sentiment) > 0.3:
            sentiment_desc = "positive" if overall_sentiment > 0 else "negative"
            key_findings.append(f"Strong {sentiment_desc} sentiment detected")
        if any(a.bias_detected for a in analyses):
            key_findings.append("Potential bias detected in some sources")
        
        # Collect unique insights
        all_insights = []
        for analysis in analyses:
            all_insights.extend(analysis.key_insights)
        unique_insights = list(set(all_insights))[:5]  # Top 5 unique insights
        key_findings.extend(unique_insights)
        
        reasoning = f"Analyzed {len(analyses)} articles with {sentiment_confidence:.1%} confidence. "
        reasoning += f"Weighted sentiment: {overall_sentiment:+.2f}, "
        reasoning += f"Impact score: {news_impact_score:.2f}, "
        reasoning += f"Probability adjustment: {probability_adjustment:+.1%}"
        
        return MarketNewsAnalysis(
            overall_sentiment=overall_sentiment,
            sentiment_confidence=sentiment_confidence,
            news_impact_score=news_impact_score,
            credible_sources_count=credible_sources_count,
            total_articles_analyzed=len(articles),
            key_findings=key_findings,
            probability_adjustment=probability_adjustment,
            reasoning=reasoning
        )