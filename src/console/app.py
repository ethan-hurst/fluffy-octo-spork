"""
Main console application for Polymarket analyzer.
"""

import asyncio
import logging
import sys
from typing import Optional

from src.analyzers.market_analyzer import MarketAnalyzer
from src.analyzers.models import AnalysisResult
from src.analyzers.news_correlator import NewsCorrelator
from src.clients.news.client import NewsClient
from src.clients.polymarket.client import PolymarketClient
from src.config.settings import settings
from src.console.display import DisplayManager
from src.utils.cache import api_cache
from src.utils.rate_limiter import rate_limiters
from src.utils.prediction_tracker import prediction_tracker

logger = logging.getLogger(__name__)


class PolymarketAnalyzerApp:
    """
    Main console application for analyzing Polymarket opportunities.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.display = DisplayManager()
        self.market_analyzer = MarketAnalyzer()
        self.news_correlator = NewsCorrelator()
        self.last_analysis: Optional[AnalysisResult] = None
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('polymarket_analyzer.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    async def run(self) -> None:
        """Run the main application loop."""
        try:
            self.display.clear_screen()
            self.display.print_banner()
            self.display.print_info("Welcome to Polymarket Analyzer!")
            self.display.print_info("Type 'help' for available commands or 'analyze' to start.")
            self.display.print()
            
            # Check API keys
            if not self._check_api_keys():
                return
                
            await self._main_loop()
            
        except KeyboardInterrupt:
            self.display.print_info("\nExiting Polymarket Analyzer. Goodbye!")
        except Exception as e:
            self.display.print_error(f"Unexpected error: {e}")
            logger.exception("Unexpected error in main application")
            
    def _check_api_keys(self) -> bool:
        """
        Check if required API keys are configured.
        
        Returns:
            bool: True if API keys are present
        """
        if not settings.news_api_key:
            self.display.print_error("NEWS_API_KEY not configured. Please set it in your .env file.")
            self.display.print_info("Get a free API key from: https://newsapi.org/register")
            return False
            
        # Polymarket API key is optional for public endpoints
        if not settings.polymarket_api_key:
            self.display.print_warning("POLYMARKET_API_KEY not configured. Some features may be limited.")
            
        return True
        
    async def _main_loop(self) -> None:
        """Main application loop."""
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if not command:
                    continue
                    
                await self._handle_command(command)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.display.print_error(f"Error processing command: {e}")
                logger.exception("Error processing command")
                
    async def _handle_command(self, command: str) -> None:
        """
        Handle user commands.
        
        Args:
            command: User command
        """
        parts = command.split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == "analyze":
            await self._run_analysis()
        elif cmd == "top":
            self._show_top_opportunities()
        elif cmd == "details" and args:
            await self._show_opportunity_details(args[0])
        elif cmd == "refresh":
            await self._refresh_and_analyze()
        elif cmd == "metrics":
            self._show_performance_metrics()
        elif cmd == "predictions":
            days = int(args[0]) if args and args[0].isdigit() else 30
            self._show_recent_predictions(days)
        elif cmd == "export" and args:
            self._export_predictions(args[0])
        elif cmd == "resolve" and len(args) >= 2:
            self._resolve_prediction(args[0], args[1])
        elif cmd == "help":
            self.display.print_menu()
        elif cmd == "quit" or cmd == "exit":
            raise KeyboardInterrupt
        else:
            self.display.print_error(f"Unknown command: {cmd}")
            self.display.print_info("Type 'help' for available commands.")
            
    async def _run_analysis(self) -> None:
        """Run market analysis."""
        self.display.print_info("Starting market analysis...")
        
        with self.display.create_progress("Analyzing markets") as progress:
            task = progress.add_task("Fetching data...", total=None)
            
            try:
                # Fetch markets
                progress.update(task, description="Fetching Polymarket markets...")
                await rate_limiters.polymarket.acquire()
                
                async with PolymarketClient() as polymarket_client:
                    markets = await polymarket_client.get_all_active_markets()
                    
                if not markets:
                    self.display.print_warning("No active markets found.")
                    return
                    
                # Get market prices
                progress.update(task, description="Calculating market prices...")
                market_prices = []
                for market in markets:
                    async with PolymarketClient() as polymarket_client:
                        price = await polymarket_client.get_market_prices(market)
                        if price:
                            market_prices.append(price)
                            
                # Fetch news
                progress.update(task, description="Fetching relevant news...")
                await rate_limiters.newsapi.acquire()
                
                async with NewsClient() as news_client:
                    news_articles = await news_client.get_relevant_news()
                    
                # Run analysis
                progress.update(task, description="Analyzing opportunities...")
                self.last_analysis = self.market_analyzer.analyze_markets(
                    markets, market_prices, news_articles
                )
                
                progress.update(task, description="Analysis complete!", completed=100)
                
            except Exception as e:
                self.display.print_error(f"Analysis failed: {e}")
                logger.exception("Analysis failed")
                return
                
        # Display results
        self.display.print_success("Analysis complete!")
        self.display.print_analysis_summary(self.last_analysis)
        
        if self.last_analysis.opportunities:
            # Log high-confidence predictions for tracking
            high_confidence_opportunities = [
                opp for opp in self.last_analysis.opportunities
                if opp.score.confidence_score >= 0.6 and opp.score.overall_score >= 0.5
            ]
            
            if high_confidence_opportunities:
                for opportunity in high_confidence_opportunities:
                    prediction_tracker.log_prediction(opportunity)
                    
                self.display.print_success(
                    f"Logged {len(high_confidence_opportunities)} high-confidence predictions for tracking."
                )
                
            self.display.print_top_opportunities(
                self.last_analysis.top_opportunities, 
                limit=10
            )
        else:
            self.display.print_warning("No opportunities found with current criteria.")
            self.display.print_info("Try adjusting the minimum spread or volume thresholds.")
            
    def _show_top_opportunities(self) -> None:
        """Show top opportunities."""
        if not self.last_analysis:
            self.display.print_warning("No analysis results available. Run 'analyze' first.")
            return
            
        if not self.last_analysis.opportunities:
            self.display.print_warning("No opportunities found in last analysis.")
            return
            
        self.display.print_top_opportunities(
            self.last_analysis.top_opportunities,
            limit=20
        )
        
    async def _show_opportunity_details(self, opportunity_id: str) -> None:
        """
        Show details for a specific opportunity.
        
        Args:
            opportunity_id: Opportunity condition ID or rank number
        """
        if not self.last_analysis:
            self.display.print_warning("No analysis results available. Run 'analyze' first.")
            return
            
        opportunity = None
        
        # Try to find by condition ID
        for opp in self.last_analysis.opportunities:
            if opp.condition_id == opportunity_id:
                opportunity = opp
                break
                
        # Try to find by rank number
        if not opportunity:
            try:
                rank = int(opportunity_id)
                if 1 <= rank <= len(self.last_analysis.top_opportunities):
                    opportunity = self.last_analysis.top_opportunities[rank - 1]
            except ValueError:
                pass
                
        if not opportunity:
            self.display.print_error(f"Opportunity not found: {opportunity_id}")
            self.display.print_info("Use the condition ID or rank number from the opportunities list.")
            return
            
        self.display.print_opportunity_details(opportunity)
        
    async def _refresh_and_analyze(self) -> None:
        """Refresh cache and run new analysis."""
        self.display.print_info("Clearing cache and refreshing data...")
        
        # Clear cache
        await api_cache.cleanup()
        
        # Run fresh analysis
        await self._run_analysis()
        
    def _show_performance_metrics(self) -> None:
        """Show prediction performance metrics."""
        metrics = prediction_tracker.calculate_metrics()
        
        if metrics.total_predictions == 0:
            self.display.print_warning("No predictions tracked yet. Run 'analyze' to start tracking.")
            return
            
        # Create metrics table
        from rich.table import Table
        
        table = Table(title="Prediction Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Predictions", str(metrics.total_predictions))
        table.add_row("Resolved Predictions", str(metrics.resolved_predictions))
        table.add_row("Correct Predictions", str(metrics.correct_predictions))
        table.add_row("Hit Rate", f"{metrics.hit_rate:.1%}")
        table.add_row("Average Confidence", f"{metrics.average_confidence:.3f}")
        table.add_row("Average Expected Return", f"{metrics.average_expected_return:.1f}%")
        table.add_row("Average Actual Return", f"{metrics.average_actual_return:.1f}%")
        table.add_row("Total ROI", f"{metrics.total_roi:.1f}%")
        table.add_row("Last Updated", metrics.last_updated.strftime("%Y-%m-%d %H:%M:%S"))
        
        self.display.console.print(table)
        
        # Show breakdown by risk level
        if metrics.predictions_by_risk:
            risk_table = Table(title="Performance by Risk Level")
            risk_table.add_column("Risk Level", style="cyan")
            risk_table.add_column("Total", style="blue")
            risk_table.add_column("Resolved", style="blue")
            risk_table.add_column("Correct", style="green")
            risk_table.add_column("Hit Rate", style="yellow")
            
            for risk_level, stats in metrics.predictions_by_risk.items():
                risk_table.add_row(
                    risk_level,
                    str(stats["total"]),
                    str(stats["resolved"]),
                    str(stats["correct"]),
                    f"{stats['hit_rate']:.1%}"
                )
                
            self.display.console.print(risk_table)
            
    def _show_recent_predictions(self, days: int = 30) -> None:
        """
        Show recent predictions.
        
        Args:
            days: Number of days to look back
        """
        predictions = prediction_tracker.get_recent_predictions(days)
        
        if not predictions:
            self.display.print_warning(f"No predictions found in the last {days} days.")
            return
            
        from rich.table import Table
        
        table = Table(title=f"Recent Predictions ({days} days)")
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Question", style="white", width=40)
        table.add_column("Position", style="green", width=8)
        table.add_column("Confidence", style="yellow", width=10)
        table.add_column("Expected Return", style="blue", width=12)
        table.add_column("Status", style="magenta", width=10)
        table.add_column("Outcome", style="green", width=8)
        
        for prediction in sorted(predictions, key=lambda x: x.prediction_date, reverse=True):
            status = "Resolved" if prediction.is_resolved else "Pending"
            outcome = ""
            
            if prediction.is_resolved:
                if prediction.prediction_correct:
                    outcome = "✓ Correct"
                elif prediction.prediction_correct is False:
                    outcome = "✗ Wrong"
                else:
                    outcome = "Invalid"
                    
            table.add_row(
                prediction.prediction_date.strftime("%Y-%m-%d"),
                prediction.question[:37] + "..." if len(prediction.question) > 40 else prediction.question,
                prediction.predicted_position,
                f"{prediction.confidence_score:.2f}",
                f"{prediction.expected_return:+.1f}%",
                status,
                outcome
            )
            
        self.display.console.print(table)
        
    def _export_predictions(self, filename: str) -> None:
        """
        Export predictions to CSV.
        
        Args:
            filename: Output filename
        """
        try:
            prediction_tracker.export_predictions_csv(filename)
            self.display.print_success(f"Predictions exported to {filename}")
        except Exception as e:
            self.display.print_error(f"Export failed: {e}")
            
    def _resolve_prediction(self, condition_id: str, outcome: str) -> None:
        """
        Manually resolve a prediction.
        
        Args:
            condition_id: Market condition ID
            outcome: Market outcome (YES, NO, or INVALID)
        """
        outcome = outcome.upper()
        if outcome not in ["YES", "NO", "INVALID"]:
            self.display.print_error("Outcome must be YES, NO, or INVALID")
            return
            
        # For manual resolution, we'll use 1.0 as final price for winning outcome
        final_price = 1.0 if outcome != "INVALID" else 0.5
        
        success = prediction_tracker.update_outcome(condition_id, outcome, final_price)
        
        if success:
            self.display.print_success(f"Updated prediction {condition_id} with outcome: {outcome}")
        else:
            self.display.print_error(f"Prediction not found: {condition_id}")


async def main() -> None:
    """Main entry point."""
    app = PolymarketAnalyzerApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())