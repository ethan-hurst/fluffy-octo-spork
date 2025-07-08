#!/usr/bin/env python3
"""
Check what markets are available.
"""

import httpx
from datetime import datetime, timezone

def main():
    print("=== POLYMARKET ANALYSIS ===\n")
    
    # Get markets
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "active": "true",
            "closed": "false",
            "limit": 100
        }
    )
    
    markets = response.json()
    print(f"Total markets fetched: {len(markets)}\n")
    
    # Categorize by days left
    by_days = {
        'ending_today': [],
        'ending_week': [],
        'ending_month': [],
        'long_term': [],
        'no_date': []
    }
    
    # Price distribution
    price_ranges = {
        'extreme_low': [],  # < 10%
        'low': [],          # 10-30%
        'medium': [],       # 30-70%
        'high': [],         # 70-90%
        'extreme_high': []  # > 90%
    }
    
    for market in markets:
        question = market.get('question', '')
        price = float(market.get('lastTradePrice', 0.5))
        volume = float(market.get('volume', 0))
        
        # Skip very low volume
        if volume < 1000:
            continue
            
        # Categorize by price
        if price < 0.1:
            price_ranges['extreme_low'].append((question, price, volume))
        elif price < 0.3:
            price_ranges['low'].append((question, price, volume))
        elif price < 0.7:
            price_ranges['medium'].append((question, price, volume))
        elif price < 0.9:
            price_ranges['high'].append((question, price, volume))
        else:
            price_ranges['extreme_high'].append((question, price, volume))
        
        # Categorize by time
        if market.get('endDate'):
            try:
                end_date = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                days_left = (end_date - datetime.now(timezone.utc)).days
                
                if days_left < 0:
                    continue  # Already ended
                elif days_left == 0:
                    by_days['ending_today'].append((question, price, volume, days_left))
                elif days_left <= 7:
                    by_days['ending_week'].append((question, price, volume, days_left))
                elif days_left <= 30:
                    by_days['ending_month'].append((question, price, volume, days_left))
                else:
                    by_days['long_term'].append((question, price, volume, days_left))
            except:
                by_days['no_date'].append((question, price, volume, None))
        else:
            by_days['no_date'].append((question, price, volume, None))
    
    # Print analysis
    print("=== TIME ANALYSIS ===")
    print(f"Ending today: {len(by_days['ending_today'])}")
    print(f"Ending this week (1-7 days): {len(by_days['ending_week'])}")
    print(f"Ending this month (8-30 days): {len(by_days['ending_month'])}")
    print(f"Long term (>30 days): {len(by_days['long_term'])}")
    print(f"No end date: {len(by_days['no_date'])}")
    
    print("\n=== PRICE DISTRIBUTION ===")
    print(f"Extreme low (<10%): {len(price_ranges['extreme_low'])}")
    print(f"Low (10-30%): {len(price_ranges['low'])}")
    print(f"Medium (30-70%): {len(price_ranges['medium'])}")
    print(f"High (70-90%): {len(price_ranges['high'])}")
    print(f"Extreme high (>90%): {len(price_ranges['extreme_high'])}")
    
    # Show time decay opportunities
    print("\n=== POTENTIAL TIME DECAY OPPORTUNITIES ===")
    opportunities = []
    
    # Markets ending soon with non-extreme prices
    for markets_list in [by_days['ending_today'], by_days['ending_week']]:
        for question, price, volume, days in markets_list:
            if volume >= 5000:  # Decent volume
                if 0.15 < price < 0.35 or 0.65 < price < 0.85:
                    opportunities.append((question, price, volume, days))
    
    if opportunities:
        print(f"\nFound {len(opportunities)} potential opportunities:")
        # Sort by volume
        opportunities.sort(key=lambda x: x[2], reverse=True)
        
        for i, (q, p, v, d) in enumerate(opportunities[:10]):
            print(f"\n{i+1}. {q[:70]}...")
            print(f"   Price: {p:.1%} | Volume: ${v:,.0f} | Days left: {d}")
            
            # Check if it's crypto/volatile
            q_lower = q.lower()
            if any(kw in q_lower for kw in ['bitcoin', 'btc', 'eth', 'crypto']):
                print("   ⚠️  Crypto market - volatile")
            elif any(kw in q_lower for kw in ['game', 'match', 'vs', 'election']):
                print("   ✓ Stable market type")
    else:
        print("No time decay opportunities found")
        
        # Show what's ending soon regardless
        print("\n=== MARKETS ENDING THIS WEEK ===")
        week_markets = by_days['ending_today'] + by_days['ending_week']
        week_markets.sort(key=lambda x: x[2], reverse=True)  # Sort by volume
        
        for q, p, v, d in week_markets[:10]:
            print(f"\n- {q[:70]}...")
            print(f"  Price: {p:.1%} | Volume: ${v:,.0f} | Days: {d}")

if __name__ == "__main__":
    main()