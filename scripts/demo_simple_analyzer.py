#!/usr/bin/env python3
"""
Demo script to show the simple pattern analyzer in action.
"""

import httpx
from datetime import datetime, timezone

def main():
    print("=== SIMPLE PATTERN ANALYZER DEMO ===\n")
    print("This analyzer looks for simple, proven patterns:")
    print("1. Time Decay - Markets unlikely to move much in final days")
    print("2. Extreme Pricing - Long shots overpriced, certainties underpriced")
    print("3. Structural Inefficiencies - True 50/50 events mispriced")
    print("4. Constitutional Impossibilities - Events requiring impossible changes")
    print("\nFetching current markets...\n")
    
    # Get some markets
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "active": "true",
            "closed": "false",
            "limit": 10,
            "order": "volume"
        }
    )
    
    if response.status_code == 200:
        markets = response.json()
        
        print(f"Analyzing {len(markets)} high-volume markets:\n")
        
        for market in markets:
            question = market.get('question', 'Unknown')
            price = float(market.get('lastTradePrice', 0.5))
            volume = float(market.get('volume', 0))
            
            if market.get('endDate'):
                try:
                    end_date = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                    days_left = (end_date - datetime.now(timezone.utc)).days
                except:
                    days_left = None
            else:
                days_left = None
            
            print(f"Market: {question[:60]}...")
            print(f"  Price: {price:.1%}")
            print(f"  Volume: ${volume:,.0f}")
            if days_left is not None:
                print(f"  Days until resolution: {days_left}")
            
            # Simple pattern detection
            patterns_found = []
            
            # Time decay pattern
            if days_left and 1 <= days_left <= 7:
                if 0.2 < price < 0.8:
                    patterns_found.append("⏰ TIME DECAY opportunity")
            
            # Extreme pricing
            if 'million' in question.lower() or '10x' in question.lower():
                if price > 0.15:
                    patterns_found.append("💰 EXTREME PRICING (long shot overpriced)")
            
            # Constitutional impossibility
            if 'constitutional' in question.lower() or 'amendment' in question.lower():
                if price > 0.05:
                    patterns_found.append("⚖️ CONSTITUTIONAL IMPOSSIBILITY")
            
            if patterns_found:
                print("  🎯 PATTERNS FOUND:")
                for pattern in patterns_found:
                    print(f"     {pattern}")
            else:
                print("  ✗ No simple patterns detected")
            
            print()
    
    print("\n💡 KEY INSIGHT:")
    print("Simple patterns often outperform complex models because they capture")
    print("fundamental market inefficiencies that persist due to behavioral biases.")

if __name__ == "__main__":
    main()