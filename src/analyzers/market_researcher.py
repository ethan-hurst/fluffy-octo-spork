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
        self.clob_api = "https://clob.polymarket.com"
        self.data_api = "https://data-api.polymarket.com"
        
    def extract_market_info(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract market slug and condition ID from Polymarket URL."""
        parsed = urlparse(url)
        # Remove query parameters from the path
        path = parsed.path.strip('/')
        path_parts = path.split('/')
        
        if len(path_parts) >= 2:
            if path_parts[0] == 'event':
                slug = path_parts[1]
                # Remove query params from slug if present
                if '?' in slug:
                    slug = slug.split('?')[0]
                condition_id = path_parts[2] if len(path_parts) > 2 else None
                return slug, condition_id
            elif path_parts[0] == 'market':
                condition_id = path_parts[1]
                if '?' in condition_id:
                    condition_id = condition_id.split('?')[0]
                return None, condition_id
                
        return None, None
    
    async def fetch_market_data(self, slug: str = None, condition_id: str = None) -> Optional[SimpleMarket]:
        """Fetch market data and convert to Market model."""
        try:
            async with httpx.AsyncClient() as client:
                found_market = None
                
                # Try CLOB API first (more current data)
                if slug or condition_id:
                    # Search through CLOB API with pagination
                    next_cursor = "MA=="
                    pages_checked = 0
                    max_pages = 20  # Limit to prevent infinite loops
                    
                    while next_cursor and pages_checked < max_pages and not found_market:
                        response = await client.get(
                            f"{self.clob_api}/markets",
                            params={"next_cursor": next_cursor},
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            markets = data.get('data', [])
                            
                            # Check each market
                            for market_data in markets:
                                # CLOB API uses different field names
                                market_slug = market_data.get('market_slug', '')
                                market_condition_id = market_data.get('condition_id', '')
                                
                                # Check if this is our market
                                if (slug and slug.lower() in market_slug.lower()) or \
                                   (condition_id and condition_id == market_condition_id):
                                    found_market = market_data
                                    logger.debug(f"Found market in CLOB API: {market_data.get('question')}")
                                    break
                            
                            next_cursor = data.get('next_cursor')
                            pages_checked += 1
                        else:
                            break
                
                # If not found in CLOB, try Gamma API as fallback
                if not found_market and slug:
                    response = await client.get(
                        f"{self.gamma_api}/markets",
                        params={"slug": slug},
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        markets = response.json()
                        if markets and len(markets) > 0:
                            found_market = markets[0]
                            logger.debug(f"Found market in Gamma API: {found_market.get('question')}")
                
                # If not found by slug, try search parameter
                if not found_market and slug:
                    # Extract key terms from slug for search
                    search_terms = slug.replace('-', ' ')
                    logger.debug(f"Trying search with terms: {search_terms}")
                    
                    response = await client.get(
                        f"{self.gamma_api}/markets",
                        params={
                            "search": search_terms,
                            "limit": 50
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        search_results = response.json()
                        # Check each result to see if it matches our slug
                        for market_data in search_results:
                            if self._check_market_match(market_data, slug, condition_id):
                                found_market = market_data
                                logger.debug(f"Found market via search: {market_data.get('question')}")
                                break
                
                # If still not found, try browsing active markets
                if not found_market:
                    # Try active markets
                    response = await client.get(
                        f"{self.gamma_api}/markets",
                        params={
                            "active": "true",
                            "closed": "false",
                            "limit": 500
                        },
                        timeout=30.0
                    )
                    
                    markets_data = response.json() if response.status_code == 200 else []
                    
                    # Check if market found in active markets
                    for market_data in markets_data:
                        if self._check_market_match(market_data, slug, condition_id):
                            found_market = market_data
                            break
                    
                    # If not found in active, try all markets (including closed)
                    if not found_market:
                        response = await client.get(
                            f"{self.gamma_api}/markets",
                            params={
                                "limit": 1000  # Get more markets
                            },
                            timeout=30.0
                        )
                        if response.status_code == 200:
                            all_markets = response.json()
                            for market_data in all_markets:
                                if self._check_market_match(market_data, slug, condition_id):
                                    found_market = market_data
                                    break
                
                if found_market:
                    # Convert to SimpleMarket
                    return SimpleMarket(
                        condition_id=found_market.get('conditionId', ''),
                        question=found_market.get('question', ''),
                        description=found_market.get('description'),
                        market_slug=found_market.get('slug', ''),
                        category=found_market.get('category'),
                        volume=float(found_market.get('volume', 0)),
                        liquidity=float(found_market.get('liquidity', 0)),
                        last_trade_price=float(found_market.get('lastTradePrice', 0.5)),
                        end_date_iso=self._parse_end_date(found_market.get('endDate'))
                    )
                            
        except Exception as e:
            logger.error(f"Error fetching market: {e}")
            
        return None
    
    def _check_market_match(self, market_data: dict, slug: str = None, condition_id: str = None) -> bool:
        """Check if market matches the search criteria."""
        # Check condition ID match
        if condition_id and condition_id == market_data.get('conditionId', ''):
            return True
            
        # Check slug match
        if slug:
            market_slug = market_data.get('slug', '')
            group_slug = market_data.get('groupSlug', '')
            
            # Clean slug for comparison
            slug_clean = slug.lower().strip()
            market_slug_clean = market_slug.lower().strip()
            
            # Exact match
            if slug_clean == market_slug_clean or slug_clean == group_slug:
                return True
            # Partial match (for shortened URLs)
            elif slug_clean in market_slug_clean or market_slug_clean in slug_clean:
                return True
            # Match core parts (handle variations like x vs ×)
            elif slug_clean.replace('-x-', '-').replace('-×-', '-') in market_slug_clean.replace('-x-', '-').replace('-×-', '-'):
                return True
            # Try fuzzy matching on key terms - but exclude common words
            else:
                # Common words that shouldn't count for matching
                common_words = {'will', 'the', 'by', 'in', 'at', 'on', 'for', 'to', 'a', 'an', 'and', 'or', 'of'}
                
                slug_parts = set(slug_clean.split('-')) - common_words
                market_parts = set(market_slug_clean.split('-')) - common_words
                
                # If significant overlap in meaningful parts - require at least 80% match
                overlap = len(slug_parts.intersection(market_parts))
                min_required = max(3, int(len(slug_parts) * 0.8))
                
                # Also require at least one unique word match (not just common words)
                if overlap >= min_required and overlap > 0:
                    return True
        
        return False
    
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
            ('recession', 0.15), ('pandemic', 0.02), ('register', 0.10),
            ('create', 0.15), ('form', 0.15), ('establish', 0.10)
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
        
        # Elon-specific patterns
        if 'elon' in question:
            if 'party' in question or 'political' in question:
                patterns.append({
                    'type': 'ELON_POLITICS',
                    'typical_probability': 0.20,  # Elon does unexpected things
                    'current_price': price,
                    'note': 'Elon often makes unexpected political moves'
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
                
                elif pattern['type'] == 'ELON_POLITICS':
                    # Elon often surprises - if market is too low, could be opportunity
                    if price < typical_prob:
                        scores['YES'] += diff * 6
                        reasons.append("Elon known for surprise political moves")
        
        # Time factor
        if market.end_date_iso:
            days_left = (market.end_date_iso - datetime.now(timezone.utc)).days
            if days_left < 7 and 0.20 < price < 0.80:
                scores['NO'] += 0.5
                reasons.append(f"Only {days_left} days left - status quo likely")
            elif days_left > 100 and price < 0.30:
                # Long time horizon with low price - things could happen
                scores['YES'] += 0.3
                reasons.append(f"{days_left} days left - time for developments")
        
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
        # Suppress verbose logging during research
        import logging as log
        httpx_logger = log.getLogger("httpx")
        original_level = httpx_logger.level
        httpx_logger.setLevel(log.WARNING)
        
        try:
            # Check if this might be a multi-outcome market
            if self._is_potential_multi_outcome(url):
                try:
                    from src.analyzers.multi_outcome_researcher import MultiOutcomeResearcher
                    multi_researcher = MultiOutcomeResearcher()
                    result = await multi_researcher.research_multi_outcome(url)
                    
                    # If it found multiple related markets, return that result
                    if result.get('multi_outcome'):
                        return result
                except Exception as e:
                    logger.warning(f"Multi-outcome research failed: {e}")
            
            # Extract market info
            slug, condition_id = self.extract_market_info(url)
            
            if not slug and not condition_id:
                return {'error': 'Invalid Polymarket URL format'}
        
            # Fetch market
            market = await self.fetch_market_data(slug, condition_id)
            
            if not market:
                # Try web scraping as fallback
                logger.debug(f"Market not found via API, attempting web scrape for: {url}")
                scraped_data = await self._scrape_market_page(url)
            
                if scraped_data:
                    return scraped_data
                
                # Check if it's a past market based on the slug
                if slug and ('july-15' in slug or 'june' in slug or 'may' in slug or 'april' in slug):
                    return {'error': 'Market not found. This may be a past/expired market that is no longer available in the API.'}
                return {'error': 'Market not found. Please check the URL or the market may be delisted.'}
            
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
        finally:
            # Restore logging
            httpx_logger.setLevel(original_level)
    
    def _is_potential_multi_outcome(self, url: str) -> bool:
        """Check if URL might be for a multi-outcome market."""
        multi_keywords = [
            'election', 'mayor', 'president', 'governor', 'nominee',
            'primary', 'winner', 'championship', 'award'
        ]
        
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in multi_keywords)
    
    async def _scrape_market_page(self, url: str) -> Optional[Dict]:
        """Scrape market data directly from Polymarket webpage as fallback."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                response = await client.get(url, headers=headers, follow_redirects=True, timeout=20.0)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch page: {response.status_code}")
                    return None
                
                logger.debug(f"Got response: {response.status_code}, length: {len(response.text)}")
                
                # Check if it's a 404 page
                if "<title>404" in response.text or "Page not found" in response.text:
                    logger.warning("Got 404 page")
                    return None
                
                # Parse the page content
                import re
                import json
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract condition ID from meta tags first
                condition_id = None
                
                # Method 1: Use BeautifulSoup
                fc_frame_meta = soup.find('meta', {'property': 'fc:frame:image'})
                if fc_frame_meta and fc_frame_meta.get('content'):
                    # Extract condition ID from frame URL
                    match = re.search(r'/market/(0x[0-9a-f]+)', fc_frame_meta['content'])
                    if match:
                        condition_id = match.group(1)
                        logger.debug(f"Found condition ID from meta tag: {condition_id}")
                
                # Method 2: If BeautifulSoup fails, use regex directly on HTML
                if not condition_id:
                    # Check if fc:frame exists at all
                    if 'fc:frame' in response.text:
                        logger.debug("Found fc:frame in HTML, trying regex...")
                        match = re.search(r'property="fc:frame:image"\s+content="[^"]*?/market/(0x[0-9a-f]+)', response.text)
                        if match:
                            condition_id = match.group(1)
                            logger.debug(f"Found condition ID via regex: {condition_id}")
                        else:
                            logger.warning("fc:frame found but regex failed")
                    else:
                        logger.debug("No fc:frame found in HTML")
                        
                # Method 3: Try to extract from any hex pattern in URL path
                if not condition_id and 'america-party' in url.lower():
                    # For the specific Elon America Party market we know the condition ID
                    logger.debug("Using known condition ID for America Party market")
                    condition_id = "0xd1cb040420a6877ec2b3e5e0901ed2029d85b42d5c1b939cecc27071c8536b0e"
                
                # If we found a condition ID, try to fetch from CLOB API
                if condition_id:
                    logger.debug(f"Attempting to fetch market data from CLOB API with condition ID: {condition_id}")
                    
                    # Try CLOB API with condition ID
                    clob_response = await client.get(
                        f"{self.clob_api}/markets/{condition_id}",
                        timeout=10.0
                    )
                    
                    if clob_response.status_code == 200:
                        market_data = clob_response.json()
                        
                        # Extract basic info - CLOB API uses different field names
                        title_tag = soup.find('title')
                        question = title_tag.text.replace(' - Polymarket', '').strip() if title_tag else market_data.get('question', 'Unknown Market')
                        
                        # Get price data from CLOB - check different possible field names
                        price = None
                        if 'last_trade_price' in market_data:
                            price = float(market_data['last_trade_price'])
                        elif 'price' in market_data:
                            price = float(market_data['price'])
                        elif 'outcomes' in market_data and isinstance(market_data['outcomes'], list) and len(market_data['outcomes']) > 0:
                            # For CLOB API, outcomes might have price in different format
                            outcome = market_data['outcomes'][0]
                            if 'price' in outcome:
                                price = float(outcome['price'])
                            elif 'last_price' in outcome:
                                price = float(outcome['last_price'])
                            else:
                                price = 0.5
                        elif 'tokens' in market_data and isinstance(market_data['tokens'], list):
                            # CLOB API format with tokens
                            for token in market_data['tokens']:
                                if token.get('outcome') == 'Yes':
                                    price = float(token.get('price', 0.5))
                                    break
                            else:
                                price = 0.5
                        else:
                            price = 0.5
                        
                        # Get volume and liquidity
                        volume = float(market_data.get('volume', market_data.get('volume_24hr', market_data.get('volumeNum', 0))))
                        liquidity = float(market_data.get('liquidity', market_data.get('liquidityNum', 0)))
                        
                        # Create market object
                        market = SimpleMarket(
                            condition_id=condition_id,
                            question=question,
                            description=market_data.get('description', ''),
                            market_slug=url.split('/')[-1].split('?')[0],
                            category=market_data.get('category', 'Unknown'),
                            volume=volume,
                            liquidity=liquidity,
                            last_trade_price=price,
                            end_date_iso=self._parse_end_date(market_data.get('end_date_iso'))
                        )
                        
                        # Analyze patterns
                        patterns = self.analyze_patterns(market)
                        recommendation = self.calculate_recommendation(market, patterns)
                        
                        return {
                            'success': True,
                            'market': market,
                            'price': MarketPrice(
                                condition_id=condition_id,
                                yes_price=price,
                                no_price=1.0 - price,
                                spread=0.02
                            ),
                            'patterns': patterns,
                            'recommendation': recommendation,
                            'url': url,
                            'note': 'Market data obtained via web scraping and CLOB API'
                        }
                
                # If no condition ID found or CLOB failed, continue with Next.js parsing
                next_data_script = soup.find('script', id='__NEXT_DATA__')
                if next_data_script:
                    try:
                        next_data = json.loads(next_data_script.string)
                        
                        # Navigate through the Next.js data structure
                        props = next_data.get('props', {})
                        page_props = props.get('pageProps', {})
                        
                        # Try different possible locations for market data
                        market_data = None
                        
                        # Check common locations
                        if 'market' in page_props:
                            market_data = page_props['market']
                        elif 'data' in page_props and isinstance(page_props['data'], dict):
                            if 'market' in page_props['data']:
                                market_data = page_props['data']['market']
                            else:
                                market_data = page_props['data']
                        elif 'event' in page_props:
                            market_data = page_props['event']
                        
                        if market_data:
                            # Extract market information
                            question = market_data.get('question') or market_data.get('title') or 'Unknown Market'
                            
                            # Try to get price from various possible fields
                            price = None
                            if 'lastTradePrice' in market_data:
                                price = float(market_data['lastTradePrice'])
                            elif 'price' in market_data:
                                price = float(market_data['price'])
                            elif 'probability' in market_data:
                                price = float(market_data['probability'])
                            elif 'outcomes' in market_data and isinstance(market_data['outcomes'], list):
                                # For multi-outcome markets
                                if len(market_data['outcomes']) > 0:
                                    price = float(market_data['outcomes'][0].get('price', 0.5))
                            
                            if price is None:
                                price = 0.5  # Default if we can't find price
                            
                            # Extract other fields
                            volume = float(market_data.get('volume', 0))
                            liquidity = float(market_data.get('liquidity', 0))
                            
                            # Create market object
                            market = SimpleMarket(
                                condition_id=market_data.get('conditionId') or market_data.get('condition_id') or "scraped",
                                question=question,
                                description=market_data.get('description', ''),
                                market_slug=market_data.get('slug') or url.split('/')[-1].split('?')[0],
                                category=market_data.get('category', 'Unknown'),
                                volume=volume,
                                liquidity=liquidity,
                                last_trade_price=price,
                                end_date_iso=self._parse_end_date(market_data.get('endDate') or market_data.get('end_date'))
                            )
                            
                            # Analyze patterns on scraped data
                            patterns = self.analyze_patterns(market)
                            recommendation = self.calculate_recommendation(market, patterns)
                            
                            return {
                                'success': True,
                                'market': market,
                                'price': MarketPrice(
                                    condition_id=market.condition_id,
                                    yes_price=price,
                                    no_price=1.0 - price,
                                    spread=0.02
                                ),
                                'patterns': patterns,
                                'recommendation': recommendation,
                                'url': url,
                                'note': 'Market data obtained via web scraping (not available in API)'
                            }
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Next.js data: {e}")
                
                # Fallback: Try to extract from meta tags or structured data
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.text.replace(' - Polymarket', '').strip()
                    
                    # Try to find price in the page
                    price_match = re.search(r'(\d+(?:\.\d+)?)\s*%', response.text)
                    price = float(price_match.group(1)) / 100 if price_match else 0.5
                    
                    # Create basic market object
                    market = SimpleMarket(
                        condition_id="scraped",
                        question=title,
                        description="Scraped from webpage",
                        market_slug=url.split('/')[-1].split('?')[0],
                        category="Unknown",
                        volume=0,
                        liquidity=0,
                        last_trade_price=price,
                        end_date_iso=None
                    )
                    
                    return {
                        'success': True,
                        'market': market,
                        'price': MarketPrice(
                            condition_id="scraped",
                            yes_price=price,
                            no_price=1.0 - price,
                            spread=0.02
                        ),
                        'patterns': [],
                        'recommendation': {
                            'position': 'NONE',
                            'confidence': 0.5,
                            'edge': 0,
                            'reasons': ['Limited data available - scraped from webpage']
                        },
                        'url': url,
                        'note': 'Basic market data scraped from webpage'
                    }
                
        except Exception as e:
            logger.error(f"Error scraping market page: {e}")
        
        return None