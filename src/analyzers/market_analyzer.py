"""
Market analyzer for identifying high-value opportunities.
"""

import logging
import math
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from src.analyzers.models import AnalysisResult, MarketOpportunity, OpportunityScore
from src.analyzers.flexible_analyzer import FlexibleAnalyzer
from src.analyzers.simple_pattern_analyzer import SimpleOpportunity
from src.analyzers.kelly_criterion import KellyCriterion
from src.analyzers.backtesting import BacktestingEngine
from src.clients.news.models import NewsArticle
from src.clients.polymarket.models import Market, MarketPrice
from src.config.settings import settings

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Analyzer for identifying market opportunities.
    """
    
    def __init__(self):
        """Initialize market analyzer."""
        self.min_volume = settings.min_market_volume
        self.min_spread = settings.min_probability_spread
        self.pattern_analyzer = FlexibleAnalyzer()
        self.kelly_criterion = KellyCriterion()
        self.backtesting_engine = BacktestingEngine()
        
    async def analyze_markets(
        self,
        markets: List[Market],
        market_prices: List[MarketPrice],
        news_articles: List[NewsArticle]
    ) -> AnalysisResult:
        """
        Analyze markets for opportunities.
        
        Args:
            markets: List of markets to analyze
            market_prices: List of market prices
            news_articles: Related news articles
            
        Returns:
            AnalysisResult: Analysis results
        """
        start_time = time.time()
        opportunities = []
        
        # Create price lookup
        price_lookup = {price.condition_id: price for price in market_prices}
        
        for market in markets:
            try:
                opportunity = await self._analyze_single_market(
                    market, 
                    price_lookup.get(market.condition_id),
                    news_articles
                )
                if opportunity:
                    opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"Error analyzing market {market.condition_id}: {e}")
                continue
                
        analysis_duration = time.time() - start_time
        
        return AnalysisResult(
            opportunities=opportunities,
            total_markets_analyzed=len(markets),
            analysis_duration_seconds=analysis_duration,
            news_articles_processed=len(news_articles)
        )
        
    async def _analyze_single_market(
        self,
        market: Market,
        price: Optional[MarketPrice],
        news_articles: List[NewsArticle]
    ) -> Optional[MarketOpportunity]:
        """
        Analyze a single market for opportunities.
        
        Args:
            market: Market to analyze
            price: Current market price
            news_articles: Related news articles
            
        Returns:
            Optional[MarketOpportunity]: Opportunity if found
        """
        if not price:
            return None
            
        # Filter markets by volume threshold
        if market.volume and market.volume < self.min_volume:
            return None
            
        # Use simple pattern analyzer
        try:
            simple_opportunity = self.pattern_analyzer.analyze_market(
                market, price
            )
            
            if not simple_opportunity:
                return None
                
            # Only proceed if edge meets minimum threshold
            if simple_opportunity.edge < self.min_spread:
                return None
                
            # Calculate fair values based on the opportunity
            fair_yes_price, fair_no_price = self.pattern_analyzer.calculate_fair_value(
                simple_opportunity
            )
            
            # Create reasoning from the simple pattern
            fair_value_reasoning = (
                f"Pattern: {simple_opportunity.pattern_type} | "
                f"{simple_opportunity.reason} | "
                f"Confidence: {simple_opportunity.confidence:.0%}"
            )
            
        except Exception as e:
            logger.error(f"Pattern analysis failed for {market.condition_id}: {e}")
            return None
            
        # Determine position from simple opportunity
        if simple_opportunity.recommended_action in ["BUY_YES", "SELL_NO"]:
            recommended_position = "YES"
            cost = price.yes_price
            expected_value = fair_yes_price * 1.0
            expected_return = ((expected_value - cost) / cost * 100) if cost > 0 else 0
            edge = simple_opportunity.edge
        else:
            recommended_position = "NO"
            cost = price.no_price
            expected_value = fair_no_price * 1.0
            expected_return = ((expected_value - cost) / cost * 100) if cost > 0 else 0
            edge = simple_opportunity.edge
            
        # Calculate scores based on simple opportunity
        score = self._calculate_simple_opportunity_score(
            market, price, simple_opportunity, news_articles
        )
        
        # Find related news
        related_news = self._find_related_news(market, news_articles)
        
        # Generate reasoning (now includes sophisticated fair value analysis)
        reasoning = self._generate_reasoning(
            market, price, fair_yes_price, fair_no_price, related_news, fair_value_reasoning
        )
        
        # Create the opportunity first
        opportunity = MarketOpportunity(
            condition_id=market.condition_id,
            question=market.question,
            description=market.description,
            category=market.category,
            market_slug=market.market_slug,
            current_yes_price=price.yes_price,
            current_no_price=price.no_price,
            current_spread=price.spread,
            volume=market.volume,
            liquidity=market.liquidity,
            fair_yes_price=fair_yes_price,
            fair_no_price=fair_no_price,
            expected_return=expected_return,
            recommended_position=recommended_position,
            score=score,
            end_date=market.end_date_iso,
            reasoning=reasoning,
            related_news=[article.title for article in related_news[:3]]
        )
        
        # Add Kelly Criterion analysis
        try:
            predicted_prob = fair_yes_price if recommended_position == "YES" else fair_no_price
            kelly_analysis = self.kelly_criterion.calculate(
                market=market,
                predicted_probability=predicted_prob,
                confidence=score.confidence_score,
                recommended_position=recommended_position
            )
            opportunity.kelly_analysis = kelly_analysis
            
            # Record prediction for backtesting
            self.backtesting_engine.record_prediction(
                market=market,
                opportunity=opportunity,
                model_version="v2024.1"  # Update this as model evolves
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate Kelly Criterion for {market.condition_id}: {e}")
            
        return opportunity
        
        
    def _analyze_news_sentiment(self, news_articles: List[NewsArticle]) -> float:
        """
        Analyze sentiment of news articles.
        
        Args:
            news_articles: News articles to analyze
            
        Returns:
            float: Sentiment score (-1 to 1)
        """
        if not news_articles:
            return 0.0
            
        # Simple keyword-based sentiment analysis
        positive_keywords = [
            "success", "win", "victory", "positive", "good", "strong", 
            "growth", "increase", "improve", "better", "up", "gain"
        ]
        negative_keywords = [
            "fail", "lose", "defeat", "negative", "bad", "weak",
            "decline", "decrease", "worse", "down", "loss", "drop"
        ]
        
        total_sentiment = 0.0
        article_count = 0
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in text)
            negative_count = sum(1 for keyword in negative_keywords if keyword in text)
            
            if positive_count > 0 or negative_count > 0:
                article_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                total_sentiment += article_sentiment
                article_count += 1
                
        return total_sentiment / article_count if article_count > 0 else 0.0
        
    def _calculate_time_factor(self, market: Market) -> float:
        """
        Calculate time factor based on market end date.
        
        Args:
            market: Market to analyze
            
        Returns:
            float: Time factor (0-1, higher is better)
        """
        if not market.end_date_iso:
            return 0.5  # Unknown end date
            
        # Handle timezone-aware datetime comparison
        now = datetime.now(timezone.utc)
        if market.end_date_iso.tzinfo is not None:
            # Both are already timezone-aware
            market_end = market.end_date_iso
        else:
            # Market date is naive, make it aware
            market_end = market.end_date_iso.replace(tzinfo=timezone.utc)
            
        days_until_end = (market_end - now).days
        return self._calculate_time_score_from_days(days_until_end)
        
    def _calculate_time_score_from_days(self, days_until_end: int) -> float:
        """
        Calculate time score from days until end.
        
        Args:
            days_until_end: Days until market resolution
            
        Returns:
            float: Time score (0-1)
        """
        if days_until_end <= 0:
            return 0.0  # Market already ended
        elif days_until_end <= 7:
            return 1.0  # Very close to resolution
        elif days_until_end <= 30:
            return 0.8  # Reasonably close
        elif days_until_end <= 90:
            return 0.6  # Moderate time horizon
        else:
            return 0.3  # Long-term market
            
    def _get_base_probability(self, market: Market) -> float:
        """
        Get base probability estimate based on market type and question.
        
        Args:
            market: Market to analyze
            
        Returns:
            float: Base probability estimate
        """
        question_lower = market.question.lower()
        
        # For "most seats" or "win the most" type questions in multi-party systems
        if any(phrase in question_lower for phrase in ["most seats", "win the most", "hold the most"]):
            # Count likely competitors by looking for party names
            party_indicators = ["ldp", "cdp", "jip", "komeito", "jcp", "sdp", "dpj", "party"]
            if any(indicator in question_lower for indicator in party_indicators):
                # Multi-party election - most parties have low probability
                if any(major in question_lower for major in ["ldp", "liberal democratic", "conservative"]):
                    return 0.35  # Major party has higher chance
                elif any(major in question_lower for major in ["cdp", "constitutional democratic"]):
                    return 0.25  # Main opposition
                else:
                    return 0.05  # Minor parties have very low chance
                    
        # Binary yes/no questions
        if question_lower.startswith("will "):
            # ETF approval questions
            if "etf" in question_lower and "approved" in question_lower:
                if "bitcoin" in question_lower:
                    return 0.4  # Already established precedent
                elif any(crypto in question_lower for crypto in ["ethereum", "litecoin"]):
                    return 0.3  # Major cryptos
                else:
                    return 0.15  # Other cryptos less likely
                    
            # Political questions
            if any(term in question_lower for term in ["trump", "president", "election"]):
                return 0.45  # Political events tend to be competitive
                
            # Sports questions
            if any(term in question_lower for term in ["win", "championship", "fire", "retire"]):
                return 0.35  # Sports outcomes
                
            # Pandemic/crisis questions
            if any(term in question_lower for term in ["pandemic", "crisis", "war"]):
                return 0.2   # Major crises are relatively rare
                
            # Merger/business questions
            if any(term in question_lower for term in ["merger", "acquisition", "cut", "traded"]):
                return 0.3   # Business decisions
                
        # Default for unclear questions
        return 0.5
        
    def _get_category_adjustment(self, market: Market) -> float:
        """
        Get adjustment based on market category knowledge.
        
        Args:
            market: Market to analyze
            
        Returns:
            float: Category adjustment (-0.1 to 0.1)
        """
        if not market.category:
            return 0.0
            
        category = market.category.lower()
        
        # Category-specific adjustments based on general knowledge
        if "crypto" in category or "bitcoin" in category:
            return 0.05  # Slightly bullish on crypto adoption
        elif "election" in category or "politics" in category:
            return 0.0   # Neutral on political outcomes
        elif "climate" in category or "weather" in category:
            return 0.02  # Slightly pessimistic on climate targets
        elif "sports" in category:
            return 0.0   # Neutral on sports outcomes
        else:
            return 0.0
            
    def _calculate_simple_opportunity_score(
        self,
        market: Market,
        price: MarketPrice,
        opportunity: SimpleOpportunity,
        news_articles: List[NewsArticle]
    ) -> OpportunityScore:
        """
        Calculate scoring based on simple opportunity.
        """
        # Value score based on edge
        value_score = min(1.0, opportunity.edge / 0.3)  # Normalize to 0-1
        
        # Confidence from the pattern analyzer
        confidence_score = opportunity.confidence
        
        # Volume score
        volume_score = 0.5
        if market.volume:
            volume_score = min(1.0, market.volume / 50000)
            
        # Time score
        time_score = self._calculate_time_factor(market)
        
        # News relevance (reduced importance for simple patterns)
        news_relevance_score = 0.3  # Default
        if news_articles and opportunity.pattern_type == "NEWS_OVERREACTION":
            news_relevance_score = 0.8
            
        return OpportunityScore(
            value_score=value_score,
            confidence_score=confidence_score,
            volume_score=volume_score,
            time_score=time_score,
            news_relevance_score=news_relevance_score
        )
    
    def _calculate_opportunity_score(
        self,
        market: Market,
        price: MarketPrice,
        fair_yes_price: float,
        fair_no_price: float,
        news_articles: List[NewsArticle]
    ) -> OpportunityScore:
        """
        Calculate opportunity scoring.
        
        Args:
            market: Market data
            price: Current prices
            fair_yes_price: Fair YES price
            fair_no_price: Fair NO price
            news_articles: Related news
            
        Returns:
            OpportunityScore: Calculated scores
        """
        # Value score: How much potential profit
        value_diff = max(
            abs(fair_yes_price - price.yes_price),
            abs(fair_no_price - price.no_price)
        )
        value_score = min(1.0, value_diff / 0.3)  # Normalize to 0-1
        
        # Confidence score: How confident we are in the analysis
        confidence_factors = []
        
        # More news articles = higher confidence
        if news_articles:
            news_confidence = min(1.0, len(news_articles) / 10)
            confidence_factors.append(news_confidence)
            
        # Time factor
        time_factor = self._calculate_time_factor(market)
        confidence_factors.append(time_factor)
        
        # Market maturity (higher volume = higher confidence)
        if market.volume:
            volume_confidence = min(1.0, market.volume / 10000)
            confidence_factors.append(volume_confidence)
            
        confidence_score = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.3
        
        # Volume score: Market liquidity
        volume_score = 0.5
        if market.volume:
            volume_score = min(1.0, market.volume / 50000)
            
        # Time score: Time until resolution
        time_score = self._calculate_time_factor(market)
        
        # News relevance score
        related_news = self._find_related_news(market, news_articles)
        news_relevance_score = min(1.0, len(related_news) / 5)
        
        return OpportunityScore(
            value_score=value_score,
            confidence_score=confidence_score,
            volume_score=volume_score,
            time_score=time_score,
            news_relevance_score=news_relevance_score
        )
        
    def _find_related_news(
        self,
        market: Market,
        news_articles: List[NewsArticle]
    ) -> List[NewsArticle]:
        """
        Find news articles related to the market.
        
        Args:
            market: Market to find news for
            news_articles: Available news articles
            
        Returns:
            List[NewsArticle]: Related news articles
        """
        market_keywords = self._extract_market_keywords(market)
        related = []
        
        for article in news_articles:
            article_text = f"{article.title} {article.description or ''}".lower()
            
            # Check if any market keywords appear in the article
            for keyword in market_keywords:
                if keyword in article_text:
                    related.append(article)
                    break
                    
        return related
        
    def _extract_market_keywords(self, market: Market) -> List[str]:
        """
        Extract keywords from market question.
        
        Args:
            market: Market to extract keywords from
            
        Returns:
            List[str]: List of keywords
        """
        # Simple keyword extraction
        question = market.question.lower()
        
        # Remove common words
        stop_words = {
            "will", "be", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "been", "have", "has", "had",
            "do", "does", "did", "can", "could", "should", "would", "may", "might", "must"
        }
        
        words = question.split()
        keywords = [word.strip(".,!?;:") for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Return top 10 keywords
        
    def _generate_reasoning(
        self,
        market: Market,
        price: MarketPrice,
        fair_yes_price: float,
        fair_no_price: float,
        related_news: List[NewsArticle],
        fair_value_reasoning: str = ""
    ) -> str:
        """
        Generate comprehensive human-readable reasoning for the analysis.
        
        Args:
            market: Market data
            price: Current prices
            fair_yes_price: Fair YES price
            fair_no_price: Fair NO price
            related_news: Related news articles
            
        Returns:
            str: Detailed analysis reasoning
        """
        reasoning_parts = []
        
        # Start with sophisticated fair value analysis
        if fair_value_reasoning:
            reasoning_parts.append(f"Fair Value Analysis: {fair_value_reasoning}")
        
        # Price analysis with confidence metrics
        yes_diff = fair_yes_price - price.yes_price
        no_diff = fair_no_price - price.no_price
        
        if abs(yes_diff) > abs(no_diff):
            if yes_diff > 0:
                reasoning_parts.append(f"YES appears undervalued by {yes_diff:.1%} (Current: {price.yes_price:.1%} vs Fair: {fair_yes_price:.1%})")
            else:
                reasoning_parts.append(f"YES appears overvalued by {abs(yes_diff):.1%} (Current: {price.yes_price:.1%} vs Fair: {fair_yes_price:.1%})")
        else:
            if no_diff > 0:
                reasoning_parts.append(f"NO appears undervalued by {no_diff:.1%} (Current: {price.no_price:.1%} vs Fair: {fair_no_price:.1%})")
            else:
                reasoning_parts.append(f"NO appears overvalued by {abs(no_diff):.1%} (Current: {price.no_price:.1%} vs Fair: {fair_no_price:.1%})")
                
        # Market spread analysis
        if price.spread > 0.1:
            reasoning_parts.append(f"Wide spread ({price.spread:.1%}) indicates pricing uncertainty")
        elif price.spread < 0.05:
            reasoning_parts.append(f"Tight spread ({price.spread:.1%}) suggests efficient pricing")
            
        # News sentiment and quality analysis
        if related_news:
            news_sentiment = self._analyze_news_sentiment(related_news)
            sentiment_desc = "positive" if news_sentiment > 0.1 else "negative" if news_sentiment < -0.1 else "neutral"
            
            # Get news source quality
            high_quality_sources = sum(1 for article in related_news 
                                     if any(source in article.source.name.lower() 
                                           for source in ["reuters", "bbc", "bloomberg", "associated press", "wall street journal"]))
            
            reasoning_parts.append(f"News analysis: {len(related_news)} articles with {sentiment_desc} sentiment")
            if high_quality_sources > 0:
                reasoning_parts.append(f"{high_quality_sources} high-quality news sources provide additional confidence")
                
            # Add most relevant headlines
            if len(related_news) > 0:
                top_headlines = [article.title for article in related_news[:2]]
                reasoning_parts.append(f"Key headlines: {'; '.join(top_headlines)}")
        else:
            reasoning_parts.append("Limited news coverage - analysis relies on market fundamentals")
            
        # Volume and liquidity analysis with specific metrics
        if market.volume:
            volume_score = min(1.0, market.volume / 50000)  # Normalize against $50k
            if market.volume > 50000:
                reasoning_parts.append(f"Excellent liquidity (${market.volume:,.0f} volume, {volume_score:.1%} liquidity score)")
            elif market.volume > 10000:
                reasoning_parts.append(f"Good liquidity (${market.volume:,.0f} volume, {volume_score:.1%} liquidity score)")
            elif market.volume > 1000:
                reasoning_parts.append(f"Moderate liquidity (${market.volume:,.0f} volume, {volume_score:.1%} liquidity score) - consider position sizing")
            else:
                reasoning_parts.append(f"Low liquidity (${market.volume:,.0f} volume, {volume_score:.1%} liquidity score) - high risk")
        else:
            reasoning_parts.append("Volume data unavailable - liquidity risk unknown")
            
        # Time analysis with specific metrics
        if market.end_date_iso:
            # Handle timezone-aware datetime comparison
            now = datetime.now(timezone.utc)
            if market.end_date_iso.tzinfo is None:
                # Make market date timezone-aware
                market.end_date_iso = market.end_date_iso.replace(tzinfo=timezone.utc)
                
            days_until_end = (market.end_date_iso - now).days
            time_score = self._calculate_time_score_from_days(days_until_end)
            
            if days_until_end <= 7:
                reasoning_parts.append(f"Resolves in {days_until_end} days (time score: {time_score:.2f}) - very high confidence")
            elif days_until_end <= 30:
                reasoning_parts.append(f"Resolves in {days_until_end} days (time score: {time_score:.2f}) - high confidence")
            elif days_until_end <= 90:
                reasoning_parts.append(f"Resolves in {days_until_end} days (time score: {time_score:.2f}) - moderate time risk")
            else:
                reasoning_parts.append(f"Resolves in {days_until_end} days (time score: {time_score:.2f}) - significant time risk")
        else:
            reasoning_parts.append("Resolution date unknown - adds uncertainty to analysis")
            
        # Category-specific insights
        if market.category:
            category_adjustment = self._get_category_adjustment(market)
            if abs(category_adjustment) > 0.02:
                direction = "bullish" if category_adjustment > 0 else "bearish"
                reasoning_parts.append(f"Category analysis ({market.category}) suggests {direction} bias ({category_adjustment:+.1%})")
                
        # Statistical confidence indicators
        confidence_factors = []
        if related_news and len(related_news) >= 3:
            confidence_factors.append("adequate news coverage")
        if market.volume and market.volume > 5000:
            confidence_factors.append("sufficient market volume")
        if market.end_date_iso:
            days_left = (market.end_date_iso - datetime.now(timezone.utc)).days if market.end_date_iso else None
            if days_left and days_left <= 30:
                confidence_factors.append("near-term resolution")
                
        if confidence_factors:
            reasoning_parts.append(f"Confidence boosted by: {', '.join(confidence_factors)}")
            
        return ". ".join(reasoning_parts) + "."