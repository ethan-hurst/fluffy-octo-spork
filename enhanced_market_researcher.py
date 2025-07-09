#!/usr/bin/env python3
"""
Enhanced Market Research Tool with Web Search Integration
"""

import re
import httpx
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import json
from urllib.parse import urlparse, quote
import os
from dotenv import load_dotenv

load_dotenv()


class EnhancedMarketResearcher:
    def __init__(self):
        self.gamma_api = "https://gamma-api.polymarket.com"
        self.news_api_key = os.getenv('NEWS_API_KEY')
        
    def extract_market_info(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract market slug and condition ID from Polymarket URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            if path_parts[0] == 'event':
                slug = path_parts[1]
                condition_id = path_parts[2] if len(path_parts) > 2 else None
                return slug, condition_id
            elif path_parts[0] == 'market':
                return None, path_parts[1]
                
        return None, None
    
    async def fetch_market_data(self, slug: str = None, condition_id: str = None) -> Optional[Dict]:
        """Fetch market data."""
        try:
            # Try different approaches
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
                    # Match by various fields
                    if (slug and (slug in market.get('groupSlug', '') or slug in market.get('slug', ''))) or \
                       (condition_id and condition_id == market.get('conditionId')):
                        return market
                        
        except Exception as e:
            print(f"Error fetching market: {e}")
            
        return None
    
    def extract_search_terms(self, question: str) -> List[str]:
        """Extract key search terms from market question."""
        # Remove common words
        stop_words = {
            'will', 'be', 'the', 'a', 'an', 'in', 'on', 'at', 'by', 'to', 'for',
            'of', 'with', 'is', 'are', 'was', 'were', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'can', 'could', 'should', 'would', 'may', 'might'
        }
        
        # Extract meaningful terms
        words = re.findall(r'\b[a-zA-Z0-9$]+\b', question.lower())
        keywords = []
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)
        
        # Prioritize proper nouns, numbers, and special terms
        priority_terms = []
        for word in question.split():
            if word[0].isupper() or '$' in word or word.isdigit():
                priority_terms.append(word)
        
        return priority_terms[:3] + keywords[:5]
    
    async def search_web_evidence(self, question: str, market: Dict) -> Dict:
        """Search for web evidence about the market."""
        search_terms = self.extract_search_terms(question)
        evidence = {
            'search_terms': search_terms,
            'news': [],
            'insights': [],
            'data_points': []
        }
        
        # If we have NEWS_API_KEY, search for news
        if self.news_api_key:
            try:
                search_query = ' '.join(search_terms[:3])
                response = httpx.get(
                    'https://newsapi.org/v2/everything',
                    params={
                        'q': search_query,
                        'sortBy': 'relevancy',
                        'pageSize': 5,
                        'apiKey': self.news_api_key,
                        'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', [])[:3]:
                        evidence['news'].append({
                            'title': article.get('title'),
                            'source': article.get('source', {}).get('name'),
                            'date': article.get('publishedAt'),
                            'url': article.get('url')
                        })
            except:
                pass
        
        # Analyze for specific data points
        evidence['data_points'] = self.extract_data_points(question, market)
        
        # Generate insights based on patterns
        evidence['insights'] = self.generate_insights(question, market, evidence)
        
        return evidence
    
    def extract_data_points(self, question: str, market: Dict) -> List[Dict]:
        """Extract relevant data points for analysis."""
        data_points = []
        question_lower = question.lower()
        
        # Bitcoin/Crypto analysis
        if 'bitcoin' in question_lower or 'btc' in question_lower:
            # Current BTC price context (example - in real app would fetch live data)
            data_points.append({
                'type': 'MARKET_CONTEXT',
                'data': 'Bitcoin current price: ~$95,000 (as of Jan 2025)',
                'relevance': 'Compare to target price in question'
            })
            
            if any(target in question for target in ['$100,000', '$100k']):
                data_points.append({
                    'type': 'HISTORICAL',
                    'data': 'Bitcoin needs ~5% increase to reach $100k',
                    'relevance': 'Relatively close to target'
                })
            elif any(target in question for target in ['$150,000', '$150k']):
                data_points.append({
                    'type': 'HISTORICAL',
                    'data': 'Bitcoin needs ~58% increase to reach $150k',
                    'relevance': 'Significant rally required'
                })
        
        # Political events
        if 'election' in question_lower:
            data_points.append({
                'type': 'ELECTORAL',
                'data': 'Incumbents historically win ~65-70% of elections',
                'relevance': 'Base rate for electoral predictions'
            })
        
        # Time-based analysis
        if market.get('endDate'):
            try:
                end_dt = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
                days_left = (end_dt - datetime.now(timezone.utc)).days
                
                if days_left < 30:
                    data_points.append({
                        'type': 'TEMPORAL',
                        'data': f'Only {days_left} days until resolution',
                        'relevance': 'Short timeframe reduces probability of major changes'
                    })
            except:
                pass
        
        return data_points
    
    def generate_insights(self, question: str, market: Dict, evidence: Dict) -> List[Dict]:
        """Generate analytical insights."""
        insights = []
        question_lower = question.lower()
        price = float(market.get('lastTradePrice', 0.5))
        
        # Volatility insight
        if market.get('volume', 0) > 100000:
            insights.append({
                'type': 'LIQUIDITY',
                'insight': 'High volume market - prices likely more efficient',
                'implication': 'Smaller edges, but more reliable'
            })
        
        # Pattern-based insights
        if any(word in question_lower for word in ['record', 'highest', 'lowest', 'first']):
            insights.append({
                'type': 'HISTORICAL_PRECEDENT',
                'insight': 'Records and firsts are statistically rare',
                'implication': 'Market may overestimate probability'
            })
        
        if price > 0.9 or price < 0.1:
            insights.append({
                'type': 'EXTREME_PROBABILITY',
                'insight': f'Market pricing at {price:.0%} - near certainty',
                'implication': 'Limited upside, consider risk/reward'
            })
        
        # News-based insights
        if evidence['news']:
            insights.append({
                'type': 'NEWS_SENTIMENT',
                'insight': f"Found {len(evidence['news'])} recent news articles",
                'implication': 'Active news coverage may indicate market efficiency'
            })
        
        return insights
    
    def calculate_recommendation(self, market: Dict, evidence: Dict) -> Dict:
        """Calculate final recommendation with confidence scoring."""
        price = float(market.get('lastTradePrice', 0.5))
        question_lower = market.get('question', '').lower()
        
        scores = {
            'YES': {'points': 0, 'reasons': []},
            'NO': {'points': 0, 'reasons': []}
        }
        
        # Base rate analysis
        if 'record' in question_lower or 'highest ever' in question_lower or 'lowest ever' in question_lower:
            if price > 0.05:
                scores['NO']['points'] += 3
                scores['NO']['reasons'].append('Historical records are rare (<5% typical)')
        
        # Continuation bias
        if any(word in question_lower for word in ['remain', 'continue', 'keep', 'maintain', 'hold']):
            if price < 0.80:
                scores['YES']['points'] += 2
                scores['YES']['reasons'].append('Status quo tends to persist (80%+ typical)')
        
        # Extreme events
        if any(word in question_lower for word in ['crash', 'collapse', 'war', 'nuclear', 'alien']):
            if price > 0.10:
                scores['NO']['points'] += 3
                scores['NO']['reasons'].append('Extreme events very rare (<10% typical)')
        
        # Bitcoin specific
        if 'bitcoin' in question_lower:
            if '$200' in question_lower:
                if price > 0.15:
                    scores['NO']['points'] += 2
                    scores['NO']['reasons'].append('BTC $200k requires 100%+ gain')
            elif '$150' in question_lower:
                if price > 0.30:
                    scores['NO']['points'] += 1
                    scores['NO']['reasons'].append('BTC $150k requires 58% gain')
            elif '$100' in question_lower:
                if price < 0.45:
                    scores['YES']['points'] += 1
                    scores['YES']['reasons'].append('BTC $100k only requires 5% gain')
        
        # Time decay
        for dp in evidence.get('data_points', []):
            if dp['type'] == 'TEMPORAL' and 'Only' in dp['data']:
                days = int(re.search(r'(\d+) days', dp['data']).group(1))
                if days < 14 and 0.2 < price < 0.8:
                    scores['NO']['points'] += 1
                    scores['NO']['reasons'].append(f'Short timeframe ({days} days) favors status quo')
        
        # Determine recommendation
        if scores['YES']['points'] > scores['NO']['points']:
            position = 'YES'
            confidence = min(0.85, 0.5 + scores['YES']['points'] * 0.1)
            reasons = scores['YES']['reasons']
        elif scores['NO']['points'] > scores['YES']['points']:
            position = 'NO'
            confidence = min(0.85, 0.5 + scores['NO']['points'] * 0.1)
            reasons = scores['NO']['reasons']
        else:
            position = 'NONE'
            confidence = 0.5
            reasons = ['No clear edge identified']
        
        # Calculate expected edge
        if position != 'NONE':
            if position == 'YES':
                fair_value = min(0.95, price + (confidence - 0.5) * 0.3)
                edge = fair_value - price
            else:
                fair_value = max(0.05, price - (confidence - 0.5) * 0.3)
                edge = price - fair_value
        else:
            edge = 0
        
        return {
            'position': position,
            'confidence': confidence,
            'edge': edge,
            'reasons': reasons,
            'score_breakdown': scores
        }
    
    async def research_market(self, url: str) -> Dict:
        """Main research function."""
        print(f"\n🔍 Researching: {url}")
        
        # Extract market info
        slug, condition_id = self.extract_market_info(url)
        
        if not slug and not condition_id:
            return {'error': 'Invalid Polymarket URL format'}
        
        # Fetch market data
        print("📊 Fetching market data...")
        market = await self.fetch_market_data(slug, condition_id)
        
        if not market:
            return {'error': 'Market not found. Please check the URL.'}
        
        # Search for evidence
        print("🔎 Searching for evidence...")
        evidence = await self.search_web_evidence(market.get('question', ''), market)
        
        # Calculate recommendation
        print("🧮 Calculating recommendation...")
        recommendation = self.calculate_recommendation(market, evidence)
        
        return {
            'market': market,
            'evidence': evidence,
            'recommendation': recommendation,
            'url': url
        }
    
    def format_report(self, report: Dict) -> str:
        """Format the research report."""
        if 'error' in report:
            return f"\n❌ Error: {report['error']}"
        
        m = report['market']
        e = report['evidence']
        r = report['recommendation']
        
        output = []
        output.append("\n" + "="*80)
        output.append("📈 POLYMARKET RESEARCH REPORT")
        output.append("="*80)
        
        # Market Overview
        output.append(f"\n📌 Market: {m.get('question')}")
        output.append(f"💰 Volume: ${m.get('volume', 0):,.0f}")
        output.append(f"📊 Current Prices: YES={m.get('lastTradePrice', 0):.1%} | NO={(1-m.get('lastTradePrice', 0)):.1%}")
        
        # Evidence Summary
        if e['data_points']:
            output.append("\n📋 Key Data Points:")
            for dp in e['data_points']:
                output.append(f"  • {dp['data']}")
                output.append(f"    → {dp['relevance']}")
        
        if e['insights']:
            output.append("\n💡 Market Insights:")
            for insight in e['insights']:
                output.append(f"  • {insight['insight']}")
                output.append(f"    → {insight['implication']}")
        
        if e['news']:
            output.append("\n📰 Recent News:")
            for article in e['news'][:3]:
                output.append(f"  • {article['title']}")
                output.append(f"    Source: {article['source']}")
        
        # Recommendation
        output.append("\n" + "="*60)
        output.append("🎯 RECOMMENDATION")
        output.append("="*60)
        
        if r['position'] != 'NONE':
            output.append(f"\n✅ Position: BUY {r['position']}")
            output.append(f"📊 Confidence: {r['confidence']:.0%}")
            output.append(f"💹 Expected Edge: {r['edge']:.1%}")
            
            output.append("\n📝 Analysis:")
            for reason in r['reasons']:
                output.append(f"  • {reason}")
            
            # Score breakdown
            output.append("\n🏆 Score Breakdown:")
            for position, data in r['score_breakdown'].items():
                if data['points'] > 0:
                    output.append(f"  {position}: {data['points']} points")
            
            # Entry suggestion
            if r['position'] == 'YES':
                entry = m.get('lastTradePrice', 0.5)
            else:
                entry = 1 - m.get('lastTradePrice', 0.5)
            
            output.append(f"\n💸 Trading Suggestion:")
            output.append(f"  Entry: {r['position']} at {entry:.1%}")
            output.append(f"  Target: {(entry + r['edge']):.1%}")
            output.append(f"  Potential Return: {(r['edge']/entry*100):.0f}%")
        else:
            output.append("\n⚖️ No Clear Edge")
            output.append("The market appears fairly priced at current levels.")
        
        # Research suggestions
        if e['search_terms']:
            output.append(f"\n🔍 For deeper research, search:")
            output.append(f"  '{' '.join(e['search_terms'][:3])}'")
        
        output.append("\n" + "="*80 + "\n")
        
        return '\n'.join(output)


async def main():
    """Run the enhanced market researcher."""
    researcher = EnhancedMarketResearcher()
    
    print("🎯 Enhanced Polymarket Research Tool")
    print("="*50)
    print("Enter a Polymarket URL to get detailed analysis")
    print("Example: https://polymarket.com/event/will-bitcoin-reach-150k-2025")
    print("\nType 'quit' to exit\n")
    
    while True:
        url = input("🔗 Enter URL: ").strip()
        
        if url.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not url.startswith('http'):
            print("❌ Please enter a valid URL")
            continue
        
        try:
            report = await researcher.research_market(url)
            print(researcher.format_report(report))
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Also support direct URL as command line argument
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        researcher = EnhancedMarketResearcher()
        report = asyncio.run(researcher.research_market(url))
        print(researcher.format_report(report))
    else:
        asyncio.run(main())