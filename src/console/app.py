"""
Main console application for Polymarket analyzer.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import List, Optional, Dict

from src.analyzers.market_analyzer import MarketAnalyzer
from src.analyzers.models import AnalysisResult
from src.analyzers.news_correlator import NewsCorrelator
from src.analyzers.market_researcher import MarketResearcher
from src.clients.news.client import NewsClient
from src.clients.polymarket.client import PolymarketClient
from src.config.settings import settings
from src.console.display import DisplayManager
from src.utils.cache import api_cache
from src.utils.rate_limiter import rate_limiters
from src.utils.prediction_tracker import prediction_tracker
from src.console.chat import start_market_chat

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
        self.market_researcher = MarketResearcher()
        self.last_analysis: Optional[AnalysisResult] = None
        self.auto_reload_enabled = False
        self.high_confidence_only = False
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
            self.display.print_info("Type 'help' for available commands or 'start' to begin analysis.")
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
            except EOFError:
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
        
        if cmd == "start":
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
        elif cmd == "open" and args:
            self._open_market_link(args[0])
        elif cmd == "chat" and args:
            await self._start_market_chat(args[0])
        elif cmd == "research":
            if args:
                # Join args in case URL has spaces
                url = ' '.join(args)
                await self._research_market(url)
            else:
                self.display.print_error("Please provide a Polymarket URL")
                self.display.print_info("Usage: research <polymarket-url>")
        elif cmd == "filter":
            self._show_filter_commands(args)
        elif cmd == "filters":
            self._show_current_filters()
        elif cmd == "closing_soon":
            self._set_time_filter("closing_soon")
        elif cmd == "medium_term":
            self._set_time_filter("medium_term")
        elif cmd == "long_term":
            self._set_time_filter("long_term")
        elif cmd == "all_time":
            self._set_time_filter(None)
        elif cmd == "high_confidence":
            self._set_confidence_filter(True)
        elif cmd == "all_confidence":
            self._set_confidence_filter(False)
        elif cmd == "restart":
            await self._restart_application()
        elif cmd == "reload":
            self._reload_modules()
        elif cmd == "watch":
            self._toggle_auto_reload()
        elif cmd == "help":
            self.display.print_menu()
        elif cmd == "quit" or cmd == "exit":
            raise KeyboardInterrupt
        else:
            self.display.print_error(f"Unknown command: {cmd}")
            self.display.print_info("Type 'help' for available commands.")
            
    async def _run_analysis(self) -> None:
        """Run market analysis."""
        # Show current filters
        from src.utils.market_filters import market_filter
        filter_summary = market_filter.get_filter_summary()
        
        self.display.print_info("Starting market analysis...")
        self.display.print_info(f"Filters: {filter_summary}")
        
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
                
                # Use high confidence analyzer if filter is active
                if self.high_confidence_only:
                    from src.analyzers.high_confidence_analyzer import HighConfidenceAnalyzer
                    # Temporarily replace the analyzer
                    original_analyzer = self.market_analyzer.pattern_analyzer
                    self.market_analyzer.pattern_analyzer = HighConfidenceAnalyzer()
                    
                self.last_analysis = await self.market_analyzer.analyze_markets(
                    markets, market_prices, news_articles
                )
                
                # Restore original analyzer if needed
                if self.high_confidence_only:
                    self.market_analyzer.pattern_analyzer = original_analyzer
                
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
            self.display.print_warning("No analysis results available. Run 'start' first.")
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
            self.display.print_warning("No analysis results available. Run 'start' first.")
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
            self.display.print_warning("No predictions tracked yet. Run 'start' to begin tracking.")
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
        table.add_column("Question", style="white", width=35)
        table.add_column("Position", style="green", width=8)
        table.add_column("Confidence", style="yellow", width=10)
        table.add_column("Expected Return", style="blue", width=12)
        table.add_column("Status", style="magenta", width=10)
        table.add_column("Outcome", style="green", width=8)
        table.add_column("Market Link", style="blue", width=15)
        
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
                    
            # Format market link for display
            market_link = ""
            if hasattr(prediction, 'market_url') and prediction.market_url:
                # Extract just the condition ID for a shorter display
                condition_id = prediction.condition_id[:8] + "..." if len(prediction.condition_id) > 8 else prediction.condition_id
                market_link = f"[link={prediction.market_url}]{condition_id}[/link]"
            else:
                # Fallback for older predictions without URLs
                market_link = f"[link=https://polymarket.com/event/{prediction.condition_id}]{prediction.condition_id[:8]}...[/link]"
            
            table.add_row(
                prediction.prediction_date.strftime("%Y-%m-%d"),
                prediction.question[:32] + "..." if len(prediction.question) > 35 else prediction.question,
                prediction.predicted_position,
                f"{prediction.confidence_score:.2f}",
                f"{prediction.expected_return:+.1f}%",
                status,
                outcome,
                market_link
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
            
    def _open_market_link(self, condition_id: str) -> None:
        """
        Open market link in browser or display URL.
        
        Args:
            condition_id: Market condition ID
        """
        try:
            # Try to find the prediction with the condition ID
            predictions = prediction_tracker.load_predictions()
            
            # Find by exact condition ID or partial match
            matching_prediction = None
            for prediction in predictions:
                if prediction.condition_id == condition_id or prediction.condition_id.startswith(condition_id):
                    matching_prediction = prediction
                    break
                    
            if matching_prediction:
                market_url = matching_prediction.market_url
                if not market_url:
                    # Try to generate URL using slug if available
                    if hasattr(matching_prediction, 'market_slug') and matching_prediction.market_slug:
                        market_url = f"https://polymarket.com/{matching_prediction.market_slug}"
                    else:
                        market_url = f"https://polymarket.com/event/{matching_prediction.condition_id}"
                        
                self.display.print_success(f"Market URL: {market_url}")
                
                # Try to open in browser
                try:
                    import webbrowser
                    webbrowser.open(market_url)
                    self.display.print_info("Opening market in your default browser...")
                except Exception as e:
                    self.display.print_warning(f"Could not open browser: {e}")
                    self.display.print_info("You can copy the URL above to open manually")
            else:
                # Fallback - warn that we need a slug
                self.display.print_warning(f"Prediction not found locally for condition ID: {condition_id}")
                self.display.print_info("Polymarket uses slug-based URLs. To get the correct link:")
                self.display.print_info("1. Run 'start' to analyze current markets (gets slugs)")
                self.display.print_info("2. Check predictions again for working links")
                self.display.print_info(f"Fallback URL (may not work): https://polymarket.com/event/{condition_id}")
                    
        except Exception as e:
            self.display.print_error(f"Error opening market link: {e}")
            
    async def _start_market_chat(self, opportunity_id: str) -> None:
        """
        Start interactive chat about a specific market.
        
        Args:
            opportunity_id: Opportunity condition ID or rank number
        """
        if not self.last_analysis:
            self.display.print_warning("No analysis results available. Run 'start' first.")
            return
            
        # Find the opportunity
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
            
        # Start chat session
        start_market_chat(opportunity)
    
    async def _research_market(self, url: str) -> None:
        """
        Research a specific Polymarket URL.
        
        Args:
            url: Polymarket URL to research
        """
        self.display.print_info(f"🔍 Researching market: {url}")
        
        try:
            # Research the market
            result = await self.market_researcher.research_market(url)
            
            if 'error' in result:
                self.display.print_error(result['error'])
                return
            
            # Display research report
            self._display_research_report(result)
            
        except Exception as e:
            self.display.print_error(f"Research failed: {e}")
            logger.exception("Error researching market")
    
    def _display_research_report(self, report: Dict) -> None:
        """Display formatted research report."""
        # Check if it's a multi-outcome market
        if report.get('multi_outcome'):
            self._display_multi_outcome_report(report)
            return
            
        market = report['market']
        price = report['price']
        patterns = report['patterns']
        rec = report['recommendation']
        
        # Header
        self.display.console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]")
        self.display.console.print("[bold white]📈 MARKET RESEARCH REPORT[/bold white]")
        self.display.console.print("[bold cyan]" + "="*80 + "[/bold cyan]\n")
        
        # Market info
        self.display.console.print(f"[bold]📌 Market:[/bold] {market.question}")
        self.display.console.print(f"[bold]💰 Volume:[/bold] ${market.volume:,.0f}")
        self.display.console.print(f"[bold]📊 Current Price:[/bold] YES={price.yes_price:.1%} | NO={price.no_price:.1%}")
        
        # Time analysis
        if market.end_date_iso:
            days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
            self.display.console.print(f"[bold]⏰ Time Left:[/bold] {days_left} days")
        
        # Pattern analysis
        if patterns:
            self.display.console.print("\n[bold yellow]📋 Pattern Analysis:[/bold yellow]")
            for pattern in patterns[:5]:  # Show top 5 patterns
                self.display.console.print(f"  • {pattern['type']}: {pattern.get('keyword', pattern.get('target', ''))} ")
                self.display.console.print(f"    Typical: {pattern['typical_probability']:.0%} vs Current: {pattern['current_price']:.0%}")
        
        # Recommendation
        self.display.console.print("\n[bold cyan]" + "="*60 + "[/bold cyan]")
        self.display.console.print("[bold white]🎯 RECOMMENDATION[/bold white]")
        self.display.console.print("[bold cyan]" + "="*60 + "[/bold cyan]\n")
        
        if rec['position'] != 'NONE':
            # Recommendation details
            self.display.console.print(f"[bold green]✅ Position: BUY {rec['position']}[/bold green]")
            self.display.console.print(f"[bold]📊 Confidence:[/bold] {rec['confidence']:.0%}")
            self.display.console.print(f"[bold]💹 Expected Edge:[/bold] {rec['edge']:.1%}")
            
            # Reasons
            if rec['reasons']:
                self.display.console.print("\n[bold]📝 Analysis:[/bold]")
                for reason in rec['reasons']:
                    self.display.console.print(f"  • {reason}")
            
            # Trading suggestion
            if rec['position'] == 'YES':
                entry_price = price.yes_price
            else:
                entry_price = price.no_price
            
            target_price = min(0.95, entry_price + rec['edge'])
            potential_return = (target_price / entry_price - 1) * 100
            
            self.display.console.print(f"\n[bold]💸 Trading Suggestion:[/bold]")
            self.display.console.print(f"  Entry: {rec['position']} at {entry_price:.1%}")
            self.display.console.print(f"  Target: {target_price:.1%}")
            self.display.console.print(f"  Potential Return: {potential_return:.0f}%")
            
            # Score breakdown
            if 'score_yes' in rec and 'score_no' in rec:
                self.display.console.print(f"\n[bold]🏆 Score Breakdown:[/bold]")
                self.display.console.print(f"  YES Score: {rec['score_yes']:.1f}")
                self.display.console.print(f"  NO Score: {rec['score_no']:.1f}")
        else:
            self.display.console.print("[yellow]⚖️ No Clear Edge[/yellow]")
            self.display.console.print("The market appears fairly priced at current levels.")
        
        self.display.console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]\n")
    
    def _display_multi_outcome_report(self, report: Dict) -> None:
        """Display multi-outcome market research report."""
        from rich.table import Table
        
        market = report['market']
        analysis = report['analysis']
        
        # Header
        self.display.console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]")
        self.display.console.print("[bold white]📊 MULTI-OUTCOME MARKET ANALYSIS[/bold white]")
        self.display.console.print("[bold cyan]" + "="*80 + "[/bold cyan]\n")
        
        # Market info
        self.display.console.print(f"[bold]📌 Event:[/bold] {market.title}")
        self.display.console.print(f"[bold]💰 Total Volume:[/bold] ${market.total_volume:,.0f}")
        self.display.console.print(f"[bold]🎯 Options:[/bold] {len(market.options)}")
        
        if market.end_date:
            days_left = (market.end_date - datetime.now(timezone.utc)).days
            self.display.console.print(f"[bold]⏰ Time Left:[/bold] {days_left} days")
        
        # Market efficiency
        efficiency = analysis['market_efficiency']
        self.display.console.print(f"\n[bold]📊 Market Efficiency:[/bold]")
        self.display.console.print(f"  Total Probability: {efficiency['total_probability']:.1%}")
        self.display.console.print(f"  Efficiency Score: {efficiency['efficiency']:.1%}")
        
        if efficiency.get('arbitrage_possible'):
            self.display.console.print("  [red]⚠️ Arbitrage opportunity detected![/red]")
        
        # Options table
        table = Table(title="\n🎯 All Options", show_header=True, header_style="bold magenta")
        table.add_column("Candidate/Option", style="cyan", width=30)
        table.add_column("Price", justify="right", style="green")
        table.add_column("Volume", justify="right", style="yellow")
        table.add_column("Implied Prob", justify="right", style="blue")
        
        for option in market.options:
            table.add_row(
                option['name'],
                f"{option['price']:.2%}",
                f"${option['volume']:,.0f}",
                f"{option['implied_probability']:.1%}"
            )
        
        self.display.console.print(table)
        
        # Arbitrage opportunities
        if analysis.get('arbitrage'):
            arb = analysis['arbitrage']
            self.display.console.print(f"\n[bold red]💎 ARBITRAGE OPPORTUNITY:[/bold red]")
            self.display.console.print(f"  Type: {arb['type']}")
            self.display.console.print(f"  Cost: ${arb['total_cost']:.2f}")
            self.display.console.print(f"  Guaranteed Return: ${arb['guaranteed_return']:.2f}")
            self.display.console.print(f"  Profit: ${arb['profit']:.2f} ({arb['profit_percentage']:.1f}%)")
        
        # Trading opportunities
        if analysis.get('opportunities'):
            self.display.console.print(f"\n[bold yellow]💡 Trading Opportunities:[/bold yellow]")
            for opp in analysis['opportunities'][:3]:  # Show top 3
                self.display.console.print(f"\n  • {opp['candidate']} - {opp['position']}")
                self.display.console.print(f"    Reason: {opp['reason']}")
                self.display.console.print(f"    Current: {opp['current_price']:.2%} → Target: {opp['target_price']:.2%}")
                self.display.console.print(f"    Confidence: {opp['confidence']:.0%}")
        
        # Long shots
        if analysis.get('long_shots'):
            self.display.console.print(f"\n[bold]🎲 Long Shots (under 10%):[/bold]")
            for shot in analysis['long_shots']:
                self.display.console.print(f"  • {shot['name']}: {shot['price']:.1%} (${shot['volume']:,.0f} volume)")
        
        self.display.console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]\n")
        
    def _show_filter_commands(self, args: List[str]) -> None:
        """
        Show filter commands or set filters.
        
        Args:
            args: Filter command arguments
        """
        if not args:
            filter_help = """
