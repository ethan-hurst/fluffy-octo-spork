"""
Display utilities for console output.
"""

from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from src.analyzers.models import AnalysisResult, MarketOpportunity


class DisplayManager:
    """
    Manages console display and formatting.
    """
    
    def __init__(self):
        """Initialize display manager."""
        self.console = Console()
        
    def print_banner(self) -> None:
        """Print application banner."""
        banner = """
    ███╗   ███╗ █████╗ ██████╗ ██╗  ██╗███████╗████████╗    ███████╗██████╗  ██████╗ ███████╗
    ████╗ ████║██╔══██╗██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝    ██╔════╝██╔══██╗██╔════╝ ██╔════╝
    ██╔████╔██║███████║██████╔╝█████╔╝ █████╗     ██║       █████╗  ██║  ██║██║  ███╗█████╗  
    ██║╚██╔╝██║██╔══██║██╔══██╗██╔═██╗ ██╔══╝     ██║       ██╔══╝  ██║  ██║██║   ██║██╔══╝  
    ██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██╗███████╗   ██║       ███████╗██████╔╝╚██████╔╝███████╗
    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝       ╚══════╝╚═════╝  ╚═════╝ ╚══════╝
    
                         🎯 INTELLIGENT PREDICTION MARKET ANALYZER 🎯
                            Find High-Value Opportunities & Track Performance
        """
        self.console.print(banner, style="bold blue")
        
    def print_analysis_summary(self, result: AnalysisResult) -> None:
        """
        Print analysis summary.
        
        Args:
            result: Analysis result to display
        """
        summary_table = Table(title="Analysis Summary", show_header=False)
        summary_table.add_column("Metric", style="cyan", width=30)
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Markets Analyzed", str(result.total_markets_analyzed))
        summary_table.add_row("Opportunities Found", str(len(result.opportunities)))
        summary_table.add_row("High Confidence Opportunities", str(len(result.high_confidence_opportunities)))
        summary_table.add_row("News Articles Processed", str(result.news_articles_processed))
        summary_table.add_row("Analysis Duration", f"{result.analysis_duration_seconds:.2f} seconds")
        summary_table.add_row("Analysis Time", result.analyzed_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        self.console.print(summary_table)
        self.console.print()
        
    def print_top_opportunities(self, opportunities: List[MarketOpportunity], limit: int = 10) -> None:
        """
        Print top opportunities table.
        
        Args:
            opportunities: List of opportunities
            limit: Maximum number to display
        """
        if not opportunities:
            self.console.print("No opportunities found.", style="yellow")
            return
            
        table = Table(title=f"Top {limit} Opportunities")
        table.add_column("Rank", style="cyan", width=4)
        table.add_column("Question", style="white", width=50)
        table.add_column("Position", style="green", width=8)
        table.add_column("Current", style="blue", width=8)
        table.add_column("Fair", style="blue", width=8)
        table.add_column("Return", style="green", width=8)
        table.add_column("Score", style="yellow", width=8)
        table.add_column("Risk", style="red", width=8)
        
        for i, opp in enumerate(opportunities[:limit], 1):
            current_price = opp.current_yes_price if opp.recommended_position == "YES" else opp.current_no_price
            fair_price = opp.fair_yes_price if opp.recommended_position == "YES" else opp.fair_no_price
            
            # Color code the return
            return_style = "green" if opp.expected_return > 0 else "red"
            
            table.add_row(
                str(i),
                opp.question[:47] + "..." if len(opp.question) > 50 else opp.question,
                opp.recommended_position,
                f"{current_price:.3f}",
                f"{fair_price:.3f}",
                f"[{return_style}]{opp.expected_return:+.1f}%[/{return_style}]",
                f"{opp.score.overall_score:.3f}",
                self._get_risk_color(opp.risk_level)
            )
            
        self.console.print(table)
        self.console.print()
        
    def print_opportunity_details(self, opportunity: MarketOpportunity) -> None:
        """
        Print detailed information about an opportunity.
        
        Args:
            opportunity: Opportunity to display
        """
        # Create main panel
        content = []
        
        # Market info
        content.append(f"[bold]Market:[/bold] {opportunity.question}")
        if opportunity.description:
            content.append(f"[bold]Description:[/bold] {opportunity.description}")
        if opportunity.category:
            content.append(f"[bold]Category:[/bold] {opportunity.category}")
            
        content.append("")
        
        # Current prices
        content.append("[bold]Current Prices:[/bold]")
        content.append(f"  YES: {opportunity.current_yes_price:.3f}")
        content.append(f"  NO:  {opportunity.current_no_price:.3f}")
        content.append(f"  Spread: {opportunity.current_spread:.3f}")
        
        content.append("")
        
        # Fair prices
        content.append("[bold]Fair Value Analysis:[/bold]")
        content.append(f"  Fair YES: {opportunity.fair_yes_price:.3f}")
        content.append(f"  Fair NO:  {opportunity.fair_no_price:.3f}")
        
        content.append("")
        
        # Recommendation
        position_color = "green" if opportunity.expected_return > 0 else "red"
        content.append(f"[bold]Recommendation:[/bold] [{position_color}]{opportunity.recommended_position}[/{position_color}]")
        content.append(f"[bold]Expected Return:[/bold] [{position_color}]{opportunity.expected_return:+.1f}%[/{position_color}]")
        content.append(f"[bold]Risk Level:[/bold] {self._get_risk_color(opportunity.risk_level)}")
        
        content.append("")
        
        # Scores
        content.append("[bold]Scoring Breakdown:[/bold]")
        content.append(f"  Overall Score:     {opportunity.score.overall_score:.3f}")
        content.append(f"  Value Score:       {opportunity.score.value_score:.3f}")
        content.append(f"  Confidence Score:  {opportunity.score.confidence_score:.3f}")
        content.append(f"  Volume Score:      {opportunity.score.volume_score:.3f}")
        content.append(f"  Time Score:        {opportunity.score.time_score:.3f}")
        content.append(f"  News Relevance:    {opportunity.score.news_relevance_score:.3f}")
        
        content.append("")
        
        # Market data
        if opportunity.volume:
            content.append(f"[bold]Volume:[/bold] ${opportunity.volume:,.2f}")
        if opportunity.liquidity:
            content.append(f"[bold]Liquidity:[/bold] ${opportunity.liquidity:,.2f}")
        if opportunity.end_date:
            content.append(f"[bold]End Date:[/bold] {opportunity.end_date.strftime('%Y-%m-%d %H:%M')}")
            
        content.append("")
        
        # Kelly Criterion analysis
        if opportunity.kelly_analysis:
            kelly = opportunity.kelly_analysis
            content.append("[bold]Kelly Criterion Position Sizing:[/bold]")
            content.append(f"  Recommended Position: {kelly.recommended_fraction:.1%} of bankroll")
            content.append(f"  Expected Value: {kelly.expected_value:.1%}")
            content.append(f"  Kelly Recommendation: {kelly.recommendation}")
            content.append(f"  Probability of Ruin: {kelly.probability_of_ruin:.1%}")
            
            if kelly.warnings:
                content.append("  [yellow]Warnings:[/yellow]")
                for warning in kelly.warnings[:2]:  # Show top 2 warnings
                    content.append(f"    • {warning}")
                    
            content.append("")
        
        # Analysis reasoning
        content.append(f"[bold]Analysis Reasoning:[/bold]")
        content.append(f"  {opportunity.reasoning}")
        
        # Related news
        if opportunity.related_news:
            content.append("")
            content.append("[bold]Related News:[/bold]")
            for i, headline in enumerate(opportunity.related_news[:3], 1):
                content.append(f"  {i}. {headline}")
                
        panel_content = "\n".join(content)
        panel = Panel(panel_content, title=f"Opportunity Details - {opportunity.condition_id}")
        self.console.print(panel)
        self.console.print()
        
    def print_error(self, message: str) -> None:
        """
        Print error message.
        
        Args:
            message: Error message to display
        """
        self.console.print(f"[red]Error:[/red] {message}")
        
    def print_warning(self, message: str) -> None:
        """
        Print warning message.
        
        Args:
            message: Warning message to display
        """
        self.console.print(f"[yellow]Warning:[/yellow] {message}")
        
    def print_info(self, message: str) -> None:
        """
        Print info message.
        
        Args:
            message: Info message to display
        """
        self.console.print(f"[blue]Info:[/blue] {message}")
        
    def print_success(self, message: str) -> None:
        """
        Print success message.
        
        Args:
            message: Success message to display
        """
        self.console.print(f"[green]Success:[/green] {message}")
        
    def create_progress(self, description: str) -> Progress:
        """
        Create progress bar.
        
        Args:
            description: Progress description
            
        Returns:
            Progress: Progress bar instance
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        )
        
    def _get_risk_color(self, risk_level: str) -> str:
        """
        Get colored risk level text.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            str: Colored risk level
        """
        colors = {
            "MINIMAL": "[bright_green]MINIMAL[/bright_green]",
            "LOW": "[green]LOW[/green]",
            "MEDIUM": "[yellow]MEDIUM[/yellow]",
            "HIGH": "[red]HIGH[/red]",
            "EXTREME": "[bold red]EXTREME[/bold red]"
        }
        return colors.get(risk_level, risk_level)
        
    def print_menu(self) -> None:
        """Print main menu options."""
        menu_text = """
[bold cyan]Available Commands:[/bold cyan]

[bold yellow]Analysis Commands:[/bold yellow]
[green]start[/green]                - Run market analysis
[green]top[/green]                  - Show top opportunities  
[green]details <id>[/green]         - Show opportunity details
[green]chat <id>[/green]            - Interactive chat about a specific market
[green]research <url>[/green]       - Research a specific Polymarket URL
[green]refresh[/green]              - Refresh data and re-analyze

[bold yellow]Market Filter Commands:[/bold yellow]
[green]high_confidence[/green]      - Only show high confidence opportunities (70%+)
[green]all_confidence[/green]       - Show all confidence levels (default)
[green]closing_soon[/green]         - Markets closing ≤30 days
[green]medium_term[/green]          - Markets closing 30-90 days
[green]long_term[/green]            - Markets closing >90 days
[green]category <name>[/green]      - Filter by category (politics, crypto, sports, etc.)
[green]all_categories[/green]       - Clear category filter
[green]filter[/green]               - Show filter help & advanced options
[green]filters[/green]              - Show current active filters

[bold yellow]Tracking Commands:[/bold yellow]
[green]metrics[/green]              - Show prediction performance metrics
[green]predictions [days][/green]   - Show recent predictions (default: 30 days)
[green]export <filename>[/green]    - Export predictions to CSV
[green]resolve <id> <outcome>[/green] - Manually resolve prediction (YES/NO/INVALID)
[green]open <condition_id>[/green]  - Open market link in browser

[bold yellow]General Commands:[/bold yellow]
[green]help[/green]                 - Show this menu
[green]restart[/green]              - Restart app (reload all modules & clear cache)
[green]reload[/green]               - Reload modules only (faster than restart)
[green]watch[/green]                - Toggle auto-reload on file changes (dev mode)
[green]quit[/green]                 - Exit application

[dim]Examples:[/dim]
[dim]  category politics      - Only analyze politics markets[/dim]
[dim]  category crypto,sports - Analyze crypto AND sports markets[/dim]
[dim]  closing_soon           - Filter for markets closing ≤30 days[/dim]
[dim]  filter keywords trump  - Only analyze Trump-related markets[/dim]
[dim]  chat 1                 - Chat about the #1 ranked opportunity[/dim]
[dim]  details 3              - Show details for #3 opportunity[/dim]
[dim]  predictions 7          - Show predictions from last 7 days[/dim]
[dim]  open 12345678          - Open market link in browser[/dim]

Enter command: 
        """
        self.console.print(menu_text)
        
    def clear_screen(self) -> None:
        """Clear the console screen."""
        self.console.clear()
        
    def print(self, *args, **kwargs) -> None:
        """Print to console (convenience method)."""
        if not args:
            self.console.print()
        else:
            self.console.print(*args, **kwargs)