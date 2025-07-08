"""
Dynamic market categorization with learning capabilities.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from src.clients.polymarket.models import Market

logger = logging.getLogger(__name__)


@dataclass
class CategoryPattern:
    """Pattern for categorizing markets."""
    category: str
    keywords: List[str]
    exclusions: List[str]
    probability_baseline: float
    confidence: float
    examples: List[str]
    last_updated: datetime
    usage_count: int = 0


class MarketCategorizer:
    """
    Dynamic market categorizer that learns from unknown market types.
    """
    
    def __init__(self, patterns_file: str = "data/market_patterns.json"):
        """Initialize the categorizer."""
        self.patterns_file = Path(patterns_file)
        self.patterns: Dict[str, CategoryPattern] = {}
        self.unknown_markets: List[Dict] = []
        self.load_patterns()
        
    def categorize_market(self, market: Market) -> Tuple[str, float, str]:
        """
        Categorize a market and return category, baseline probability, and reasoning.
        
        Args:
            market: Market to categorize
            
        Returns:
            Tuple[str, float, str]: (category, baseline_probability, reasoning)
        """
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        # Try to match existing patterns
        best_match = self._find_best_match(full_text)
        
        if best_match:
            category, pattern = best_match
            pattern.usage_count += 1
            self.save_patterns()  # Save updated usage count
            
            return (
                category,
                pattern.probability_baseline,
                f"Matched pattern '{category}' (confidence: {pattern.confidence:.1%}, used {pattern.usage_count} times)"
            )
        
        # Unknown market type - add to learning queue
        self._add_unknown_market(market)
        
        # Use conservative baseline for unknown types
        return (
            "unknown",
            0.25,
            "Unknown market type - using conservative 25% baseline. Added to learning queue."
        )
        
    def _find_best_match(self, text: str) -> Optional[Tuple[str, CategoryPattern]]:
        """Find the best matching pattern for given text."""
        best_score = 0.0
        best_match = None
        
        for category, pattern in self.patterns.items():
            score = self._calculate_match_score(text, pattern)
            if score > best_score and score > 0.3:  # Minimum confidence threshold
                best_score = score
                best_match = (category, pattern)
                
        return best_match
        
    def _calculate_match_score(self, text: str, pattern: CategoryPattern) -> float:
        """Calculate how well text matches a pattern."""
        # Check for exclusions first
        if any(exclusion in text for exclusion in pattern.exclusions):
            return 0.0
            
        # Count keyword matches
        keyword_matches = sum(1 for keyword in pattern.keywords if keyword in text)
        if keyword_matches == 0:
            return 0.0
            
        # Calculate score based on keyword density and pattern confidence
        keyword_density = keyword_matches / len(pattern.keywords)
        return keyword_density * pattern.confidence
        
    def _add_unknown_market(self, market: Market) -> None:
        """Add unknown market to learning queue."""
        unknown_market = {
            "condition_id": market.condition_id,
            "question": market.question,
            "description": market.description,
            "category": market.category,
            "timestamp": datetime.now().isoformat(),
            "end_date": market.end_date_iso.isoformat() if market.end_date_iso else None
        }
        
        self.unknown_markets.append(unknown_market)
        
        # Save unknown markets for analysis
        self._save_unknown_markets()
        
        logger.info(f"Added unknown market to learning queue: {market.question[:50]}...")
        
    def learn_from_outcomes(self, condition_id: str, actual_outcome: bool, market_probability: float) -> None:
        """
        Learn from market outcomes to improve categorization.
        
        Args:
            condition_id: Market condition ID
            actual_outcome: Whether the market resolved to YES
            market_probability: What the market was pricing at resolution
        """
        # Find which pattern was used for this market
        # Update pattern confidence based on how accurate it was
        # This would be implemented with outcome tracking
        pass
        
    def suggest_new_patterns(self) -> List[Dict]:
        """
        Analyze unknown markets and suggest new patterns.
        
        Returns:
            List of suggested new patterns
        """
        if len(self.unknown_markets) < 5:
            return []
            
        # Group unknown markets by common keywords
        keyword_groups = self._group_by_keywords()
        
        suggestions = []
        for keywords, markets in keyword_groups.items():
            if len(markets) >= 3:  # Minimum threshold for new pattern
                suggestion = {
                    "suggested_category": keywords,
                    "keywords": list(keywords.split()),
                    "examples": [m["question"] for m in markets[:3]],
                    "count": len(markets),
                    "suggested_baseline": 0.3  # Conservative default
                }
                suggestions.append(suggestion)
                
        return suggestions
        
    def _group_by_keywords(self) -> Dict[str, List[Dict]]:
        """Group unknown markets by common keywords."""
        keyword_groups = {}
        
        for market in self.unknown_markets:
            # Extract meaningful keywords from question
            question_words = set(market["question"].lower().split())
            
            # Filter out common words
            stop_words = {"will", "the", "a", "an", "be", "to", "of", "in", "on", "at", "by", "for", "with", "is", "was", "are", "were"}
            meaningful_words = question_words - stop_words
            
            # Create keyword combinations
            for word in meaningful_words:
                if len(word) > 3:  # Skip very short words
                    if word not in keyword_groups:
                        keyword_groups[word] = []
                    keyword_groups[word].append(market)
                    
        return keyword_groups
        
    def add_pattern(self, category: str, keywords: List[str], exclusions: List[str], 
                   baseline: float, examples: List[str]) -> None:
        """Add a new pattern to the categorizer."""
        pattern = CategoryPattern(
            category=category,
            keywords=keywords,
            exclusions=exclusions,
            probability_baseline=baseline,
            confidence=0.8,  # Start with medium confidence
            examples=examples,
            last_updated=datetime.now(),
            usage_count=0
        )
        
        self.patterns[category] = pattern
        self.save_patterns()
        logger.info(f"Added new pattern: {category}")
        
    def load_patterns(self) -> None:
        """Load patterns from file."""
        if not self.patterns_file.exists():
            self._create_default_patterns()
            return
            
        try:
            with open(self.patterns_file, 'r') as f:
                data = json.load(f)
                
            for category, pattern_data in data.items():
                pattern_data['last_updated'] = datetime.fromisoformat(pattern_data['last_updated'])
                self.patterns[category] = CategoryPattern(**pattern_data)
                
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            self._create_default_patterns()
            
    def save_patterns(self) -> None:
        """Save patterns to file."""
        self.patterns_file.parent.mkdir(exist_ok=True)
        
        data = {}
        for category, pattern in self.patterns.items():
            pattern_dict = asdict(pattern)
            pattern_dict['last_updated'] = pattern.last_updated.isoformat()
            data[category] = pattern_dict
            
        with open(self.patterns_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _save_unknown_markets(self) -> None:
        """Save unknown markets for analysis."""
        unknown_file = self.patterns_file.parent / "unknown_markets.json"
        
        with open(unknown_file, 'w') as f:
            json.dump(self.unknown_markets, f, indent=2)
            
    def _create_default_patterns(self) -> None:
        """Create default categorization patterns."""
        default_patterns = [
            {
                "category": "constitutional_amendment",
                "keywords": ["constitutional amendment", "22nd amendment", "term limits", "repeal", "supreme court"],
                "exclusions": [],
                "baseline": 0.01,
                "examples": ["Will Trump repeal Presidential term limits?"]
            },
            {
                "category": "presidential_election",
                "keywords": ["president", "election", "win presidency"],
                "exclusions": ["term limits", "amendment"],
                "baseline": 0.45,
                "examples": ["Will Trump win the 2024 election?"]
            },
            {
                "category": "crypto_etf",
                "keywords": ["etf", "approved", "bitcoin", "ethereum", "crypto"],
                "exclusions": [],
                "baseline": 0.40,
                "examples": ["Will a Bitcoin ETF be approved?"]
            },
            {
                "category": "geopolitical_conflict",
                "keywords": ["war", "military action", "troops", "invasion"],
                "exclusions": [],
                "baseline": 0.20,
                "examples": ["Will there be military conflict in Taiwan?"]
            },
            {
                "category": "economic_recession",
                "keywords": ["recession", "economic downturn", "gdp decline", "unemployment"],
                "exclusions": [],
                "baseline": 0.25,
                "examples": ["Will the US enter recession in 2024?"]
            }
        ]
        
        for pattern_data in default_patterns:
            pattern = CategoryPattern(
                category=pattern_data["category"],
                keywords=pattern_data["keywords"],
                exclusions=pattern_data["exclusions"],
                probability_baseline=pattern_data["baseline"],
                confidence=0.8,
                examples=pattern_data["examples"],
                last_updated=datetime.now(),
                usage_count=0
            )
            self.patterns[pattern_data["category"]] = pattern
            
        self.save_patterns()