#!/usr/bin/env python3
"""
Main entry point for Polymarket Analyzer.

Usage:
    python main.py                    # Start interactive console
    python main.py research <url>     # Research a specific market
    python main.py --help            # Show help
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.console.app import PolymarketAnalyzerApp
from src.analyzers.market_researcher import MarketResearcher
from src.console.display import DisplayManager


async def research_market(url: str):
    """Research a specific market URL."""
    display = DisplayManager()
    researcher = MarketResearcher()
    
    display.print_info(f"🔍 Researching market: {url}")
    
    try:
        # Research the market
        result = await researcher.research_market(url)
        
        if 'error' in result:
            display.print_error(result['error'])
            return 1
        
        # Display research report
        display_research_report(display, result)
        return 0
        
    except Exception as e:
        display.print_error(f"Research failed: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        return 1


def display_multi_outcome_report(display: DisplayManager, report):
    """Display multi-outcome market report."""
    market = report['market']
    analysis = report['analysis']
    
    # Header
    display.console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]")
    display.console.print("[bold white]📊 MULTI-OUTCOME MARKET ANALYSIS[/bold white]")
    display.console.print("[bold cyan]" + "="*80 + "[/bold cyan]\n")
    
    # Market info
    display.console.print(f"[bold]📌 Market:[/bold] {market.title}")
    display.console.print(f"[bold]💰 Total Volume:[/bold] ${market.total_volume:,.0f}")
    display.console.print(f"[bold]🎯 Options:[/bold] {len(market.options)} candidates\n")
    
    # Top candidates
    display.console.print("[bold]🏆 Top Candidates:[/bold]")
    for i, opt in enumerate(analysis['top_candidates'][:5], 1):
        display.console.print(f"  {i}. {opt['name']}: {opt['implied_probability']:.1%} (${opt['volume']:,.0f})")
    
    # Market efficiency
    eff = analysis['market_efficiency']
    display.console.print(f"\n[bold]📊 Market Efficiency:[/bold]")
    display.console.print(f"  Total Probability: {eff['total_probability']:.1%}")
    display.console.print(f"  Efficiency Score: {eff.get('efficiency', eff.get('efficiency_score', 0)):.1%}")
    
    # Arbitrage opportunities
    if analysis['arbitrage']['opportunity_exists']:
        display.console.print(f"\n[bold green]💎 Arbitrage Opportunity![/bold green]")
        display.console.print(f"  Potential Profit: {analysis['arbitrage']['profit_percentage']:.1%}")
    
    # Trading opportunities
    if analysis['opportunities']:
        display.console.print(f"\n[bold]📈 Trading Opportunities:[/bold]")
        for opp in analysis['opportunities'][:3]:
            display.console.print(f"  • {opp['candidate']}: {opp['position']} at {opp['current_price']:.1%}")
            display.console.print(f"    Reason: {opp['reason']}")
    
    display.console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]\n")


def display_research_report(display: DisplayManager, report):
    """Display formatted research report."""
    from datetime import datetime, timezone
    
    # Check if it's a multi-outcome market
    if report.get('multi_outcome'):
        display_multi_outcome_report(display, report)
        return
    
    market = report['market']
    price = report['price']
    patterns = report['patterns']
    rec = report['recommendation']
    
    # Header
    display.console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]")
    display.console.print("[bold white]📈 MARKET RESEARCH REPORT[/bold white]")
    display.console.print("[bold cyan]" + "="*80 + "[/bold cyan]\n")
    
    # Market info
    display.console.print(f"[bold]📌 Market:[/bold] {market.question}")
    display.console.print(f"[bold]💰 Volume:[/bold] ${market.volume:,.0f}")
    display.console.print(f"[bold]📊 Current Price:[/bold] YES={price.yes_price:.1%} | NO={price.no_price:.1%}")
    
    # Time analysis
    if market.end_date_iso:
        days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
        display.console.print(f"[bold]⏰ Time Left:[/bold] {days_left} days")
    
    # Pattern analysis
    if patterns:
        display.console.print("\n[bold yellow]📋 Pattern Analysis:[/bold yellow]")
        for pattern in patterns[:5]:  # Show top 5 patterns
            display.console.print(f"  • {pattern['type']}: {pattern.get('keyword', pattern.get('target', ''))} ")
            display.console.print(f"    Typical: {pattern['typical_probability']:.0%} vs Current: {pattern['current_price']:.0%}")
    
    # Recommendation
    display.console.print("\n[bold cyan]" + "="*60 + "[/bold cyan]")
    display.console.print("[bold white]🎯 RECOMMENDATION[/bold white]")
    display.console.print("[bold cyan]" + "="*60 + "[/bold cyan]\n")
    
    if rec['position'] != 'NONE':
        # Recommendation details
        display.console.print(f"[bold green]✅ Position: BUY {rec['position']}[/bold green]")
        display.console.print(f"[bold]📊 Confidence:[/bold] {rec['confidence']:.0%}")
        display.console.print(f"[bold]💹 Expected Edge:[/bold] {rec['edge']:.1%}")
        
        # Reasons
        if rec['reasons']:
            display.console.print("\n[bold]📝 Analysis:[/bold]")
            for reason in rec['reasons']:
                display.console.print(f"  • {reason}")
        
        # Trading suggestion
        if rec['position'] == 'YES':
            entry_price = price.yes_price
        else:
            entry_price = price.no_price
        
        target_price = min(0.95, entry_price + rec['edge'])
        potential_return = (target_price / entry_price - 1) * 100
        
        display.console.print(f"\n[bold]💸 Trading Suggestion:[/bold]")
        display.console.print(f"  Entry: {rec['position']} at {entry_price:.1%}")
        display.console.print(f"  Target: {target_price:.1%}")
        display.console.print(f"  Potential Return: {potential_return:.0f}%")
        
        # Score breakdown
        if 'score_yes' in rec and 'score_no' in rec:
            display.console.print(f"\n[bold]🏆 Score Breakdown:[/bold]")
            display.console.print(f"  YES Score: {rec['score_yes']:.1f}")
            display.console.print(f"  NO Score: {rec['score_no']:.1f}")
    else:
        display.console.print("[yellow]⚖️ No Clear Edge[/yellow]")
        display.console.print("The market appears fairly priced at current levels.")
    
    display.console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]\n")


def show_help():
    """Show help message."""
    help_text = """
Polymarket Analyzer - Command Line Tool

Usage:
    python main.py                    Start interactive console
    python main.py research <url>     Research a specific Polymarket URL
    python main.py --help            Show this help message

Examples:
    python main.py
    python main.py research https://polymarket.com/event/bitcoin-150k-2025
    
Interactive Commands:
    start               - Run market analysis
    top                 - Show top opportunities
    research <url>      - Research specific market
    details <id>        - Show opportunity details
    metrics             - Show performance metrics
    help                - Show all commands
    quit                - Exit the application
"""
    print(help_text)


async def main():
    """Main entry point with command-line argument handling."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['--help', '-h', 'help']:
            show_help()
            return 0
            
        elif command == 'research':
            if len(sys.argv) < 3:
                print("Error: Please provide a Polymarket URL")
                print("Usage: python main.py research <url>")
                return 1
            
            # Join remaining args in case URL has spaces
            url = ' '.join(sys.argv[2:])
            return await research_market(url)
            
        else:
            print(f"Unknown command: {command}")
            print("Use 'python main.py --help' for usage information")
            return 1
    
    # No arguments - start interactive console
    app = PolymarketAnalyzerApp()
    await app.run()
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)