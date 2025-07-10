#!/usr/bin/env python3
"""
Enhanced opportunity finder that searches for more trading opportunities.
"""

import httpx
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
import sys

class OpportunityFinder:
    def __init__(self):
        self.api_url = "https://gamma-api.polymarket.com"
        self.min_volume = 5000
        self.min_edge = 0.05  # 5% minimum edge
        
    def fetch_active_markets(self, limit: int = 500) -> List[Dict]:
        """Fetch all active markets."""
        response = httpx.get(
            f"{self.api_url}/markets",
            params={
                "active": "true",
                "closed": "false",
                "limit": limit
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_extreme_longshots(self, market: Dict) -> Optional[Tuple[str, float, str]]:
        """Find overpriced extreme longshots."""
        price = float(market.get('lastTradePrice', 0.5))
        question = market.get('question', '').lower()
        
        # Pattern 1: Extreme records/milestones
        if 0.05 < price < 0.20:
            extreme_patterns = [
                ('reach $1 million', 0.01),
                ('reach $1 billion', 0.001),
                ('1000x', 0.02),
                ('10000x', 0.001),
                ('break all-time high', 0.03),
                ('world record', 0.02),
                ('unanimous', 0.01),
                ('sweep all', 0.02),
                ('perfect season', 0.01),
                ('100% accuracy', 0.001),
                ('hottest year on record', 0.02),
                ('coldest year on record', 0.02),
                ('most ever', 0.02),
                ('least ever', 0.02),
                ('highest ever', 0.02),
                ('lowest ever', 0.02),
                ('record-breaking', 0.03),
                ('win every', 0.01),
                ('lose every', 0.01),
                ('zero', 0.02),
                ('none', 0.02),
                ('extinct', 0.01),
                ('completely', 0.02),
                ('entirely', 0.02),
                ('nobody', 0.01),
                ('everyone', 0.01),
                ('all countries', 0.01),
                ('every state', 0.01),
                ('100 million', 0.03),
                ('1 billion', 0.02),
            ]
            
            for pattern, fair_value in extreme_patterns:
                if pattern in question:
                    edge = price - fair_value
                    if edge >= self.min_edge:
                        return ("EXTREME_LONGSHOT", edge, f"'{pattern}' suggests ~{fair_value:.0%} probability, currently {price:.0%}")
        
        return None
    
    def analyze_high_confidence_continuations(self, market: Dict) -> Optional[Tuple[str, float, str]]:
        """Find underpriced high-confidence events."""
        price = float(market.get('lastTradePrice', 0.5))
        question = market.get('question', '').lower()
        
        # Pattern 2: Things that almost always continue
        if 0.70 < price < 0.90:
            continuation_patterns = [
                ('remain', 0.92),
                ('continue', 0.90),
                ('stay', 0.91),
                ('maintain', 0.90),
                ('will still', 0.92),
                ('keep', 0.90),
                ('hold', 0.88),
                ('re-elected', 0.85),
                ('incumbent', 0.88),
                ('defend', 0.85),
                ('retain', 0.90),
                ('survive', 0.88),
            ]
            
            for pattern, fair_value in continuation_patterns:
                if pattern in question:
                    edge = fair_value - price
                    if edge >= self.min_edge:
                        return ("CONTINUATION", edge, f"'{pattern}' events typically have {fair_value:.0%} success rate, currently {price:.0%}")
        
        return None
    
    def analyze_impossibilities(self, market: Dict) -> Optional[Tuple[str, float, str]]:
        """Find overpriced near-impossibilities."""
        price = float(market.get('lastTradePrice', 0.5))
        question = market.get('question', '').lower()
        
        # Pattern 3: Near impossibilities
        if price > 0.05:
            impossible_patterns = [
                ('constitutional amendment', 0.001),
                ('abolish the', 0.005),
                ('merge states', 0.001),
                ('change the flag', 0.01),
                ('rename the country', 0.001),
                ('dissolve', 0.01),
                ('eliminate all', 0.01),
                ('ban all', 0.01),
                ('outlaw', 0.02),
                ('declare war', 0.01),
                ('invade', 0.02),
                ('annex', 0.01),
                ('secede', 0.01),
                ('overthrow', 0.01),
                ('revolution', 0.02),
                ('civil war', 0.01),
                ('nuclear', 0.01),
                ('world war', 0.001),
                ('extinction', 0.001),
                ('asteroid', 0.001),
                ('alien', 0.001),
            ]
            
            for pattern, fair_value in impossible_patterns:
                if pattern in question:
                    edge = price - fair_value
                    if edge >= self.min_edge:
                        return ("IMPOSSIBILITY", edge, f"'{pattern}' has ~{fair_value:.1%} probability, currently {price:.0%}")
        
        return None
    
    def analyze_binary_events(self, market: Dict) -> Optional[Tuple[str, float, str]]:
        """Find mispriced binary events."""
        price = float(market.get('lastTradePrice', 0.5))
        question = market.get('question', '').lower()
        
        # Pattern 4: True 50/50 events mispriced
        fifty_fifty_patterns = [
            'coin flip', 'coin toss', 'heads or tails',
            'odd or even', 'red or black', 'random',
            'lottery', 'dice', 'roulette'
        ]
        
        for pattern in fifty_fifty_patterns:
            if pattern in question:
                distance = abs(price - 0.5)
                if distance > 0.10:
                    if price > 0.5:
                        edge = price - 0.52
                        action = "overpriced"
                    else:
                        edge = 0.48 - price
                        action = "underpriced"
                    
                    if edge >= self.min_edge:
                        return ("BINARY_50_50", edge, f"True 50/50 event '{pattern}' is {action} at {price:.0%}")
        
        return None
    
    def analyze_time_decay(self, market: Dict) -> Optional[Tuple[str, float, str]]:
        """Find opportunities based on time decay."""
        price = float(market.get('lastTradePrice', 0.5))
        question = market.get('question', '').lower()
        end_date = market.get('endDate')
        
        if not end_date:
            return None
            
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            days_left = (end_dt - datetime.now(timezone.utc)).days
            
            # Pattern 5: Short-term stable events
            if 7 <= days_left <= 30:
                # Events unlikely to change in short term
                if 0.70 < price < 0.85:
                    stable_patterns = [
                        'remain above', 'remain below', 'stay above', 'stay below',
                        'continue to', 'maintain', 'hold above', 'hold below'
                    ]
                    
                    for pattern in stable_patterns:
                        if pattern in question:
                            # Short term continuations have high probability
                            fair_value = 0.90 if days_left < 14 else 0.88
                            edge = fair_value - price
                            if edge >= self.min_edge:
                                return ("TIME_DECAY", edge, f"Stable event with {days_left} days left, should be ~{fair_value:.0%}")
                
                # Events very unlikely in short term
                elif 0.10 < price < 0.30:
                    unlikely_patterns = [
                        'resign', 'quit', 'step down', 'fired', 'impeached',
                        'arrested', 'indicted', 'convicted', 'die', 'pass away'
                    ]
                    
                    for pattern in unlikely_patterns:
                        if pattern in question:
                            # Short term dramatic events are rare
                            fair_value = 0.05 if days_left < 14 else 0.08
                            edge = price - fair_value
                            if edge >= self.min_edge:
                                return ("TIME_DECAY", edge, f"Unlikely event with {days_left} days left, should be ~{fair_value:.0%}")
        except:
            pass
            
        return None
    
    def analyze_market(self, market: Dict) -> Optional[Dict]:
        """Analyze a single market for opportunities."""
        volume = float(market.get('volume', 0))
        if volume < self.min_volume:
            return None
            
        # Try all patterns
        patterns = [
            self.analyze_extreme_longshots(market),
            self.analyze_high_confidence_continuations(market),
            self.analyze_impossibilities(market),
            self.analyze_binary_events(market),
            self.analyze_time_decay(market),
        ]
        
        # Find best opportunity
        best_opportunity = None
        best_edge = 0
        
        for result in patterns:
            if result and result[1] > best_edge:
                best_opportunity = result
                best_edge = result[1]
        
        if best_opportunity:
            pattern_type, edge, reason = best_opportunity
            price = float(market.get('lastTradePrice', 0.5))
            
            # Determine action
            if pattern_type in ["EXTREME_LONGSHOT", "IMPOSSIBILITY"]:
                action = "BUY NO"
            elif pattern_type in ["CONTINUATION", "TIME_DECAY"] and price < 0.85:
                action = "BUY YES"
            elif pattern_type == "BINARY_50_50":
                action = "BUY NO" if price > 0.5 else "BUY YES"
            elif pattern_type == "TIME_DECAY" and price > 0.15:
                action = "BUY NO"
            else:
                action = "BUY YES" if edge > 0 else "BUY NO"
            
            return {
                'question': market.get('question'),
                'url': f"https://polymarket.com/event/{market.get('groupSlug', '')}",
                'current_price': price,
                'volume': volume,
                'edge': edge,
                'pattern': pattern_type,
                'reason': reason,
                'action': action
            }
        
        return None
    
    def find_all_opportunities(self) -> List[Dict]:
        """Find all opportunities in the market."""
        print("Fetching active markets...")
        markets = self.fetch_active_markets(limit=500)
        print(f"Analyzing {len(markets)} markets...\n")
        
        opportunities = []
        for market in markets:
            opportunity = self.analyze_market(market)
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by edge * volume for best opportunities
        opportunities.sort(key=lambda x: x['edge'] * min(x['volume'], 100000), reverse=True)
        
        return opportunities


def main():
    finder = OpportunityFinder()
    
    try:
        opportunities = finder.find_all_opportunities()
        
        if not opportunities:
            print("No opportunities found with current criteria.")
            return
        
        print(f"=== FOUND {len(opportunities)} OPPORTUNITIES ===\n")
        
        # Group by pattern
        by_pattern = {}
        for opp in opportunities:
            pattern = opp['pattern']
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(opp)
        
        # Display by pattern
        for pattern, opps in by_pattern.items():
            print(f"\n{pattern} ({len(opps)} opportunities):")
            print("-" * 80)
            
            for i, opp in enumerate(opps[:10]):  # Show top 10 per pattern
                print(f"\n{i+1}. {opp['question']}")
                print(f"   Price: {opp['current_price']:.1%} | Volume: ${opp['volume']:,.0f} | Edge: {opp['edge']:.1%}")
                print(f"   Action: {opp['action']} | Reason: {opp['reason']}")
                print(f"   URL: {opp['url']}")
        
        # Summary statistics
        print(f"\n\n=== SUMMARY ===")
        print(f"Total opportunities: {len(opportunities)}")
        print(f"Average edge: {sum(o['edge'] for o in opportunities) / len(opportunities):.1%}")
        print(f"Total volume: ${sum(o['volume'] for o in opportunities):,.0f}")
        
        # Top 5 by edge
        print(f"\n=== TOP 5 BY EDGE ===")
        for i, opp in enumerate(opportunities[:5]):
            print(f"{i+1}. {opp['question'][:60]}... ({opp['edge']:.1%} edge)")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()