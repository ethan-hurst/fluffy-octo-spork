"""
Market Research Module - Analyzes specific Polymarket URLs
"""

import re
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import logging

from src.clients.polymarket.models import MarketPrice
from src.analyzers.models import MarketOpportunity
from dataclasses import dataclass
from typing import Optional as Opt

logger = logging.getLogger(__name__)


@dataclass
class SimpleMarket:
    """Simple market data for research."""
    condition_id: str
    question: str
    description: Opt[str]
    market_slug: str
    category: Opt[str]
    volume: float
    liquidity: float
    last_trade_price: float
    end_date_iso: Opt[datetime]


class MarketResearcher:
    """Analyzes specific Polymarket links for trading opportunities."""
    
    def __init__(self):
        self.gamma_api = "https://gamma-api.polymarket.com"
        
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
    
    async def fetch_market_data(self, slug: str = None, condition_id: str = None) -> Optional[SimpleMarket]:
        """Fetch market data and convert to Market model."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
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
                    for market_data in markets:
                        # More flexible matching
                        market_slug = market_data.get('slug', '')
                        group_slug = market_data.get('groupSlug', '')
                        market_condition_id = market_data.get('conditionId', '')
                        
                        # Check multiple matching criteria
                        slug_match = False
                        if slug:
                            # Exact match
                            if slug == market_slug or slug == group_slug:
                                slug_match = True
                            # Partial match (for shortened URLs)
                            elif slug in market_slug or market_slug in slug:
                                slug_match = True
                            # Try matching just the key part (e.g., "bitcoin-150k" from full slug)
                            elif any(part in market_slug for part in slug.split('-')[:3]):
                                # Check if this is a bitcoin market with the right price
                                if 'bitcoin' in slug and any(price in market_slug for price in ['150k', '150000']):
                                    slug_match = True
                        
                        condition_match = condition_id and condition_id == market_condition_id
                        
                        if slug_match or condition_match:
                            # Convert to SimpleMarket
                            return SimpleMarket(
                                condition_id=market_condition_id,
                                question=market_data.get('question', ''),
                                description=market_data.get('description'),
                                market_slug=market_slug,
                                category=market_data.get('category'),
                                volume=float(market_data.get('volume', 0)),
                                liquidity=float(market_data.get('liquidity', 0)),
                                last_trade_price=float(market_data.get('lastTradePrice', 0.5)),
                                end_date_iso=self._parse_end_date(market_data.get('endDate'))
                            )
                            
        except Exception as e:
            logger.error(f"Error fetching market: {e}")
            
        return None
    
    def _parse_end_date(self, date_str: str) -> Optional[datetime]:
        """Parse end date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    def analyze_patterns(self, market: SimpleMarket) -> List[Dict]:
        """Identify patterns in the market."""
        patterns = []
        question = market.question.lower()
        price = market.last_trade_price or 0.5
        
        # Extreme events
        extreme_keywords = [
            ('record', 0.02), ('all-time', 0.02), ('highest ever', 0.02), 
            ('lowest ever', 0.02), ('unanimous', 0.01), ('perfect', 0.01),
            ('100%', 0.001), ('zero', 0.02), ('nobody', 0.01), 
            ('everyone', 0.01), ('$1 million', 0.01), ('$1 billion', 0.001),
            ('1000x', 0.02), ('world war', 0.001), ('nuclear', 0.01),
            ('alien', 0.001), ('asteroid', 0.001)
        ]
        
        for keyword, typical_prob in extreme_keywords:
            if keyword in question:
                patterns.append({
                    'type': 'EXTREME_EVENT',
                    'keyword': keyword,
                    'typical_probability': typical_prob,
                    'current_price': price
                })
        
        # Continuation patterns
        continuation_keywords = [
            ('remain', 0.85), ('continue', 0.85), ('stay', 0.85),
            ('maintain', 0.85), ('keep', 0.85), ('hold', 0.80),
            ('incumbent', 0.70), ('defend', 0.75), ('retain', 0.85)
        ]
        
        for keyword, typical_prob in continuation_keywords:
            if keyword in question:
                patterns.append({
                    'type': 'CONTINUATION',
                    'keyword': keyword,
                    'typical_probability': typical_prob,
                    'current_price': price
                })
        
        # Dramatic events
        drama_keywords = [
            ('resign', 0.05), ('impeach', 0.03), ('arrest', 0.05),
            ('indict', 0.10), ('convict', 0.05), ('crash', 0.08),
            ('collapse', 0.05), ('war', 0.03), ('invasion', 0.02),
            ('revolution', 0.02), ('coup', 0.02), ('bankrupt', 0.05),
            ('recession', 0.15), ('pandemic', 0.02)
        ]
        
        for keyword, typical_prob in drama_keywords:
            if keyword in question:
                patterns.append({
                    'type': 'DRAMATIC_EVENT',
                    'keyword': keyword,
                    'typical_probability': typical_prob,
                    'current_price': price
                })
        
        # Bitcoin specific
        if 'bitcoin' in question or 'btc' in question:
            if '$200,000' in question or '$200k' in question:
                patterns.append({
                    'type': 'BITCOIN_TARGET',
                    'target': '$200k',
                    'typical_probability': 0.10,
                    'current_price': price
                })
            elif '$150,000' in question or '$150k' in question:
                patterns.append({
                    'type': 'BITCOIN_TARGET',
                    'target': '$150k',
                    'typical_probability': 0.25,
                    'current_price': price
                })
            elif '$120,000' in question or '$120k' in question:
                patterns.append({
                    'type': 'BITCOIN_TARGET',
                    'target': '$120k',
                    'typical_probability': 0.40,
                    'current_price': price
                })
            elif '$100,000' in question or '$100k' in question:
                patterns.append({
                    'type': 'BITCOIN_TARGET',
                    'target': '$100k',
                    'typical_probability': 0.55,
                    'current_price': price
                })
        
        return patterns
    
    def calculate_recommendation(self, market: SimpleMarket, patterns: List[Dict]) -> Dict:
        """Calculate trading recommendation."""
        price = market.last_trade_price or 0.5
        scores = {'YES': 0, 'NO': 0}
        reasons = []
        
        for pattern in patterns:
            typical_prob = pattern['typical_probability']
            diff = abs(price - typical_prob)
            
            if diff > 0.05:  # Significant mispricing
                if pattern['type'] in ['EXTREME_EVENT', 'DRAMATIC_EVENT']:
                    if price > typical_prob:
                        scores['NO'] += diff * 10
                        reasons.append(f"{pattern['keyword']} events rare (~{typical_prob:.0%})")
                
                elif pattern['type'] == 'CONTINUATION':
                    if price < typical_prob:
                        scores['YES'] += diff * 10
                        reasons.append(f"{pattern['keyword']} patterns persist (~{typical_prob:.0%})")
                
                elif pattern['type'] == 'BITCOIN_TARGET':
                    if price > typical_prob + 0.05:
                        scores['NO'] += diff * 8
                        reasons.append(f"BTC {pattern['target']} ambitious (~{typical_prob:.0%} likely)")
                    elif price < typical_prob - 0.05:
                        scores['YES'] += diff * 8
                        reasons.append(f"BTC {pattern['target']} achievable (~{typical_prob:.0%} likely)")
        
        # Time factor
        if market.end_date_iso:
            days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
            if days_left < 7 and 0.20 < price < 0.80:
                scores['NO'] += 0.5
                reasons.append(f"Only {days_left} days left - status quo likely")
        
        # Determine position - lower thresholds for recommendations
        if scores['YES'] > scores['NO'] and scores['YES'] > 0.3:
            position = 'YES'
            confidence = min(0.85, 0.50 + scores['YES'] * 0.05)
            edge = min(0.30, scores['YES'] / 10)
        elif scores['NO'] > scores['YES'] and scores['NO'] > 0.3:
            position = 'NO'
            confidence = min(0.85, 0.50 + scores['NO'] * 0.05)
            edge = min(0.30, scores['NO'] / 10)
        else:
            position = 'NONE'
            confidence = 0.5
            edge = 0
        
        return {
            'position': position,
            'confidence': confidence,
            'edge': edge,
            'reasons': reasons[:3],  # Top 3 reasons
            'score_yes': scores['YES'],
            'score_no': scores['NO']
        }
    
    async def research_market(self, url: str) -> Dict:
        """Main research function."""
        # Extract market info
        slug, condition_id = self.extract_market_info(url)
        
        if not slug and not condition_id:
            return {'error': 'Invalid Polymarket URL format'}
        
        # Fetch market
        market = await self.fetch_market_data(slug, condition_id)
        
        if not market:
            return {'error': 'Market not found. Please check the URL.'}
        
        # Analyze patterns
        patterns = self.analyze_patterns(market)
        
        # Calculate recommendation
        recommendation = self.calculate_recommendation(market, patterns)
        
        # Create price object for compatibility
        price = MarketPrice(
            condition_id=market.condition_id,
            yes_price=market.last_trade_price or 0.5,
            no_price=1.0 - (market.last_trade_price or 0.5),
            spread=0.02
        )
        
        return {
            'success': True,
            'market': market,
            'price': price,
            'patterns': patterns,
            'recommendation': recommendation,
            'url': url
        }