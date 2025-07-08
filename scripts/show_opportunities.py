#!/usr/bin/env python3
"""
Show specific opportunity examples.
"""

import httpx
from datetime import datetime, timezone

def main():
    print("=== SEARCHING FOR OPPORTUNITIES ===\n")
    
    # Get markets
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "active": "true",
            "closed": "false",
            "limit": 200
        }
    )
    
    markets = response.json()
    
    # Look for specific patterns
    opportunities = {
        'longshots': [],
        'high_confidence': [],
        'binary': [],
        'impossible': []
    }
    
    for market in markets:
        question = market.get('question', '')
        price = float(market.get('lastTradePrice', 0.5))
        volume = float(market.get('volume', 0))
        
        if volume < 5000:
            continue
            
        question_lower = question.lower()
        
        # Longshots (5-15%)
        if 0.05 < price < 0.15:
            if any(kw in question_lower for kw in [
                'million', '10x', 'all-time high', 'record', 'perfect'
            ]):
                opportunities['longshots'].append((question, price, volume))
        
        # High confidence continuation (70-90%)
        if 0.70 < price < 0.90:
            if any(kw in question_lower for kw in [
                'remain', 'continue', 'stay', 'still be', 'maintain'
            ]):
                opportunities['high_confidence'].append((question, price, volume))
        
        # Binary events far from 50%
        if any(kw in question_lower for kw in ['coin', 'random', 'odd or even']):
            if abs(price - 0.5) > 0.1:
                opportunities['binary'].append((question, price, volume))
        
        # Near impossibilities
        if any(kw in question_lower for kw in [
            'constitutional', 'abolish', 'merge states', 'rename'
        ]):
            if price > 0.05:
                opportunities['impossible'].append((question, price, volume))
    
    # Display results
    print("=== LONGSHOT OPPORTUNITIES (BUY NO) ===")
    if opportunities['longshots']:
        for q, p, v in opportunities['longshots'][:5]:
            print(f"\n{q}")
            print(f"Price: {p:.1%} | Volume: ${v:,.0f}")
            print(f"💡 Likely overpriced longshot")
    else:
        print("None found")
    
    print("\n=== HIGH CONFIDENCE CONTINUATION (BUY YES) ===")
    if opportunities['high_confidence']:
        for q, p, v in opportunities['high_confidence'][:5]:
            print(f"\n{q}")
            print(f"Price: {p:.1%} | Volume: ${v:,.0f}")
            print(f"💡 Stable continuation event possibly underpriced")
    else:
        print("None found")
    
    print("\n=== BINARY MISPRICING ===")
    if opportunities['binary']:
        for q, p, v in opportunities['binary'][:5]:
            print(f"\n{q}")
            print(f"Price: {p:.1%} | Volume: ${v:,.0f}")
            print(f"💡 True 50/50 event mispriced")
    else:
        print("None found")
    
    print("\n=== NEAR IMPOSSIBILITIES (BUY NO) ===")
    if opportunities['impossible']:
        for q, p, v in opportunities['impossible'][:5]:
            print(f"\n{q}")
            print(f"Price: {p:.1%} | Volume: ${v:,.0f}")
            print(f"💡 Nearly impossible event overpriced")
    else:
        print("None found")
    
    # Show some actual markets
    print("\n=== SAMPLE HIGH VOLUME MARKETS ===")
    high_volume = sorted(markets, key=lambda x: x.get('volume', 0), reverse=True)
    
    for market in high_volume[:10]:
        q = market.get('question', '')
        p = float(market.get('lastTradePrice', 0.5))
        v = float(market.get('volume', 0))
        
        print(f"\n{q[:80]}...")
        print(f"Price: {p:.1%} | Volume: ${v:,.0f}")

if __name__ == "__main__":
    main()