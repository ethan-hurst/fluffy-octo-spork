#!/usr/bin/env python3
"""
Test the analyzer directly.
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.flexible_analyzer import FlexibleAnalyzer
from src.clients.polymarket.models import Market, MarketPrice, Token
from datetime import datetime, timezone, timedelta

def test_analyzer():
    """Test analyzer with sample data."""
    
    analyzer = FlexibleAnalyzer()
    print(f"Analyzer settings: min_edge={analyzer.min_edge}, min_volume={analyzer.min_volume}")
    
    # Test case 1: Longshot
    market1 = Market(
        condition_id="0x001",
        question="Will 2025 be the hottest year on record?",
        market_slug="test1",
        volume=1367331,
        active=True,
        closed=False,
        tokens=[
            Token(token_id="t1", outcome="YES", price=0.08),
            Token(token_id="t2", outcome="NO", price=0.92)
        ],
        minimum_order_size=0.01,
        end_date_iso=datetime.now(timezone.utc) + timedelta(days=300)
    )
    price1 = MarketPrice(
        condition_id="0x001",
        yes_price=0.08,
        no_price=0.92,
        spread=0.01
    )
    
    print("\nTest 1: Longshot market")
    print(f"Market: {market1.question}")
    print(f"Price: {price1.yes_price:.1%}")
    
    result1 = analyzer.analyze_market(market1, price1)
    if result1:
        print(f"✅ FOUND: {result1.pattern_type} - {result1.reason}")
        print(f"   Action: {result1.recommended_action}, Edge: {result1.edge:.2%}")
    else:
        print("❌ No opportunity found")
    
    # Test case 2: Bitcoin million
    market2 = Market(
        condition_id="0x002",
        question="Will Bitcoin reach $1 million by end of 2025?",
        market_slug="test2",
        volume=1111350,
        active=True,
        closed=False,
        tokens=[
            Token(token_id="t1", outcome="YES", price=0.10),
            Token(token_id="t2", outcome="NO", price=0.90)
        ],
        minimum_order_size=0.01,
        end_date_iso=datetime.now(timezone.utc) + timedelta(days=350)
    )
    price2 = MarketPrice(
        condition_id="0x002",
        yes_price=0.10,
        no_price=0.90,
        spread=0.01
    )
    
    print("\nTest 2: Bitcoin million")
    print(f"Market: {market2.question}")
    print(f"Price: {price2.yes_price:.1%}")
    
    result2 = analyzer.analyze_market(market2, price2)
    if result2:
        print(f"✅ FOUND: {result2.pattern_type} - {result2.reason}")
        print(f"   Action: {result2.recommended_action}, Edge: {result2.edge:.2%}")
    else:
        print("❌ No opportunity found")
    
    # Test case 3: Stable continuation
    market3 = Market(
        condition_id="0x003",
        question="Will the Fed continue to maintain interest rates above 4%?",
        market_slug="test3",
        volume=50000,
        active=True,
        closed=False,
        tokens=[
            Token(token_id="t1", outcome="YES", price=0.75),
            Token(token_id="t2", outcome="NO", price=0.25)
        ],
        minimum_order_size=0.01,
        end_date_iso=datetime.now(timezone.utc) + timedelta(days=20)
    )
    price3 = MarketPrice(
        condition_id="0x003",
        yes_price=0.75,
        no_price=0.25,
        spread=0.01
    )
    
    print("\nTest 3: Stable continuation")
    print(f"Market: {market3.question}")
    print(f"Price: {price3.yes_price:.1%}")
    
    result3 = analyzer.analyze_market(market3, price3)
    if result3:
        print(f"✅ FOUND: {result3.pattern_type} - {result3.reason}")
        print(f"   Action: {result3.recommended_action}, Edge: {result3.edge:.2%}")
    else:
        print("❌ No opportunity found")

if __name__ == "__main__":
    test_analyzer()