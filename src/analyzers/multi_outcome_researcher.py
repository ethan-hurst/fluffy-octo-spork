"""
Multi-Outcome Market Research Module - Analyzes elections and multi-choice markets
"""

import re
import httpx
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import logging
from dataclasses import dataclass
from typing import Optional as Opt

from src.analyzers.market_researcher import MarketResearcher, SimpleMarket

logger = logging.getLogger(__name__)


@dataclass
class MultiOutcomeMarket:
    """Represents a multi-outcome market with all candidates/options."""
    title: str
    description: str
    options: List[Dict[str, any]]  # Each option has: name, market, price, volume
    total_volume: float
    end_date: Opt[datetime]
    category: str


class MultiOutcomeResearcher(MarketResearcher):
    """Analyzes multi-outcome markets like elections."""
    
    def __init__(self):
        super().__init__()
        
    async def research_multi_outcome(self, url: str) -> Dict:
        """Research a multi-outcome market from URL."""
        # Suppress httpx logging temporarily
        import logging as log
        httpx_logger = log.getLogger("httpx")
        original_level = httpx_logger.level
        httpx_logger.setLevel(log.WARNING)
        
        try:
            # Extract base info from URL
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) < 2 or path_parts[0] != 'event':
                return {'error': 'Invalid Polymarket URL format'}
            
            event_slug = path_parts[1].split('?')[0]
            
            # Show progress
            # Progress is shown by parent caller
            
            # Search for related markets
            related_markets = await self._find_related_markets(event_slug)
        
            if not related_markets:
                logger.debug("No related markets found, treating as single market")
                # Fall back to single market research without multi-outcome check
                return await self._research_single_market(url)
            
            # Analyze as multi-outcome
            logger.debug(f"Processing {len(related_markets)} related markets")
            multi_market = self._create_multi_outcome_market(related_markets)
            analysis = self._analyze_multi_outcome(multi_market)
            
            return {
                'success': True,
                'multi_outcome': True,
                'market': multi_market,
                'analysis': analysis,
                'url': url
            }
        finally:
            # Restore logging
            httpx_logger.setLevel(original_level)
    
    async def _research_single_market(self, url: str) -> Dict:
        """Research a single market without multi-outcome check."""
        # Extract market info
        slug, condition_id = self.extract_market_info(url)
        
        if not slug and not condition_id:
            return {'error': 'Invalid Polymarket URL format'}
        
        # Fetch market
        market = await self.fetch_market_data(slug, condition_id)
        
        if not market:
            return {'error': 'Market not found. Please check the URL or the market may be delisted.'}
        
        # Analyze patterns
        patterns = self.analyze_patterns(market)
        
        # Calculate recommendation
        recommendation = self.calculate_recommendation(market, patterns)
        
        # Create price object for compatibility
        from src.clients.polymarket.models import MarketPrice
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
    
    async def _find_related_markets(self, event_slug: str) -> List[SimpleMarket]:
        """Find all markets related to an event."""
        related_markets = []
        
        async with httpx.AsyncClient() as client:
            # For Argentina election, search specifically for the pattern
            if "chamber-of-deputies" in event_slug and "argentina" in event_slug:
                # Search for all parties in this election
                response = await client.get(
                    f"{self.gamma_api}/markets",
                    params={"search": "chamber deputies argentina", "active": "true", "limit": 100},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    markets = response.json()
                    for market_data in markets:
                        question = market_data.get('question', '')
                        if "win the most seats in the Chamber of Deputies" in question:
                            market = await self._convert_to_simple_market(market_data)
                            if market:
                                related_markets.append(market)
                
                return related_markets
            
            # Generic multi-outcome search (simplified)
            base_terms = self._extract_base_terms(event_slug)
            
            # For NYC mayor, use specific search
            if "new-york" in event_slug and "mayor" in event_slug:
                search_term = "NYC mayor"
            else:
                search_term = base_terms[0] if base_terms else event_slug.replace('-', ' ')
            
            logger.debug(f"Searching for: {search_term}")
            
            # Just do one search with the most relevant term
            response = await client.get(
                f"{self.gamma_api}/markets",
                params={"search": search_term, "active": "true", "limit": 50},
                timeout=30.0
            )
            
            if response.status_code == 200:
                markets = response.json()
                
                # Filter for related markets
                for market_data in markets:
                    question = market_data.get('question', '').lower()
                    slug = market_data.get('slug', '').lower()
                    
                    # Quick check if related
                    if any(term in question for term in base_terms[:3]):
                        market = await self._convert_to_simple_market(market_data)
                        if market:
                            related_markets.append(market)
                            
                        # Stop after finding 10 related markets
                        if len(related_markets) >= 10:
                            break
        
        return related_markets
    
    def _extract_base_terms(self, event_slug: str) -> List[str]:
        """Extract search terms from event slug."""
        # Remove common suffixes
        slug = event_slug.lower()
        slug = re.sub(r'-(election|primary|nominee|race|contest)$', '', slug)
        
        # Extract key terms
        terms = []
        
        # Add full slug
        terms.append(slug.replace('-', ' '))
        
        # Add individual important words
        words = slug.split('-')
        important_words = [w for w in words if len(w) > 3 and w not in ['will', 'the', 'win', 'for']]
        terms.extend(important_words)
        
        # Add common election terms
        if any(term in slug for term in ['mayor', 'president', 'governor', 'senate']):
            terms.extend(['election', 'primary', 'nominee'])
        
        return list(set(terms))
    
    def _is_related_market(self, event_slug: str, market_slug: str, question: str, base_terms: List[str]) -> bool:
        """Check if a market is related to the event."""
        # Check for common terms
        common_terms = 0
        for term in base_terms:
            if term in market_slug or term in question:
                common_terms += 1
        
        # Need at least 2 common terms or specific patterns
        if common_terms >= 2:
            return True
        
        # Check for election patterns
        election_patterns = [
            r'will (\w+) win',
            r'(\w+) (for|as) (mayor|president|governor)',
            r'(democratic|republican) (nominee|primary)',
            r'which (candidate|party) will'
        ]
        
        for pattern in election_patterns:
            if re.search(pattern, question):
                # Check if it contains any base terms
                for term in base_terms:
                    if term in question:
                        return True
        
        return False
    
    def _extract_pattern(self, question: str) -> Optional[str]:
        """Extract pattern from question for finding similar markets."""
        # Common election patterns
        patterns = [
            (r'Will (\w+) win the (.+)\?', 'Will {candidate} win the {election}?'),
            (r'(\w+) for (.+) in (\d+)', '{candidate} for {position} in {year}'),
            (r'Will (\w+) be the (.+) nominee', 'Will {candidate} be the {party} nominee'),
        ]
        
        for regex, template in patterns:
            match = re.search(regex, question, re.IGNORECASE)
            if match:
                return template
        
        return None
    
    def _matches_pattern(self, question: str, pattern: str) -> bool:
        """Check if question matches a pattern template."""
        # Convert pattern to regex
        pattern_regex = pattern.replace('{candidate}', r'(\w+)')
        pattern_regex = pattern_regex.replace('{election}', r'(.+)')
        pattern_regex = pattern_regex.replace('{position}', r'(.+)')
        pattern_regex = pattern_regex.replace('{year}', r'(\d+)')
        pattern_regex = pattern_regex.replace('{party}', r'(\w+)')
        
        return bool(re.search(pattern_regex, question, re.IGNORECASE))
    
    async def _convert_to_simple_market(self, market_data: dict) -> Optional[SimpleMarket]:
        """Convert API data to SimpleMarket."""
        try:
            return SimpleMarket(
                condition_id=market_data.get('conditionId', ''),
                question=market_data.get('question', ''),
                description=market_data.get('description'),
                market_slug=market_data.get('slug', ''),
                category=market_data.get('category'),
                volume=float(market_data.get('volume', 0)),
                liquidity=float(market_data.get('liquidity', 0)),
                last_trade_price=float(market_data.get('lastTradePrice', 0.5)),
                end_date_iso=self._parse_end_date(market_data.get('endDate'))
            )
        except Exception as e:
            logger.error(f"Error converting market data: {e}")
            return None
    
    def _create_multi_outcome_market(self, markets: List[SimpleMarket]) -> MultiOutcomeMarket:
        """Create a multi-outcome market from related markets."""
        # Extract candidate/option names from questions
        options = []
        total_volume = 0
        
        for market in markets:
            # Extract candidate name
            candidate_match = re.search(r'Will (\w+(?:\s+\w+)?)', market.question)
            candidate = candidate_match.group(1) if candidate_match else market.question[:30]
            
            options.append({
                'name': candidate,
                'market': market,
                'price': market.last_trade_price,
                'volume': market.volume,
                'implied_probability': market.last_trade_price
            })
            
            total_volume += market.volume
        
        # Sort by probability
        options.sort(key=lambda x: x['implied_probability'], reverse=True)
        
        # Extract common title
        title = self._extract_common_title(markets)
        
        return MultiOutcomeMarket(
            title=title,
            description=f"Multi-outcome market with {len(options)} options",
            options=options,
            total_volume=total_volume,
            end_date=markets[0].end_date_iso if markets else None,
            category=markets[0].category if markets else "Politics"
        )
    
    def _extract_common_title(self, markets: List[SimpleMarket]) -> str:
        """Extract common title from related markets."""
        if not markets:
            return "Multi-Outcome Market"
        
        # Find common words in all questions
        first_words = set(markets[0].question.lower().split())
        common_words = first_words
        
        for market in markets[1:]:
            market_words = set(market.question.lower().split())
            common_words = common_words.intersection(market_words)
        
        # Try to construct a title
        if 'election' in common_words:
            if 'mayor' in common_words:
                return "Mayoral Election"
            elif 'president' in common_words:
                return "Presidential Election"
            elif 'governor' in common_words:
                return "Gubernatorial Election"
        
        # Fall back to first market question pattern
        return re.sub(r'Will \w+ ', 'Who will ', markets[0].question)
    
    def _analyze_multi_outcome(self, market: MultiOutcomeMarket) -> Dict:
        """Analyze a multi-outcome market for opportunities."""
        analysis = {
            'opportunities': [],
            'market_efficiency': self._calculate_market_efficiency(market),
            'top_candidates': market.options[:3],
            'long_shots': [opt for opt in market.options if opt['implied_probability'] < 0.10],
            'arbitrage': self._check_arbitrage(market)
        }
        
        # Check for mispriced candidates
        for option in market.options:
            opportunity = self._analyze_candidate(option, market)
            if opportunity:
                analysis['opportunities'].append(opportunity)
        
        return analysis
    
    def _calculate_market_efficiency(self, market: MultiOutcomeMarket) -> Dict:
        """Calculate how efficient the market pricing is."""
        # Sum of all probabilities should be close to 100%
        total_probability = sum(opt['implied_probability'] for opt in market.options)
        
        # Avoid division by zero
        if total_probability == 0:
            total_probability = 0.01
        
        return {
            'total_probability': total_probability,
            'efficiency': 1.0 - abs(1.0 - total_probability),
            'is_efficient': 0.95 <= total_probability <= 1.05,
            'arbitrage_possible': total_probability < 0.95 or total_probability > 1.05
        }
    
    def _check_arbitrage(self, market: MultiOutcomeMarket) -> Optional[Dict]:
        """Check for arbitrage opportunities."""
        total_prob = sum(opt['implied_probability'] for opt in market.options)
        
        # Avoid division by zero
        if total_prob == 0:
            return None
            
        if total_prob < 0.95:
            # Can buy all YES positions
            return {
                'type': 'BUY_ALL',
                'total_cost': total_prob,
                'guaranteed_return': 1.0,
                'profit': 1.0 - total_prob,
                'profit_percentage': ((1.0 - total_prob) / total_prob) * 100 if total_prob > 0 else 0
            }
        elif total_prob > 1.05:
            # Can sell all YES positions (buy all NO)
            total_no_cost = sum(1 - opt['implied_probability'] for opt in market.options)
            if total_no_cost > 0:
                return {
                    'type': 'SELL_ALL',
                    'total_cost': total_no_cost,
                    'guaranteed_return': len(market.options) - 1,  # All but one will be NO
                    'profit': (len(market.options) - 1) - total_no_cost,
                    'profit_percentage': (((len(market.options) - 1) - total_no_cost) / total_no_cost) * 100
                }
        
        return None
    
    def _analyze_candidate(self, option: Dict, market: MultiOutcomeMarket) -> Optional[Dict]:
        """Analyze individual candidate for opportunities."""
        prob = option['implied_probability']
        volume = option['volume']
        
        # Skip if too low volume
        if volume < 10000:
            return None
        
        opportunity = None
        
        # Check for specific patterns
        if option['name'].lower() in ['yang', 'adams', 'garcia']:  # Known candidates
            # Historical mayoral election patterns
            if prob < 0.05 and 'yang' in option['name'].lower():
                opportunity = {
                    'candidate': option['name'],
                    'position': 'YES',
                    'reason': 'Tech entrepreneur with name recognition undervalued',
                    'current_price': prob,
                    'target_price': 0.15,
                    'confidence': 0.65
                }
        
        # Long shot value
        if 0.02 <= prob <= 0.08 and volume > 50000:
            opportunity = {
                'candidate': option['name'],
                'position': 'YES',
                'reason': f'Long shot with decent volume (${volume:,.0f})',
                'current_price': prob,
                'target_price': prob * 2,
                'confidence': 0.55
            }
        
        # Overpriced favorite
        if prob > 0.60:
            opportunity = {
                'candidate': option['name'],
                'position': 'NO',
                'reason': 'Overpriced favorite - elections are unpredictable',
                'current_price': prob,
                'target_price': 0.50,
                'confidence': 0.60
            }
        
        return opportunity