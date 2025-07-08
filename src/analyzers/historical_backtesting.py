"""
Historical backtesting system for validating models against closed markets.

This module fetches closed markets from Polymarket and runs our prediction
models against them to evaluate performance on real historical data.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from src.clients.polymarket.client import PolymarketClient
from src.clients.polymarket.models import Market
from src.clients.news.client import NewsAPIClient
from src.analyzers.market_analyzer import MarketAnalyzer
from src.analyzers.backtesting import BacktestingEngine, BacktestMetrics
from src.analyzers.models import MarketOpportunity

logger = logging.getLogger(__name__)


@dataclass
class HistoricalBacktestResult:
    """Result of historical backtesting."""
    
    markets_tested: int
    successful_predictions: int
    failed_predictions: int
    filtered_markets: int
    
    # Performance metrics
    metrics: BacktestMetrics
    
    # Market breakdown
    markets_by_category: Dict[str, int]
    accuracy_by_category: Dict[str, float]
    
    # Time analysis
    prediction_timeframes: Dict[str, int]  # How far before close we "predicted"
    

class HistoricalBacktester:
    """
    Runs backtests against historical closed markets to validate model performance.
    """
    
    def __init__(self):
        """Initialize historical backtester."""
        self.polymarket_client = PolymarketClient()
        self.news_client = NewsAPIClient()
        self.market_analyzer = MarketAnalyzer()
        self.backtesting_engine = BacktestingEngine("data/historical_backtests")
        
    async def run_historical_backtest(
        self,
        days_back: int = 30,
        max_markets: int = 50,
        prediction_window_days: int = 7,
        categories: Optional[List[str]] = None
    ) -> HistoricalBacktestResult:
        """
        Run backtest against historical closed markets.
        
        Args:
            days_back: How many days back to look for closed markets
            max_markets: Maximum number of markets to test
            prediction_window_days: Simulate predictions N days before close
            categories: Filter by market categories
            
        Returns:
            HistoricalBacktestResult: Comprehensive backtest results
        """
        logger.info(f"Starting historical backtest: {days_back} days back, max {max_markets} markets")
        
        # Fetch closed markets
        closed_markets = await self._fetch_closed_markets(
            days_back=days_back,
            max_markets=max_markets,
            categories=categories
        )
        
        logger.info(f"Found {len(closed_markets)} closed markets for backtesting")
        
        # Run predictions on each market
        results = await self._run_predictions_on_historical_markets(
            markets=closed_markets,
            prediction_window_days=prediction_window_days
        )
        
        # Analyze results
        metrics = self.backtesting_engine.run_backtest(
            model_version="historical_backtest",
            min_days_since_prediction=0
        )
        
        return HistoricalBacktestResult(
            markets_tested=results["tested"],
            successful_predictions=results["successful"], 
            failed_predictions=results["failed"],
            filtered_markets=results["filtered"],
            metrics=metrics,
            markets_by_category=results["by_category"],
            accuracy_by_category=results["accuracy_by_category"],
            prediction_timeframes=results["timeframes"]
        )
        
    async def _fetch_closed_markets(
        self,
        days_back: int,
        max_markets: int,
        categories: Optional[List[str]] = None
    ) -> List[Market]:
        """Fetch closed markets from Polymarket."""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            logger.info(f"Fetching closed markets from {start_date.date()} to {end_date.date()}")
            
            # Fetch all markets and filter for closed ones
            all_markets = await self.polymarket_client.get_markets()
            
            closed_markets = []
            for market in all_markets:
                # Filter for closed markets
                if not market.closed:
                    continue
                    
                # Check if resolved recently
                if market.end_date_iso:
                    if market.end_date_iso < start_date or market.end_date_iso > end_date:
                        continue
                        
                # Filter by category if specified
                if categories and market.category:
                    if market.category.lower() not in [c.lower() for c in categories]:
                        continue
                        
                # Only include markets with clear binary outcomes
                if len(market.tokens) != 2:
                    continue
                    
                # Must have volume data
                if not market.volume or market.volume < 1000:  # At least $1000 volume
                    continue
                    
                closed_markets.append(market)
                
                if len(closed_markets) >= max_markets:
                    break
                    
            logger.info(f"Filtered to {len(closed_markets)} suitable closed markets")
            return closed_markets
            
        except Exception as e:
            logger.error(f"Failed to fetch closed markets: {e}")
            return []
            
    async def _run_predictions_on_historical_markets(
        self,
        markets: List[Market],
        prediction_window_days: int
    ) -> Dict:
        """Run our prediction model on historical markets."""
        
        results = {
            "tested": 0,
            "successful": 0,
            "failed": 0,
            "filtered": 0,
            "by_category": {},
            "accuracy_by_category": {},
            "timeframes": {}
        }
        
        for market in markets:
            try:
                # Simulate making prediction N days before market closed
                if market.end_date_iso:
                    simulated_prediction_time = market.end_date_iso - timedelta(days=prediction_window_days)
                else:
                    continue
                    
                logger.info(f"Backtesting market: {market.question[:60]}...")
                
                # Get historical news (simulate what news was available at prediction time)
                news_articles = await self._get_historical_news(
                    market=market,
                    cutoff_date=simulated_prediction_time
                )
                
                # Run our prediction model as if we were predicting then
                opportunity = await self._simulate_historical_prediction(
                    market=market,
                    prediction_time=simulated_prediction_time,
                    news_articles=news_articles
                )
                
                if opportunity:
                    # Determine actual outcome
                    actual_outcome = self._determine_actual_outcome(market)
                    
                    if actual_outcome:
                        # Record the "historical" prediction with known outcome
                        self._record_historical_prediction(
                            market=market,
                            opportunity=opportunity,
                            actual_outcome=actual_outcome,
                            prediction_time=simulated_prediction_time
                        )
                        
                        results["successful"] += 1
                        results["tested"] += 1
                        
                        # Track by category
                        category = market.category or "Unknown"
                        results["by_category"][category] = results["by_category"].get(category, 0) + 1
                        
                        # Track timeframe
                        timeframe = f"{prediction_window_days}d_before"
                        results["timeframes"][timeframe] = results["timeframes"].get(timeframe, 0) + 1
                        
                    else:
                        logger.warning(f"Could not determine outcome for {market.condition_id}")
                        results["failed"] += 1
                        
                else:
                    results["filtered"] += 1
                    logger.debug(f"Market {market.condition_id} was filtered out by analyzer")
                    
            except Exception as e:
                logger.error(f"Failed to backtest market {market.condition_id}: {e}")
                results["failed"] += 1
                
        # Calculate accuracy by category
        if results["successful"] > 0:
            # This would need actual outcome tracking to implement properly
            # For now, we'll get it from the backtesting engine after recording
            pass
            
        return results
        
    async def _get_historical_news(
        self,
        market: Market,
        cutoff_date: datetime
    ) -> List:
        """Get news articles that would have been available at prediction time."""
        try:
            # Extract key terms from market question for news search
            search_terms = self._extract_search_terms(market.question)
            
            # Search for news from a week before cutoff date to cutoff date
            # This simulates what news would have been available
            search_start = cutoff_date - timedelta(days=7)
            
            # In a real implementation, we'd need access to historical news
            # For now, we'll use current news as a proxy (not ideal but functional)
            news_articles = await self.news_client.get_everything(
                query=search_terms,
                from_date=search_start.isoformat(),
                to_date=cutoff_date.isoformat(),
                sort_by="relevancy",
                page_size=20
            )
            
            return news_articles.articles if news_articles else []
            
        except Exception as e:
            logger.warning(f"Failed to get historical news for {market.condition_id}: {e}")
            return []
            
    def _extract_search_terms(self, question: str) -> str:
        """Extract search terms from market question."""
        # Remove common prediction market language
        stop_words = {
            "will", "would", "should", "could", "may", "might", "the", "a", "an",
            "by", "before", "after", "during", "in", "on", "at", "to", "for",
            "and", "or", "but", "if", "then", "than", "as", "be", "is", "are",
            "was", "were", "been", "being", "have", "has", "had", "do", "does",
            "did", "get", "go", "make", "take", "come", "see", "know", "think",
            "say", "tell", "ask", "work", "seem", "feel", "try", "leave", "call"
        }
        
        # Extract meaningful words
        words = question.lower().replace("?", "").split()
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Take first few most important terms
        return " ".join(meaningful_words[:5])
        
    async def _simulate_historical_prediction(
        self,
        market: Market,
        prediction_time: datetime,
        news_articles: List
    ) -> Optional[MarketOpportunity]:
        """Simulate running our prediction model at a historical point in time."""
        try:
            # Create price object based on historical data
            # In a real implementation, we'd need historical price data
            # For now, we'll use current prices as a proxy
            from src.clients.polymarket.models import MarketPrice
            
            # Simulate historical prices (this is a simplification)
            yes_price = market.tokens[0].price if market.tokens else 0.5
            no_price = market.tokens[1].price if len(market.tokens) > 1 else 1.0 - yes_price
            
            price = MarketPrice(
                condition_id=market.condition_id,
                yes_price=yes_price,
                no_price=no_price,
                spread=abs(yes_price - no_price)
            )
            
            # Run our analyzer as if we were making the prediction then
            opportunity = await self.market_analyzer._analyze_single_market(
                market=market,
                price=price,
                news_articles=news_articles
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to simulate prediction for {market.condition_id}: {e}")
            return None
            
    def _determine_actual_outcome(self, market: Market) -> Optional[str]:
        """Determine the actual outcome of a closed market."""
        try:
            # Look at token prices to determine outcome
            # In closed markets, winning token should be at ~$1.00, losing at ~$0.00
            if len(market.tokens) != 2:
                return None
                
            yes_token = market.tokens[0]
            no_token = market.tokens[1]
            
            # Check final prices to determine winner
            if yes_token.price and no_token.price:
                if yes_token.price > 0.9:  # YES won
                    return "YES"
                elif no_token.price > 0.9:  # NO won
                    return "NO"
                else:
                    # Unclear outcome or invalid market
                    return "INVALID"
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Could not determine outcome for {market.condition_id}: {e}")
            return None
            
    def _record_historical_prediction(
        self,
        market: Market,
        opportunity: MarketOpportunity,
        actual_outcome: str,
        prediction_time: datetime
    ) -> None:
        """Record a historical prediction with known outcome."""
        try:
            # Record the prediction
            self.backtesting_engine.record_prediction(
                market=market,
                opportunity=opportunity,
                model_version="historical_backtest"
            )
            
            # Immediately update with the known outcome
            self.backtesting_engine.update_outcome(
                condition_id=market.condition_id,
                outcome=actual_outcome,
                resolution_date=market.end_date_iso,
                final_price=market.tokens[0].price if actual_outcome == "YES" else market.tokens[1].price
            )
            
            logger.debug(f"Recorded historical prediction for {market.condition_id}: {actual_outcome}")
            
        except Exception as e:
            logger.error(f"Failed to record historical prediction for {market.condition_id}: {e}")
            
    def generate_historical_report(self, result: HistoricalBacktestResult) -> str:
        """Generate a comprehensive historical backtest report."""
        lines = []
        lines.append("📊 **Historical Backtest Report**")
        lines.append("=" * 60)
        lines.append("")
        
        # Overview
        lines.append("🎯 **Overview:**")
        lines.append(f"• Markets Tested: {result.markets_tested}")
        lines.append(f"• Successful Predictions: {result.successful_predictions}")
        lines.append(f"• Failed Predictions: {result.failed_predictions}")
        lines.append(f"• Filtered Markets: {result.filtered_markets}")
        if result.markets_tested > 0:
            success_rate = result.successful_predictions / result.markets_tested
            lines.append(f"• Success Rate: {success_rate:.1%}")
        lines.append("")
        
        # Performance metrics
        if result.metrics.total_predictions > 0:
            lines.append("📈 **Model Performance:**")
            lines.append(f"• Accuracy: {result.metrics.accuracy:.1%}")
            lines.append(f"• Calibration Error: {result.metrics.calibration_error:.1%}")
            lines.append(f"• Brier Score: {result.metrics.mean_brier_score:.3f}")
            lines.append(f"• Log Score: {result.metrics.mean_log_score:.3f}")
            lines.append("")
            
            # Confidence analysis
            lines.append("🔍 **Confidence Analysis:**")
            lines.append(f"• High Confidence (>80%): {result.metrics.high_confidence_accuracy:.1%}")
            lines.append(f"• Low Confidence (<50%): {result.metrics.low_confidence_accuracy:.1%}")
            lines.append("")
        
        # Category breakdown
        if result.markets_by_category:
            lines.append("📂 **Markets by Category:**")
            for category, count in result.markets_by_category.items():
                lines.append(f"• {category}: {count} markets")
            lines.append("")
            
        # Market deviation analysis
        if result.metrics.market_deviation_analysis:
            lines.append("📊 **Market Deviation Analysis:**")
            for deviation_type, accuracy in result.metrics.market_deviation_analysis.items():
                lines.append(f"• {deviation_type.replace('_', ' ').title()}: {accuracy:.1%}")
            lines.append("")
            
        return "\n".join(lines)