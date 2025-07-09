#!/usr/bin/env python3
"""
Direct API opportunity finder with comprehensive patterns.
"""

import httpx
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

class DirectOpportunityFinder:
    def __init__(self):
        self.api_url = "https://gamma-api.polymarket.com"
        self.min_volume = 500  # Lower to $500
        self.min_edge = 0.03  # 3% minimum edge
        
    def fetch_markets(self) -> List[Dict]:
        """Fetch all active markets directly from API."""
        try:
            response = httpx.get(
                f"{self.api_url}/markets",
                params={
                    "active": "true",
                    "closed": "false",
                    "limit": 500  # Get many markets
                },
                timeout=30.0
            )
            response.raise_for_status()
            markets = response.json()
            
            # Filter for good volume
            filtered = [m for m in markets if float(m.get('volume', 0)) >= self.min_volume]
            
            # Sort by volume
            filtered.sort(key=lambda m: float(m.get('volume', 0)), reverse=True)
            
            return filtered
            
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []
    
    def analyze_market(self, market: Dict) -> List[Dict]:
        """Analyze a single market for multiple opportunity types."""
        price = float(market.get('lastTradePrice', 0.5))
        volume = float(market.get('volume', 0))
        question = market.get('question', '').lower()
        
        if volume < self.min_volume:
            return []
            
        opportunities = []
        
        # Pattern 1: Extreme Longshots (5-20% that should be <5%)
        if 0.05 < price < 0.20:
            patterns = [
                ('$1 million', 0.01, "Extreme price targets"),
                ('$1 billion', 0.001, "Impossible price targets"),
                ('1000x', 0.02, "Extreme multipliers"),
                ('break all-time high', 0.03, "Record breaking events"),
                ('world record', 0.02, "World records are rare"),
                ('unanimous', 0.01, "Unanimous decisions are extremely rare"),
                ('perfect season', 0.01, "Perfect seasons almost never happen"),
                ('100%', 0.001, "100% outcomes are nearly impossible"),
                ('hottest year', 0.02, "Climate records are rare"),
                ('coldest year', 0.02, "Climate records are rare"),
                ('highest ever', 0.02, "All-time highs are rare"),
                ('lowest ever', 0.02, "All-time lows are rare"),
                ('win every', 0.01, "Winning everything is extremely rare"),
                ('zero', 0.02, "Zero outcomes are rare"),
                ('everyone', 0.01, "Universal agreement is nearly impossible"),
                ('all countries', 0.01, "Global unanimity is nearly impossible"),
                ('bankrupt', 0.03, "Bankruptcy is relatively rare"),
                ('default', 0.04, "Defaults are uncommon"),
            ]
            
            for pattern, fair_value, reason in patterns:
                if pattern in question:
                    edge = price - fair_value
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'EXTREME_LONGSHOT',
                            'edge': edge,
                            'action': 'BUY NO',
                            'reason': f"{reason} (~{fair_value:.0%} prob)",
                            'confidence': 0.8
                        })
                        
        # Pattern 2: Overpriced Moderate Events (10-30%)
        elif 0.10 < price < 0.30:
            patterns = [
                ('impeach', 0.05, "Impeachments are rare"),
                ('resign', 0.05, "Resignations are uncommon"),
                ('fired', 0.08, "High-level firings are uncommon"),
                ('war', 0.03, "Wars are rare events"),
                ('invasion', 0.02, "Invasions are extremely rare"),
                ('nuclear', 0.01, "Nuclear events are nearly impossible"),
                ('revolution', 0.02, "Revolutions are extremely rare"),
                ('coup', 0.02, "Coups are very rare"),
                ('assassin', 0.001, "Assassinations are extremely rare"),
                ('terrorist', 0.05, "Major attacks are uncommon"),
                ('pandemic', 0.02, "Pandemics are rare"),
                ('crash', 0.08, "Market crashes are uncommon"),
                ('recession', 0.15, "Recessions happen but not frequently"),
                ('collapse', 0.05, "Collapses are rare"),
                ('crisis', 0.10, "Crises are uncommon"),
            ]
            
            for pattern, fair_value, reason in patterns:
                if pattern in question:
                    edge = price - fair_value
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'OVERPRICED_MODERATE',
                            'edge': edge,
                            'action': 'BUY NO',
                            'reason': f"{reason} (~{fair_value:.0%} prob)",
                            'confidence': 0.7
                        })
                        
        # Pattern 3: Underpriced Continuations (70-90%)
        elif 0.70 < price < 0.90:
            patterns = [
                ('remain', 0.92, "Status quo usually continues"),
                ('continue', 0.90, "Trends tend to continue"),
                ('stay', 0.91, "Things tend to stay the same"),
                ('maintain', 0.90, "Maintenance of status is common"),
                ('keep', 0.90, "Keeping positions is common"),
                ('hold', 0.88, "Holdings tend to persist"),
                ('incumbent', 0.85, "Incumbents have advantages"),
                ('defend', 0.85, "Defenders usually succeed"),
                ('retain', 0.90, "Retention is common"),
            ]
            
            for pattern, fair_value, reason in patterns:
                if pattern in question:
                    edge = fair_value - price
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'UNDERPRICED_CONTINUATION',
                            'edge': edge,
                            'action': 'BUY YES',
                            'reason': f"{reason} (~{fair_value:.0%} prob)",
                            'confidence': 0.75
                        })
                        
        # Pattern 4: Binary Mispricings
        if abs(price - 0.5) > 0.15:
            binary_patterns = [
                'coin flip', 'coin toss', 'heads or tails',
                'odd or even', 'red or black', 'random',
                '50/50', 'fifty-fifty'
            ]
            
            for pattern in binary_patterns:
                if pattern in question:
                    if price > 0.5:
                        edge = price - 0.52
                        action = 'BUY NO'
                    else:
                        edge = 0.48 - price
                        action = 'BUY YES'
                        
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'BINARY_MISPRICING',
                            'edge': edge,
                            'action': action,
                            'reason': f"True 50/50 event at {price:.0%}",
                            'confidence': 0.9
                        })
                        
        # Pattern 5: Near Impossibilities
        if price > 0.05:
            impossible_patterns = [
                ('alien', 0.001, "Alien confirmation nearly impossible"),
                ('world war', 0.001, "World wars are extremely rare"),
                ('extinction', 0.001, "Extinction events are nearly impossible"),
                ('asteroid', 0.001, "Asteroid impacts are extremely rare"),
                ('merge countries', 0.001, "Country mergers don't happen"),
                ('abolish', 0.005, "Abolishing institutions is very rare"),
                ('dissolve', 0.01, "Dissolving entities is rare"),
                ('constitutional amendment', 0.01, "Amendments are very rare"),
            ]
            
            for pattern, fair_value, reason in impossible_patterns:
                if pattern in question:
                    edge = price - fair_value
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'NEAR_IMPOSSIBILITY',
                            'edge': edge,
                            'action': 'BUY NO',
                            'reason': f"{reason} (~{fair_value:.1%} prob)",
                            'confidence': 0.9
                        })
                        
        # Pattern 6: Time-sensitive opportunities
        end_date = market.get('endDate')
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                days_left = (end_dt - datetime.now(timezone.utc)).days
                
                # Very short term unlikely events
                if 0 < days_left < 7 and 0.15 < price < 0.40:
                    unlikely_patterns = [
                        'announce', 'release', 'launch', 'resign',
                        'step down', 'deal', 'agreement', 'merger'
                    ]
                    
                    for pattern in unlikely_patterns:
                        if pattern in question:
                            edge = price - 0.08
                            if edge >= self.min_edge:
                                opportunities.append({
                                    'pattern': 'SHORT_TERM_UNLIKELY',
                                    'edge': edge,
                                    'action': 'BUY NO',
                                    'reason': f"Unlikely in {days_left} days",
                                    'confidence': 0.7
                                })
                                
            except:
                pass
                
        # Pattern 7: Bitcoin/Crypto specific
        if 'bitcoin' in question or 'btc' in question:
            # Bitcoin price targets
            if '$200,000' in question or '$200k' in question:
                if price > 0.15:
                    edge = price - 0.10
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'BITCOIN_EXTREME',
                            'edge': edge,
                            'action': 'BUY NO',
                            'reason': "BTC $200k is extreme target (~10% prob)",
                            'confidence': 0.7
                        })
            elif '$150,000' in question or '$150k' in question:
                if price > 0.35:
                    edge = price - 0.25
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'BITCOIN_HIGH',
                            'edge': edge,
                            'action': 'BUY NO',
                            'reason': "BTC $150k is ambitious (~25% prob)",
                            'confidence': 0.65
                        })
            elif '$120,000' in question or '$120k' in question:
                if price > 0.65:
                    edge = price - 0.50
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'BITCOIN_MODERATE',
                            'edge': edge,
                            'action': 'BUY NO',
                            'reason': "BTC $120k is possible but not likely (~50% prob)",
                            'confidence': 0.6
                        })
            elif '$100,000' in question or '$100k' in question:
                if price < 0.40:
                    edge = 0.55 - price
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'BITCOIN_LIKELY',
                            'edge': edge,
                            'action': 'BUY YES',
                            'reason': "BTC $100k is reasonably likely (~55% prob)",
                            'confidence': 0.65
                        })
            
            # Bitcoin crash scenarios
            if '$50,000' in question or '$50k' in question or 'below $50' in question:
                if price > 0.25:
                    edge = price - 0.15
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'BITCOIN_CRASH',
                            'edge': edge,
                            'action': 'BUY NO',
                            'reason': "Major BTC crash unlikely (~15% prob)",
                            'confidence': 0.7
                        })
                        
        # Pattern 8: Political events
        if 'trump' in question:
            if 'arrest' in question or 'indict' in question or 'convict' in question:
                if price > 0.30:
                    edge = price - 0.20
                    if edge >= self.min_edge:
                        opportunities.append({
                            'pattern': 'POLITICAL_DRAMA',
                            'edge': edge,
                            'action': 'BUY NO',
                            'reason': "Political arrests/convictions are uncommon (~20% prob)",
                            'confidence': 0.6
                        })
                        
        return opportunities
    
    def find_all_opportunities(self) -> List[Dict]:
        """Find all opportunities across markets."""
        print("Fetching markets from Polymarket...")
        markets = self.fetch_markets()
        print(f"Analyzing {len(markets)} markets...\n")
        
        all_opportunities = []
        pattern_counts = {}
        
        for market in markets:
            opportunities = self.analyze_market(market)
            
            for opp in opportunities:
                all_opportunities.append({
                    'market': market,
                    'opportunity': opp
                })
                
                # Count patterns
                pattern = opp['pattern']
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Sort by edge * volume
        all_opportunities.sort(
            key=lambda x: x['opportunity']['edge'] * min(float(x['market'].get('volume', 0)), 100000),
            reverse=True
        )
        
        return all_opportunities, pattern_counts


