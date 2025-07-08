#!/usr/bin/env python3
"""Run analysis directly."""

import asyncio
import sys
from src.console.app import PolymarketAnalyzer

async def run():
    """Run the analyzer."""
    app = PolymarketAnalyzer()
    await app.run_async()
    
    # Run analysis directly
    print("\nRunning analysis...")
    await app._handle_start_command()
    
    # Exit
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run())