[bold cyan]Market Filter Commands:[/bold cyan]

[bold yellow]Quick Time Filters (standalone commands):[/bold yellow]
[green]closing_soon[/green]     - Markets closing ≤30 days
[green]medium_term[/green]      - Markets closing 30-90 days  
[green]long_term[/green]        - Markets closing >90 days
[green]all_time[/green]         - Remove time filter

[bold yellow]Confidence Filters (standalone commands):[/bold yellow]
[green]high_confidence[/green]  - Only show high confidence opportunities (70%+)
[green]all_confidence[/green]   - Show all confidence levels (default)

[bold yellow]Advanced Filters (use with 'filter' prefix):[/bold yellow]
[green]filter categories politics,crypto[/green]    - Filter by categories
[green]filter keywords trump,bitcoin[/green]        - Filter by keywords
[green]filter max_days 30[/green]                   - Max days to resolution
[green]filter min_days 7[/green]                    - Min days to resolution
[green]filter clear[/green]                         - Clear all filters

[bold yellow]View Current Filters:[/bold yellow]
[green]filters[/green]          - Show active filters

[dim]Examples:[/dim]
[dim]  high_confidence                 # Enable high confidence filter[/dim]
[dim]  closing_soon                    # Quick filter for urgent markets[/dim]
[dim]  filter categories politics      # Only political markets[/dim]  
[dim]  filter keywords trump,election  # Only Trump or election markets[/dim]
"""
            self.display.console.print(filter_help)
            return
            
        # Handle filter commands
        if len(args) >= 2:
            filter_type = args[0]
            filter_value = args[1]
            
            if filter_type == "categories":
                self._set_category_filter(filter_value)
            elif filter_type == "keywords":
                self._set_keyword_filter(filter_value)
            elif filter_type == "max_days":
                try:
                    days = int(filter_value)
                    self._set_max_days_filter(days)
                except ValueError:
                    self.display.print_error("Invalid number for max_days")
            elif filter_type == "min_days":
                try:
                    days = int(filter_value)
                    self._set_min_days_filter(days)
                except ValueError:
                    self.display.print_error("Invalid number for min_days")
            else:
                self.display.print_error(f"Unknown filter type: {filter_type}")
        elif len(args) == 1 and args[0] == "clear":
            self._clear_all_filters()
        else:
            self.display.print_error("Invalid filter command. Use 'filter' for help.")
            
    def _show_current_filters(self) -> None:
        """Show current active filters."""
        from src.utils.market_filters import market_filter
        
        summary = market_filter.get_filter_summary()
        self.display.print_info(f"Current filters: {summary}")
        
    def _set_time_filter(self, time_horizon: Optional[str]) -> None:
        """
        Set time horizon filter.
        
        Args:
            time_horizon: Time horizon filter
        """
        from src.utils.market_filters import market_filter
        
        market_filter.time_horizon_filter = time_horizon
        
        if time_horizon:
            self.display.print_success(f"Time filter set to: {time_horizon}")
        else:
            self.display.print_success("Time filter cleared")
            
        self.display.print_info("Run 'start' to apply new filters")
        
    def _set_category_filter(self, categories: str) -> None:
        """
        Set category filter.
        
        Args:
            categories: Comma-separated categories
        """
        from src.utils.market_filters import market_filter
        
        market_filter.categories = market_filter._parse_comma_separated(categories)
        self.display.print_success(f"Category filter set to: {categories}")
        self.display.print_info("Run 'start' to apply new filters")
        
    def _set_keyword_filter(self, keywords: str) -> None:
        """
        Set keyword filter.
        
        Args:
            keywords: Comma-separated keywords
        """
        from src.utils.market_filters import market_filter
        
        market_filter.keywords = market_filter._parse_comma_separated(keywords)
        self.display.print_success(f"Keyword filter set to: {keywords}")
        self.display.print_info("Run 'start' to apply new filters")
        
    def _set_max_days_filter(self, days: int) -> None:
        """
        Set maximum days filter.
        
        Args:
            days: Maximum days to resolution
        """
        from src.utils.market_filters import market_filter
        
        market_filter.max_days_to_resolution = days
        self.display.print_success(f"Maximum days filter set to: {days}")
        self.display.print_info("Run 'start' to apply new filters")
        
    def _set_min_days_filter(self, days: int) -> None:
        """
        Set minimum days filter.
        
        Args:
            days: Minimum days to resolution
        """
        from src.utils.market_filters import market_filter
        
        market_filter.min_days_to_resolution = days
        self.display.print_success(f"Minimum days filter set to: {days}")
        self.display.print_info("Run 'start' to apply new filters")
        
    def _set_confidence_filter(self, high_confidence_only: bool) -> None:
        """
        Set high confidence filter.
        
        Args:
            high_confidence_only: Whether to show only high confidence opportunities
        """
        # Store the preference
        self.high_confidence_only = high_confidence_only
        
        if high_confidence_only:
            self.display.print_success("High confidence filter activated - will use specialized analyzer")
        else:
            self.display.print_success("All confidence levels enabled")
        self.display.print_info("Run 'start' to apply new filter.")
        
    def _clear_all_filters(self) -> None:
        """Clear all active filters."""
        from src.utils.market_filters import market_filter
        
        market_filter.categories = []
        market_filter.keywords = []
        market_filter.time_horizon_filter = None
        market_filter.max_days_to_resolution = None
        market_filter.min_days_to_resolution = None
        
        self.display.print_success("All filters cleared")
        self.display.print_info("Run 'start' to analyze all markets")
        
    async def _restart_application(self) -> None:
        """Restart the application gracefully."""
        self.display.print_info("Restarting application...")
        
        # Clear caches
        try:
            await api_cache.cleanup()
            self.display.print_success("Cache cleared")
        except Exception as e:
            self.display.print_warning(f"Cache cleanup failed: {e}")
        
        # Reload modules
        self._reload_modules()
        
        # Reset application state
        self.last_analysis = None
        
        # Clear screen and show banner
        self.display.clear_screen()
        self.display.print_banner()
        self.display.print_success("Application restarted successfully!")
        self.display.print_info("All modules reloaded, cache cleared, filters reset")
        self.display.print_info("Type 'help' for available commands or 'start' to begin analysis.")
        self.display.print()
        
    def _reload_modules(self) -> None:
        """Reload all application modules to pick up code changes."""
        import importlib
        import sys
        
        try:
            # Try to use enhanced reloader if available
            from src.utils.module_reloader import ModuleReloader
            
            packages_to_reload = [
                'src.analyzers',
                'src.clients',
                'src.config',
                'src.console',
                'src.utils'
            ]
            
            # Deep reload all packages
            reloaded_count = ModuleReloader.deep_reload(packages_to_reload)
            
            # Clear caches
            ModuleReloader.clear_instance_caches()
            
        except ImportError:
            # Fallback to basic reloading
            modules_to_reload = [
                'src.analyzers.market_analyzer',
                'src.analyzers.models', 
                'src.analyzers.news_correlator',
                'src.analyzers.market_researcher',
                'src.analyzers.high_confidence_analyzer',
                'src.analyzers.flexible_analyzer',
                'src.analyzers.simple_pattern_analyzer',
                'src.analyzers.kelly_criterion',
                'src.analyzers.backtesting',
                'src.clients.news.client',
                'src.clients.news.models',
                'src.clients.polymarket.client',
                'src.clients.polymarket.models',
                'src.config.settings',
                'src.console.display',
                'src.console.chat',
                'src.utils.cache',
                'src.utils.rate_limiter',
                'src.utils.prediction_tracker',
                'src.utils.market_filters',
                'src.utils.logger'
            ]
            
            reloaded_count = 0
            for module_name in modules_to_reload:
                try:
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                        reloaded_count += 1
                except Exception as e:
                    self.display.print_warning(f"Failed to reload {module_name}: {e}")
                
        # Reinitialize components with reloaded modules
        try:
            # Reimport classes after reload
            from src.analyzers.market_analyzer import MarketAnalyzer
            from src.analyzers.news_correlator import NewsCorrelator
            from src.analyzers.market_researcher import MarketResearcher
            from src.console.display import DisplayManager
            
            # Create new instances
            self.market_analyzer = MarketAnalyzer()
            self.news_correlator = NewsCorrelator()
            self.market_researcher = MarketResearcher()
            self.display = DisplayManager()
            
            # Reset global instances and singletons
            import src.utils.market_filters
            importlib.reload(src.utils.market_filters)
            
            # Force reload of settings
            import src.config.settings
            importlib.reload(src.config.settings)
            from src.config.settings import settings
            
            self.display.print_success(f"Reloaded {reloaded_count} modules and reinitialized all components")
            
        except Exception as e:
            self.display.print_error(f"Error reinitializing components: {e}")
            self.display.print_warning("Some features may not work correctly until full restart")
            
    def _toggle_auto_reload(self) -> None:
        """Toggle auto-reload functionality."""
        try:
            from src.utils.auto_reload import enable_auto_reload, disable_auto_reload
            
            if self.auto_reload_enabled:
                disable_auto_reload()
                self.auto_reload_enabled = False
                self.display.print_success("Auto-reload disabled")
                self.display.print_info("Changes to code will no longer trigger automatic reloads")
            else:
                enable_auto_reload(self)
                self.auto_reload_enabled = True
                self.display.print_success("Auto-reload enabled")
                self.display.print_info("Code changes will now automatically reload modules")
                self.display.print_warning("This is a development feature - disable for production")
                
        except Exception as e:
            self.display.print_error(f"Failed to toggle auto-reload: {e}")
            self.display.print_info("Auto-reload feature may not be available")


async def main() -> None:
    """Main entry point."""
    app = PolymarketAnalyzerApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())