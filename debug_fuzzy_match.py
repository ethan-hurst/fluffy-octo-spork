#!/usr/bin/env python3
"""
Debug why the fuzzy match is happening
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analyzers.market_researcher import MarketResearcher


async def debug_match():
    """Debug the matching."""
    
    researcher = MarketResearcher()
    
    # Our slug
    our_slug = "will-elon-register-the-america-party-by"
    
    # The market that's being returned
    wrong_market = {
        'slug': 'will-elon-cut-the-budget-by-at-least-10-in-2025',
        'question': 'Will Elon cut the budget by at least 10% in 2025?',
        'conditionId': '0x123'
    }
    
    print(f"Our slug: {our_slug}")
    print(f"Wrong market slug: {wrong_market['slug']}")
    
    # Test the match
    matches = researcher._check_market_match(wrong_market, our_slug, None)
    print(f"\nDoes it match? {matches}")
    
    if matches:
        # Debug why
        market_slug = wrong_market['slug'].lower()
        slug_clean = our_slug.lower()
        
        print("\nDEBUG:")
        print(f"Exact match: {slug_clean == market_slug}")
        print(f"Partial in: {slug_clean in market_slug}")
        print(f"Partial in reverse: {market_slug in slug_clean}")
        
        # Check x replacement
        slug_x = slug_clean.replace('-x-', '-').replace('-×-', '-')
        market_x = market_slug.replace('-x-', '-').replace('-×-', '-')
        print(f"After X replacement: {slug_x in market_x or market_x in slug_x}")
        
        # Fuzzy match
        slug_parts = set(slug_clean.split('-'))
        market_parts = set(market_slug.split('-'))
        overlap = slug_parts.intersection(market_parts)
        
        print(f"\nFuzzy matching:")
        print(f"Our parts: {slug_parts}")
        print(f"Market parts: {market_parts}")
        print(f"Overlap: {overlap}")
        print(f"Overlap count: {len(overlap)}")
        print(f"Required (60% of {len(slug_parts)}): {max(3, int(len(slug_parts) * 0.6))}")


if __name__ == "__main__":
    asyncio.run(debug_match())