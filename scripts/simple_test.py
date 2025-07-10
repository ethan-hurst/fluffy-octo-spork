#!/usr/bin/env python3
"""Simple test to check if we can find opportunities."""

import asyncio
import httpx
from datetime import datetime

async def simple_test():
    """Direct API test."""
    async with httpx.AsyncClient() as client:
        # Get just first page of current markets
        print("Fetching current markets from Gamma API...")
        
        response = await client.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "closed": "false", "limit": 10},
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return
            
        markets = response.json()
        
        # Filter for current markets with good volume
        current_markets = []
        now = datetime.now()
        
        for market in markets:
            if market.get('endDate'):
                try:
                    end_date = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                    volume = float(market.get('volume', 0) or 0)
                    
                    if end_date > now.replace(tzinfo=end_date.tzinfo) and volume > 1000:
                        current_markets.append(market)
                except:
                    pass
        
        print(f"\nFound {len(current_markets)} current markets with volume > $1000")
        
        if current_markets:
            print("\nAnalyzing markets for opportunities...")
            print("-" * 80)
            
            for market in current_markets[:3]:
                question = market['question']
                volume = float(market.get('volume', 0) or 0)
                
                # Get prices from market data
                best_bid = float(market.get('bestBid', 0) or 0)
                best_ask = float(market.get('bestAsk', 0) or 0)
                last_price = float(market.get('lastTradePrice', 0) or 0)
                
                print(f"\n{question[:70]}...")
                print(f"Volume: ${volume:,.0f}")
                print(f"Prices - Bid: {best_bid:.2f}, Ask: {best_ask:.2f}, Last: {last_price:.2f}")
                
                # Simple fair value check - just use 50% as baseline for now
                fair_value = 0.5
                
                # For specific types of questions, adjust baseline
                if "trump" in question.lower() and "repeal" in question.lower() and "term limits" in question.lower():
                    fair_value = 0.01  # Very unlikely
                elif "tariffs" in question.lower():
                    fair_value = 0.7  # More likely
                elif "etf" in question.lower() and "approved" in question.lower():
                    fair_value = 0.4  # Moderate chance
                
                current_price = last_price if last_price > 0 else best_bid
                diff = abs(fair_value - current_price)
                
                print(f"Simple fair value: {fair_value:.2f}, Current: {current_price:.2f}, Diff: {diff:.2f}")
                
                if diff >= 0.05:  # 5% threshold
                    print("✓ POTENTIAL OPPORTUNITY!")
                else:
                    print("✗ Difference too small")

if __name__ == "__main__":
    asyncio.run(simple_test())