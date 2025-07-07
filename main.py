#!/usr/bin/env python3
"""
Main entry point for Polymarket Analyzer.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.console.app import main

if __name__ == "__main__":
    asyncio.run(main())