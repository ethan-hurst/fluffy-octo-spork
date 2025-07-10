#!/usr/bin/env python3
"""
Find the budget market that's being incorrectly returned
"""

import httpx
import asyncio

async def find_budget():
    """Find the budget market."""
    
    slug = "will-elon-register-the-america-party-by"
    
    async with httpx.AsyncClient() as client:
        # Get all markets
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "limit": 1000},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            
            # Find the budget market
            for market in markets:
                if "cut the budget by at least 10%" in market.get('question', ''):
                    print("Found the problematic market:")
                    print(f"Question: {market.get('question')}")
                    print(f"Slug: {market.get('slug')}")
                    
                    # Check if it would match
                    market_slug = market.get('slug', '').lower()
                    slug_clean = slug.lower()
                    
                    print(f"\nMatching analysis:")
                    print(f"Our slug: {slug_clean}")
                    print(f"Market slug: {market_slug}")
                    
                    # Check different matching methods
                    print(f"\nExact match: {slug_clean == market_slug}")
                    print(f"Partial match: {slug_clean in market_slug or market_slug in slug_clean}")
                    
                    # Check fuzzy match
                    slug_parts = set(slug_clean.split('-'))
                    market_parts = set(market_slug.split('-'))
                    overlap = slug_parts.intersection(market_parts)
                    
                    print(f"\nFuzzy match:")
                    print(f"Our parts: {slug_parts}")
                    print(f"Market parts: {market_parts}")
                    print(f"Overlap: {overlap}")
                    print(f"Overlap count: {len(overlap)}")
                    print(f"Required: {max(3, int(len(slug_parts) * 0.6))}")
                    
                    # This must be matching somehow
                    if len(overlap) >= 3:
                        print("\n⚠️ This would match with fuzzy logic!")
                    
                    break


if __name__ == "__main__":
    asyncio.run(find_budget())