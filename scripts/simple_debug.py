#!/usr/bin/env python3
"""
Simple debug to check current markets.
"""

import httpx
from datetime import datetime, timezone

def main():
    print("=== CHECKING CURRENT POLYMARKET DATA ===\n")
    
    # Get markets from gamma API
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "active": "true",
            "closed": "false",
            "limit": 30,
            "order": "volume"
        }
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
        
    markets = response.json()
    print(f"Found {len(markets)} markets\n")
    
    # Analyze each market
    time_decay_candidates = []
    
    for i, market in enumerate(markets[:20]):
        question = market.get('question', '')
        price = float(market.get('lastTradePrice', 0.5))
        volume = float(market.get('volume', 0))
        
        # Skip low volume
        if volume < 10000:
            continue
            
        # Calculate days left
        days_left = None
        if market.get('endDate'):
            try:
                end_date = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                days_left = (end_date - datetime.now(timezone.utc)).days
            except:
                pass
        
        print(f"{i+1}. {question[:70]}...")
        print(f"   Price: {price:.1%} | Volume: ${volume:,.0f} | Days left: {days_left}")
        
        # Check for opportunities
        opportunities = []
        
        # Time decay check
        if days_left and 1 <= days_left <= 7:
            if 0.15 < price < 0.35:
                opportunities.append(f"TIME DECAY: Low price ({price:.0%}) unlikely to rise in {days_left} days")
            elif 0.65 < price < 0.85:
                opportunities.append(f"TIME DECAY: High price ({price:.0%}) unlikely to fall in {days_left} days")
                
        # Check for volatile keywords
        question_lower = question.lower()
        is_volatile = any(kw in question_lower for kw in [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'stock', 'meme'
        ])
        
        # Check for stable keywords
        is_stable = any(kw in question_lower for kw in [
            'game', 'match', 'vs', 'beat', 'win', 'championship', 'election'
        ])
        
        if is_volatile:
            print("   ⚠️  Volatile market (crypto/stock)")
        elif is_stable:
            print("   ✓  Stable market type")
            
        if opportunities:
            print("   🎯 OPPORTUNITIES:")
            for opp in opportunities:
                print(f"      - {opp}")
            if days_left and 1 <= days_left <= 7 and not is_volatile:
                time_decay_candidates.append({
                    'question': question,
                    'price': price,
                    'volume': volume,
                    'days_left': days_left
                })
        
        print()
    
    print("\n=== SUMMARY ===")
    print(f"Time decay candidates found: {len(time_decay_candidates)}")
    
    if time_decay_candidates:
        print("\nBest candidates:")
        for candidate in time_decay_candidates[:5]:
            print(f"- {candidate['question'][:60]}...")
            print(f"  {candidate['price']:.0%} with {candidate['days_left']} days left")

if __name__ == "__main__":
    main()