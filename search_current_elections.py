#!/usr/bin/env python3
"""
Search for current election markets
"""

import httpx
import asyncio
import json
from datetime import datetime

async def search_elections():
    """Search for current election markets."""
    
    async with httpx.AsyncClient() as client:
        print("=== SEARCHING CURRENT ELECTION MARKETS ===\n")
        
        # Search for 2025/2026 election markets
        keywords = ['2025', '2026', 'election', 'president', 'nominee', 'primary']
        
        for keyword in keywords:
            response = await client.get(
                "https://gamma-api.polymarket.com/markets",
                params={"search": keyword, "active": "true", "limit": 50},
                timeout=30.0
            )
            
            if response.status_code == 200:
                markets = response.json()
                
                # Filter for election-related
                election_markets = []
                for market in markets:
                    q = market.get('question', '').lower()
                    if any(term in q for term in ['president', 'election', 'nominee', 'primary', 'governor', 'senate']):
                        election_markets.append(market)
                
                if election_markets:
                    print(f"\n--- {keyword.upper()} Election Markets ---")
                    for market in election_markets[:10]:
                        print(f"\nQuestion: {market.get('question')}")
                        print(f"Slug: {market.get('slug')}")
                        print(f"Volume: ${float(market.get('volume', 0)):,.0f}")
                        print(f"Price: {market.get('lastTradePrice')}")
                        print(f"URL: https://polymarket.com/event/{market.get('slug')}")
        
        # Try to find markets with similar candidates/options
        print("\n\n--- CHECKING FOR RELATED MARKETS ---")
        
        # Get all active markets
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "limit": 1000},
            timeout=30.0
        )
        
        if response.status_code == 200:
            all_markets = response.json()
            
            # Group by similar patterns
            candidate_markets = {}
            
            for market in all_markets:
                question = market.get('question', '')
                
                # Pattern: "Will X win/be the Y?"
                if 'win' in question.lower() or 'nominee' in question.lower():
                    # Extract candidate name (simplified)
                    for name in ['Trump', 'Biden', 'DeSantis', 'Kennedy', 'Newsom', 'Ramaswamy', 'Haley']:
                        if name in question:
                            if name not in candidate_markets:
                                candidate_markets[name] = []
                            candidate_markets[name].append(market)
            
            # Show candidates with multiple markets
            print("\nCandidate-related markets:")
            for candidate, markets in candidate_markets.items():
                if len(markets) > 1:
                    print(f"\n{candidate}: {len(markets)} markets")
                    for market in markets[:3]:
                        print(f"  - {market.get('question')}")

if __name__ == "__main__":
    asyncio.run(search_elections())