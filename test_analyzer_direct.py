#!/usr/bin/env python3
"""Test the analyzer directly."""

import asyncio
from src.console.app import PolymarketAnalyzerApp

async def test_analyzer():
    """Test the analyzer functionality."""
    app = PolymarketAnalyzerApp()
    
    # Run analysis directly
    print("Starting market analysis...")
    await app._run_analysis()
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    asyncio.run(test_analyzer())