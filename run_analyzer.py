#!/usr/bin/env python3
"""Run the Polymarket analyzer to show real market opportunities."""

import asyncio
from src.console.app import PolymarketAnalyzerApp

async def run_analyzer():
    """Run the analyzer and display results."""
    app = PolymarketAnalyzerApp()
    
    print("Running Polymarket Analyzer on real markets...")
    print("-" * 80)
    
    # Run analysis
    await app._run_analysis()
    
    # Show the results (already displayed by the analyzer)
    print("\n" + "-" * 80)
    print("Analysis complete! The markets shown above are real and accessible on Polymarket.")
    print("\nExample URLs:")
    print("- https://polymarket.com/event/russia-x-ukraine-ceasefire-in-2025")
    print("- https://polymarket.com/event/us-recession-in-2025")
    print("- https://polymarket.com/event/nuclear-weapon-detonation-in-2025")

if __name__ == "__main__":
    asyncio.run(run_analyzer())