def main():
    finder = DirectOpportunityFinder()
    
    try:
        opportunities, pattern_counts = finder.find_all_opportunities()
        
        if not opportunities:
            print("No opportunities found with current criteria.")
            return
            
        print(f"=== FOUND {len(opportunities)} OPPORTUNITIES ===\n")
        
        # Pattern distribution
        print("Pattern Distribution:")
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pattern}: {count} opportunities")
        
        # Group by pattern
        by_pattern = {}
        for opp_data in opportunities:
            pattern = opp_data['opportunity']['pattern']
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(opp_data)
        
        # Show top opportunities by pattern
        print("\n=== TOP OPPORTUNITIES BY PATTERN ===")
        
        for pattern, opps in sorted(by_pattern.items()):
            print(f"\n{pattern} ({len(opps)} total):")
            print("-" * 80)
            
            for i, opp_data in enumerate(opps[:3]):
                market = opp_data['market']
                opp = opp_data['opportunity']
                
                print(f"\n{i+1}. {market.get('question')}")
                print(f"   Price: {float(market.get('lastTradePrice', 0)):.1%} | Volume: ${float(market.get('volume', 0)):,.0f}")
                print(f"   Edge: {opp['edge']:.1%} | Confidence: {opp['confidence']:.0%}")
                print(f"   Action: {opp['action']} | {opp['reason']}")
                print(f"   URL: https://polymarket.com/event/{market.get('groupSlug', '')}")
        
        # Top 10 overall
        print("\n\n=== TOP 10 OPPORTUNITIES BY EDGE * VOLUME ===")
        print("-" * 80)
        
        for i, opp_data in enumerate(opportunities[:10]):
            market = opp_data['market']
            opp = opp_data['opportunity']
            
            print(f"\n{i+1}. {market.get('question')}")
            print(f"   Pattern: {opp['pattern']} | Edge: {opp['edge']:.1%}")
            print(f"   Price: {float(market.get('lastTradePrice', 0)):.0%} | Volume: ${float(market.get('volume', 0)):,.0f}")
            print(f"   Action: {opp['action']} | {opp['reason']}")
            
        # Quick picks
        print("\n\n=== QUICK PICKS (HIGH CONFIDENCE + HIGH VOLUME) ===")
        quick_picks = [
            o for o in opportunities
            if o['opportunity']['confidence'] >= 0.75
            and float(o['market'].get('volume', 0)) > 50000
            and o['opportunity']['edge'] >= 0.05
        ]
        
        for i, pick in enumerate(quick_picks[:5]):
            market = pick['market']
            opp = pick['opportunity']
            print(f"\n{i+1}. {market.get('question')[:70]}...")
            print(f"   {opp['action']} at {float(market.get('lastTradePrice', 0)):.0%} (Edge: {opp['edge']:.0%}, Volume: ${float(market.get('volume', 0)):,.0f})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()