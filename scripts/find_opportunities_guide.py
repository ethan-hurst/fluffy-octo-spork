#!/usr/bin/env python3
"""
Guide to finding opportunities with different filters.
"""

import httpx
from datetime import datetime, timezone
from collections import defaultdict

def analyze_current_markets():
    """Analyze current market conditions to suggest filters."""
    
    print("=== POLYMARKET OPPORTUNITY FINDER GUIDE ===\n")
    
    # Get all markets
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "active": "true",
            "closed": "false",
            "limit": 500  # Get more markets
        }
    )
    
    markets = response.json()
    print(f"Total active markets: {len(markets)}\n")
    
    # Analyze market characteristics
    categories = defaultdict(list)
    price_buckets = {
        'extreme_low': [],    # < 10%
        'low': [],           # 10-20%
        'moderate_low': [],  # 20-35%
        'middle': [],        # 35-65%
        'moderate_high': [], # 65-80%
        'high': [],          # 80-90%
        'extreme_high': []   # > 90%
    }
    
    time_buckets = {
        'urgent': [],      # < 7 days
        'short': [],       # 7-14 days
        'medium': [],      # 14-30 days
        'long': []         # > 30 days
    }
    
    keywords_found = defaultdict(int)
    
    for market in markets:
        question = market.get('question', '')
        price = float(market.get('lastTradePrice', 0.5))
        volume = float(market.get('volume', 0))
        
        # Skip very low volume
        if volume < 1000:
            continue
            
        # Categorize by price
        if price < 0.10:
            price_buckets['extreme_low'].append((question, price, volume))
        elif price < 0.20:
            price_buckets['low'].append((question, price, volume))
        elif price < 0.35:
            price_buckets['moderate_low'].append((question, price, volume))
        elif price < 0.65:
            price_buckets['middle'].append((question, price, volume))
        elif price < 0.80:
            price_buckets['moderate_high'].append((question, price, volume))
        elif price < 0.90:
            price_buckets['high'].append((question, price, volume))
        else:
            price_buckets['extreme_high'].append((question, price, volume))
            
        # Categorize by time
        if market.get('endDate'):
            try:
                end_date = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                days_left = (end_date - datetime.now(timezone.utc)).days
                
                if 0 <= days_left < 7:
                    time_buckets['urgent'].append((question, price, volume, days_left))
                elif 7 <= days_left < 14:
                    time_buckets['short'].append((question, price, volume, days_left))
                elif 14 <= days_left < 30:
                    time_buckets['medium'].append((question, price, volume, days_left))
                else:
                    time_buckets['long'].append((question, price, volume, days_left))
            except:
                pass
                
        # Extract keywords
        words = question.lower().split()
        for word in words:
            if len(word) > 4:  # Skip short words
                keywords_found[word] += 1
                
        # Categorize
        question_lower = question.lower()
        if 'bitcoin' in question_lower or 'btc' in question_lower or 'crypto' in question_lower:
            categories['crypto'].append((question, price, volume))
        elif 'election' in question_lower or 'president' in question_lower:
            categories['politics'].append((question, price, volume))
        elif 'game' in question_lower or 'match' in question_lower or 'championship' in question_lower:
            categories['sports'].append((question, price, volume))
        elif 'company' in question_lower or 'stock' in question_lower or 'ceo' in question_lower:
            categories['business'].append((question, price, volume))
        elif 'weather' in question_lower or 'temperature' in question_lower or 'climate' in question_lower:
            categories['climate'].append((question, price, volume))
    
    # Print analysis
    print("=== MARKET DISTRIBUTION ===")
    print("\nBy Price:")
    for bucket, markets_list in price_buckets.items():
        if markets_list:
            print(f"  {bucket}: {len(markets_list)} markets")
            
    print("\nBy Time to Resolution:")
    for bucket, markets_list in time_buckets.items():
        if markets_list:
            print(f"  {bucket}: {len(markets_list)} markets")
            
    print("\nBy Category:")
    for cat, markets_list in categories.items():
        if markets_list:
            print(f"  {cat}: {len(markets_list)} markets")
    
    # Suggest filters
    print("\n=== RECOMMENDED FILTERS FOR OPPORTUNITIES ===\n")
    
    print("1. EXTREME LONGSHOTS (filter_extreme_low):")
    print("   Command: filter_extreme_low")
    print("   Look for: Markets < 10% that should be < 2%")
    if price_buckets['extreme_low']:
        print(f"   Available: {len(price_buckets['extreme_low'])} markets")
        for q, p, v in sorted(price_buckets['extreme_low'], key=lambda x: x[2], reverse=True)[:3]:
            print(f"   - {q[:60]}... ({p:.0%}, ${v:,.0f})")
    
    print("\n2. OVERPRICED MODERATE EVENTS (filter_low):")
    print("   Command: filter_low")
    print("   Look for: Markets 10-20% that might be overpriced")
    if price_buckets['low']:
        print(f"   Available: {len(price_buckets['low'])} markets")
        for q, p, v in sorted(price_buckets['low'], key=lambda x: x[2], reverse=True)[:3]:
            print(f"   - {q[:60]}... ({p:.0%}, ${v:,.0f})")
    
    print("\n3. HIGH CONFIDENCE EVENTS (filter_high):")
    print("   Command: filter_high")
    print("   Look for: Markets 80-90% that should be higher")
    if price_buckets['high']:
        print(f"   Available: {len(price_buckets['high'])} markets")
        for q, p, v in sorted(price_buckets['high'], key=lambda x: x[2], reverse=True)[:3]:
            print(f"   - {q[:60]}... ({p:.0%}, ${v:,.0f})")
    
    print("\n4. TIME DECAY OPPORTUNITIES:")
    if time_buckets['urgent'] or time_buckets['short']:
        print("   Command: closing_soon")
        print("   Look for: Markets ending soon with stable prices")
        all_soon = time_buckets['urgent'] + time_buckets['short']
        print(f"   Available: {len(all_soon)} markets ending in < 14 days")
        for q, p, v, d in sorted(all_soon, key=lambda x: x[2], reverse=True)[:3]:
            print(f"   - {q[:60]}... ({p:.0%}, {d} days)")
    else:
        print("   Command: max_days 30")
        print("   Look for: Markets ending within 30 days")
        print(f"   Available: {len(time_buckets['medium'])} markets")
    
    print("\n5. CATEGORY FILTERS:")
    for cat, markets_list in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        if len(markets_list) >= 5:
            print(f"   category {cat}")
            print(f"   Available: {len(markets_list)} markets")
    
    print("\n6. KEYWORD SEARCH:")
    print("   Command: keyword <word>")
    print("   Popular keywords:")
    for word, count in sorted(keywords_found.items(), key=lambda x: x[1], reverse=True)[:10]:
        if count >= 3 and word not in ['will', 'the', 'this', 'that', 'what', 'when']:
            print(f"   - {word} ({count} markets)")
    
    print("\n=== COMBINED FILTER STRATEGIES ===\n")
    
    print("Strategy 1 - Find Extreme Mispricings:")
    print("  1. filter_extreme_low")
    print("  2. Look for 'million', 'record', 'perfect' keywords")
    print("  3. These are often overpriced longshots\n")
    
    print("Strategy 2 - Time Decay on Stable Events:")
    print("  1. max_days 30")
    print("  2. category sports")
    print("  3. Look for prices 20-35% or 65-80%\n")
    
    print("Strategy 3 - High Volume Opportunities:")
    print("  1. No filters (to see all)")
    print("  2. Sort by volume")
    print("  3. Look for prices far from 50% in high volume markets\n")
    
    print("Strategy 4 - Specific Event Types:")
    print("  1. keyword 'record' or 'highest' or 'lowest'")
    print("  2. These extreme events are often overpriced\n")
    
    # Show some specific opportunities
    print("=== CURRENT OPPORTUNITY EXAMPLES ===\n")
    
    # Find potential opportunities
    opportunities = []
    
    # Check extreme low prices
    for q, p, v in price_buckets['extreme_low']:
        if v >= 10000:  # Decent volume
            if any(kw in q.lower() for kw in ['million', 'record', 'perfect', 'all-time']):
                opportunities.append(('EXTREME_LONGSHOT', q, p, v, 'BUY NO'))
    
    # Check high confidence
    for q, p, v in price_buckets['high']:
        if v >= 10000:
            if any(kw in q.lower() for kw in ['remain', 'continue', 'still']):
                opportunities.append(('HIGH_CONFIDENCE', q, p, v, 'BUY YES'))
    
    # Check moderate prices for patterns
    for q, p, v in price_buckets['moderate_low'] + price_buckets['moderate_high']:
        if v >= 20000:  # Higher volume requirement
            q_lower = q.lower()
            # Binary events
            if any(kw in q_lower for kw in ['coin', 'random', '50/50']):
                if abs(p - 0.5) > 0.1:
                    action = 'BUY NO' if p > 0.5 else 'BUY YES'
                    opportunities.append(('BINARY_MISPRICING', q, p, v, action))
    
    if opportunities:
        print("Found potential opportunities:")
        for pattern, q, p, v, action in sorted(opportunities, key=lambda x: x[3], reverse=True)[:10]:
            print(f"\n{pattern}:")
            print(f"  {q}")
            print(f"  Current: {p:.1%} | Volume: ${v:,.0f}")
            print(f"  Suggested: {action}")
    else:
        print("No obvious opportunities in current market conditions.")
        print("Try the filter strategies above to find more subtle edges.")

if __name__ == "__main__":
    analyze_current_markets()