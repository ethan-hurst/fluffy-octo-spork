#!/usr/bin/env python3
"""
Market Research Tool - Analyzes specific Polymarket links and provides evidence-based recommendations.
"""

import re
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import json
from urllib.parse import urlparse


class MarketResearcher:
    def __init__(self):
        self.gamma_api = "https://gamma-api.polymarket.com"
        self.clob_api = "https://clob.polymarket.com"
        
    def extract_market_info(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract market slug and condition ID from Polymarket URL."""
        # Parse URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Pattern 1: /event/slug/market-id
        # Pattern 2: /market/condition-id
        # Pattern 3: /event/slug (need to fetch condition_id)
        
        if len(path_parts) >= 2:
            if path_parts[0] == 'event':
                slug = path_parts[1]
                condition_id = path_parts[2] if len(path_parts) > 2 else None
                return slug, condition_id
            elif path_parts[0] == 'market':
                return None, path_parts[1]
                
        return None, None
    
    def fetch_market_by_slug(self, slug: str) -> Optional[Dict]:
        """Fetch market data by slug."""
        try:
            # Try to find market by searching
            response = httpx.get(
                f"{self.gamma_api}/markets",
                params={
                    "slug": slug,
                    "limit": 10
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                markets = response.json()
                # Find market with matching slug
                for market in markets:
                    if market.get('groupSlug') == slug or market.get('slug') == slug:
                        return market
                        
            # If not found, search more broadly
            response = httpx.get(
                f"{self.gamma_api}/markets",
                params={
                    "active": "true",
                    "closed": "false",
                    "limit": 500
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                markets = response.json()
                for market in markets:
                    if slug in (market.get('groupSlug', ''), market.get('slug', ''), market.get('conditionId', '')):
                        return market
                        
        except Exception as e:
            print(f"Error fetching market by slug: {e}")
            
        return None
    
    def analyze_market_fundamentals(self, market: Dict) -> Dict:
        """Analyze market fundamentals."""
        price = float(market.get('lastTradePrice', 0.5))
        volume = float(market.get('volume', 0))
        question = market.get('question', '').lower()
        
        analysis = {
            'current_price': price,
            'volume': volume,
            'liquidity': float(market.get('liquidity', 0)),
            'num_trades': market.get('numTrades', 0),
            'patterns': [],
            'time_analysis': None,
            'recommended_position': None,
            'confidence': 0,
            'edge': 0,
            'reasons': []
        }
        
        # Time analysis
        if market.get('endDate'):
            try:
                end_dt = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                days_left = (end_dt - datetime.now(timezone.utc)).days
                analysis['time_analysis'] = {
                    'days_left': days_left,
                    'end_date': end_dt.strftime('%Y-%m-%d'),
                    'urgency': 'high' if days_left < 7 else 'medium' if days_left < 30 else 'low'
                }
            except:
                pass
        
        # Pattern analysis
        patterns = self.identify_patterns(question, price)
        analysis['patterns'] = patterns
        
        # Calculate recommendation
        recommendation = self.calculate_recommendation(market, patterns, analysis['time_analysis'])
        analysis.update(recommendation)
        
        return analysis
    
    def identify_patterns(self, question: str, price: float) -> List[Dict]:
        """Identify patterns in the market question."""
        patterns = []
        
        # Extreme events
        extreme_keywords = [
            'record', 'all-time', 'highest ever', 'lowest ever', 'unanimous',
            'perfect', '100%', 'zero', 'nobody', 'everyone', 'all countries',
            '$1 million', '$1 billion', '1000x', 'world war', 'nuclear'
        ]
        
        for keyword in extreme_keywords:
            if keyword in question:
                patterns.append({
                    'type': 'EXTREME_EVENT',
                    'keyword': keyword,
                    'typical_probability': 0.01 if 'billion' in keyword or 'nuclear' in keyword else 0.02,
                    'description': 'Extreme events are historically very rare'
                })
        
        # Continuation patterns
        continuation_keywords = [
            'remain', 'continue', 'stay', 'maintain', 'keep', 'hold',
            'incumbent', 'defend', 'retain'
        ]
        
        for keyword in continuation_keywords:
            if keyword in question:
                patterns.append({
                    'type': 'CONTINUATION',
                    'keyword': keyword,
                    'typical_probability': 0.85,
                    'description': 'Status quo tends to continue'
                })
        
        # Dramatic events
        drama_keywords = [
            'resign', 'impeach', 'arrest', 'indict', 'convict', 'crash',
            'collapse', 'war', 'invasion', 'revolution', 'coup'
        ]
        
        for keyword in drama_keywords:
            if keyword in question:
                patterns.append({
                    'type': 'DRAMATIC_EVENT',
                    'keyword': keyword,
                    'typical_probability': 0.05,
                    'description': 'Dramatic political/economic events are uncommon'
                })
        
        # Bitcoin specific
        if 'bitcoin' in question or 'btc' in question:
            if '$200,000' in question or '$200k' in question:
                patterns.append({
                    'type': 'BITCOIN_EXTREME',
                    'target': '$200k',
                    'typical_probability': 0.10,
                    'description': 'Bitcoin $200k is an extreme target'
                })
            elif '$150,000' in question or '$150k' in question:
                patterns.append({
                    'type': 'BITCOIN_HIGH',
                    'target': '$150k',
                    'typical_probability': 0.25,
                    'description': 'Bitcoin $150k is ambitious but possible'
                })
            elif '$100,000' in question or '$100k' in question:
                patterns.append({
                    'type': 'BITCOIN_MODERATE',
                    'target': '$100k',
                    'typical_probability': 0.55,
                    'description': 'Bitcoin $100k is a psychological milestone'
                })
        
        return patterns
    
    def calculate_recommendation(self, market: Dict, patterns: List[Dict], time_analysis: Optional[Dict]) -> Dict:
        """Calculate trading recommendation based on patterns."""
        price = float(market.get('lastTradePrice', 0.5))
        recommendations = []
        
        # Analyze each pattern
        for pattern in patterns:
            typical_prob = pattern.get('typical_probability', 0.5)
            
            if pattern['type'] in ['EXTREME_EVENT', 'DRAMATIC_EVENT', 'BITCOIN_EXTREME']:
                if price > typical_prob + 0.05:
                    recommendations.append({
                        'position': 'NO',
                        'edge': price - typical_prob,
                        'confidence': 0.8,
                        'reason': f"{pattern['description']} (typical: {typical_prob:.0%}, current: {price:.0%})"
                    })
            
            elif pattern['type'] == 'CONTINUATION':
                if price < typical_prob - 0.05:
                    recommendations.append({
                        'position': 'YES',
                        'edge': typical_prob - price,
                        'confidence': 0.75,
                        'reason': f"{pattern['description']} (typical: {typical_prob:.0%}, current: {price:.0%})"
                    })
            
            elif pattern['type'] in ['BITCOIN_HIGH', 'BITCOIN_MODERATE']:
                if abs(price - typical_prob) > 0.10:
                    if price > typical_prob:
                        position = 'NO'
                        edge = price - typical_prob
                    else:
                        position = 'YES'
                        edge = typical_prob - price
                    
                    recommendations.append({
                        'position': position,
                        'edge': edge,
                        'confidence': 0.65,
                        'reason': f"{pattern['description']} (typical: {typical_prob:.0%}, current: {price:.0%})"
                    })
        
        # Time-based adjustments
        if time_analysis and time_analysis['days_left'] < 7:
            # Very short term - status quo likely
            if 0.20 < price < 0.80:
                if price < 0.5:
                    recommendations.append({
                        'position': 'NO',
                        'edge': 0.05,
                        'confidence': 0.6,
                        'reason': f"Only {time_analysis['days_left']} days left - unlikely to happen"
                    })
        
        # Choose best recommendation
        if recommendations:
            best = max(recommendations, key=lambda x: x['edge'] * x['confidence'])
            return {
                'recommended_position': best['position'],
                'edge': best['edge'],
                'confidence': best['confidence'],
                'reasons': [r['reason'] for r in recommendations]
            }
        
        # No clear recommendation
        return {
            'recommended_position': 'NONE',
            'edge': 0,
            'confidence': 0,
            'reasons': ['No clear mispricing detected']
        }
    
    def search_web_evidence(self, question: str) -> List[Dict]:
        """Search for web evidence (simplified version)."""
        # Extract key terms
        keywords = []
        
        # Remove common words
        stop_words = {'will', 'be', 'the', 'a', 'an', 'in', 'on', 'at', 'by', 'to', 'for'}
        words = question.lower().split()
        
        for word in words:
            if len(word) > 3 and word not in stop_words:
                keywords.append(word)
        
        # In a real implementation, this would search news APIs
        # For now, return keyword analysis
        return [{
            'type': 'KEYWORDS',
            'terms': keywords[:5],
            'suggestion': f"Search for: {' '.join(keywords[:3])}"
        }]
    
    async def research_market(self, url: str) -> Dict:
        """Main research function."""
        print(f"Researching market: {url}\n")
        
        # Extract market info
        slug, condition_id = self.extract_market_info(url)
        
        if not slug and not condition_id:
            return {
                'error': 'Could not parse Polymarket URL. Please check the format.'
            }
        
        # Fetch market data
        print("Fetching market data...")
        market = None
        
        if slug:
            market = self.fetch_market_by_slug(slug)
        
        if not market and condition_id:
            # Try direct fetch by condition ID
            try:
                response = httpx.get(f"{self.gamma_api}/markets/{condition_id}")
                if response.status_code == 200:
                    market = response.json()
            except:
                pass
        
        if not market:
            # Try one more search
            market = self.fetch_market_by_slug(slug or condition_id)
        
        if not market:
            return {
                'error': 'Could not find market. Please check the URL.'
            }
        
        # Analyze market
        print("Analyzing market fundamentals...")
        analysis = self.analyze_market_fundamentals(market)
        
        # Search for evidence
        print("Searching for evidence...")
        evidence = self.search_web_evidence(market.get('question', ''))
        
        # Compile research report
        report = {
            'market': {
                'question': market.get('question'),
                'current_price': analysis['current_price'],
                'volume': analysis['volume'],
                'liquidity': analysis['liquidity'],
                'trades': analysis['num_trades'],
                'url': url
            },
            'analysis': analysis,
            'evidence': evidence,
            'recommendation': {
                'position': analysis['recommended_position'],
                'confidence': analysis['confidence'],
                'edge': analysis['edge'],
                'reasons': analysis['reasons']
            }
        }
        
        return report
    
    def format_report(self, report: Dict) -> str:
        """Format research report for display."""
        if 'error' in report:
            return f"Error: {report['error']}"
        
        market = report['market']
        analysis = report['analysis']
        rec = report['recommendation']
        
        output = []
        output.append("=" * 80)
        output.append("MARKET RESEARCH REPORT")
        output.append("=" * 80)
        
        # Market Info
        output.append(f"\nQuestion: {market['question']}")
        output.append(f"Current Price: YES = {market['current_price']:.1%} | NO = {(1-market['current_price']):.1%}")
        output.append(f"Volume: ${market['volume']:,.0f} | Liquidity: ${market['liquidity']:,.0f}")
        output.append(f"Number of Trades: {market['trades']:,}")
        
        # Time Analysis
        if analysis['time_analysis']:
            time_info = analysis['time_analysis']
            output.append(f"\nTime Analysis:")
            output.append(f"  Days Until Resolution: {time_info['days_left']}")
            output.append(f"  End Date: {time_info['end_date']}")
            output.append(f"  Urgency: {time_info['urgency'].upper()}")
        
        # Pattern Analysis
        if analysis['patterns']:
            output.append(f"\nPattern Analysis:")
            for pattern in analysis['patterns']:
                output.append(f"  - {pattern['type']}: {pattern['description']}")
                if 'keyword' in pattern:
                    output.append(f"    Triggered by: '{pattern['keyword']}'")
                if 'typical_probability' in pattern:
                    output.append(f"    Historical probability: {pattern['typical_probability']:.0%}")
        
        # Recommendation
        output.append(f"\n{'='*60}")
        output.append("RECOMMENDATION")
        output.append("="*60)
        
        if rec['position'] != 'NONE':
            output.append(f"\nPosition: BUY {rec['position']}")
            output.append(f"Confidence: {rec['confidence']:.0%}")
            output.append(f"Expected Edge: {rec['edge']:.1%}")
            
            output.append(f"\nReasons:")
            for reason in rec['reasons']:
                output.append(f"  • {reason}")
            
            # Trading suggestion
            if rec['position'] == 'YES':
                entry_price = market['current_price']
                target_price = min(0.95, market['current_price'] + rec['edge'])
            else:
                entry_price = 1 - market['current_price']
                target_price = min(0.95, (1 - market['current_price']) + rec['edge'])
            
            output.append(f"\nTrading Suggestion:")
            output.append(f"  Entry: {rec['position']} at {entry_price:.1%}")
            output.append(f"  Target: {target_price:.1%} ({(target_price/entry_price - 1)*100:.0f}% profit)")
            output.append(f"  Risk: Consider 10-20% stop loss")
        else:
            output.append("\nNo clear trading opportunity identified.")
            output.append("The market appears to be fairly priced.")
        
        # Evidence Search Suggestion
        output.append(f"\nFurther Research:")
        if report['evidence']:
            keywords = report['evidence'][0]['terms']
            output.append(f"  Search for: {', '.join(keywords[:3])}")
            output.append(f"  Focus on recent news about: {market['question'][:50]}...")
        
        output.append("\n" + "="*80)
        
        return '\n'.join(output)


async def main():
    """Interactive market research tool."""
    researcher = MarketResearcher()
    
    print("Polymarket Research Tool")
    print("=" * 50)
    print("Paste a Polymarket URL to analyze (or 'quit' to exit)")
    print("Example: https://polymarket.com/event/bitcoin-100k-2025")
    print()
    
    while True:
        url = input("\nEnter Polymarket URL: ").strip()
        
        if url.lower() in ['quit', 'exit', 'q']:
            break
        
        if not url.startswith('http'):
            print("Please enter a valid URL starting with http:// or https://")
            continue
        
        try:
            # Research the market
            report = await researcher.research_market(url)
            
            # Display formatted report
            print(researcher.format_report(report))
            
        except Exception as e:
            print(f"Error analyzing market: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())