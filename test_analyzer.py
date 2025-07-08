#!/usr/bin/env python3
"""Test the analyzer with gamma API."""

import asyncio
from src.console.app import PolymarketAnalyzerApp

async def test_analyzer():
    """Test the analyzer functionality."""
    analyzer = PolymarketAnalyzerApp()
    
    # Run analysis
    print("Starting market analysis...")
    await analyzer.start(max_markets=10)
    
    # The results should already be displayed by the analyzer

if __name__ == "__main__":
    asyncio.run(test_analyzer())