#!/usr/bin/env python3
"""Test the async fair value engine integration."""

import asyncio
from src.console.app import PolymarketAnalyzerApp

async def test_async_analyzer():
    """Test the analyzer with async fair value calculations."""
    app = PolymarketAnalyzerApp()
    
    print("Testing Polymarket Analyzer with sophisticated fair value engine...")
    print("-" * 80)
    
    # Check if Claude API is configured
    from src.config.settings import settings
    if settings.claude_api_key:
        print("✅ Claude API key is configured - will use LLM analysis")
    else:
        print("⚠️  Claude API key not configured - will use enhanced keyword analysis")
    
    print("\nRunning analysis...")
    
    # Run analysis
    await app._run_analysis()
    
    print("\n" + "-" * 80)
    print("Analysis complete!")

if __name__ == "__main__":
    asyncio.run(test_async_analyzer())