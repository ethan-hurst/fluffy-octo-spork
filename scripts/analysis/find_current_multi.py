#!/usr/bin/env python3
"""
Find current multi-outcome markets
"""

import httpx
import asyncio
import json
from collections import defaultdict

async def find_current_multi():
    """Find current multi-outcome markets by looking for patterns."""
    
    async with httpx.AsyncClient() as client:
        print("Searching for multi-outcome markets...\n")
        
        # Get all active markets
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "closed": "false", "limit": 1000},
            timeout=30.0
        )
        
        if response.status_code == 200:
            markets = response.json()
            print(f"Found {len(markets)} active markets")
            
            # Group markets by common patterns
            pattern_groups = defaultdict(list)
            
            for market in markets:
                question = market.get('question', '')
                slug = market.get('slug', '')
                
                # Look for "Who will win" patterns
                if 'who will win' in question.lower():
                    pattern_groups['who_will_win'].append(market)
                
                # Look for specific candidate names in similar questions
                if 'will' in question.lower() and 'win' in question.lower():
                    # Extract pattern
                    words = question.lower().split()
                    if 'will' in words and 'win' in words:
                        will_idx = words.index('will')
                        win_idx = words.index('win')
                        if will_idx < win_idx and will_idx + 1 < len(words):
                            candidate = words[will_idx + 1]
                            if candidate not in ['the', 'a', 'an']:
                                pattern_key = ' '.join(words[win_idx:])  # Everything after "win"
                                pattern_groups[pattern_key].append(market)
                
                # Presidential/election patterns
                if 'president' in question.lower() or 'nominee' in question.lower():
                    pattern_groups['presidential'].append(market)
                
                # Sports patterns
                if any(sport in question.lower() for sport in ['nba', 'nfl', 'mlb', 'championship', 'super bowl']):
                    pattern_groups['sports'].append(market)
            
            # Find groups with multiple related markets
            print("\nPotential multi-outcome market groups:")
            for pattern, group_markets in pattern_groups.items():
                if len(group_markets) >= 3:  # At least 3 related markets
                    print(f"\n{pattern.upper()}: {len(group_markets)} markets")
                    
                    # Show first few
                    for market in group_markets[:5]:
                        print(f"  - {market.get('question')[:60]}...")
                        print(f"    Volume: ${float(market.get('volume', 0)):,.0f}")
                        print(f"    Price: {market.get('lastTradePrice', 0):.2%}")
                    
                    if len(group_markets) > 5:
                        print(f"  ... and {len(group_markets) - 5} more")
            
            # Look for specific examples
            print("\n\nChecking for specific multi-outcome examples...")
            
            # Find markets with numbers in similar patterns
            number_patterns = defaultdict(list)
            for market in markets:
                question = market.get('question', '')
                # Look for temperature, price, or number predictions
                if any(char.isdigit() for char in question):
                    # Group by removing numbers
                    pattern = ''.join(['X' if c.isdigit() else c for c in question])
                    number_patterns[pattern].append(market)
            
            for pattern, group in number_patterns.items():
                if len(group) >= 3:
                    print(f"\nNumber pattern group: {len(group)} markets")
                    for market in group[:3]:
                        print(f"  - {market.get('question')}")
            
            # Save some examples
            if pattern_groups['presidential']:
                print("\n\nExample multi-outcome market URL:")
                market = pattern_groups['presidential'][0]
                print(f"https://polymarket.com/event/{market.get('slug')}")

if __name__ == "__main__":
    asyncio.run(find_current_multi())