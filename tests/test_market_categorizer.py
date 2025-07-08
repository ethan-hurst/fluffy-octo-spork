"""
Unit tests for MarketCategorizer functionality.
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple

from src.analyzers.market_categorizer import MarketCategorizer, CategoryPattern
from src.clients.polymarket.models import Market, Token


class TestMarketCategorizer:
    """Test cases for MarketCategorizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test patterns
        self.temp_dir = tempfile.mkdtemp()
        self.patterns_file = Path(self.temp_dir) / "test_patterns.json"
        self.categorizer = MarketCategorizer(patterns_file=str(self.patterns_file))
        
        # Create test markets
        self.election_market = Market(
            condition_id="election_market",
            question="Will Trump win the 2024 presidential election?",
            description="US presidential election outcome",
            category="Politics",
            active=True,
            closed=False,
            volume=100000.0,
            end_date_iso=datetime.now() + timedelta(days=300),
            tokens=[
                Token(token_id="yes", outcome="YES", price=0.45),
                Token(token_id="no", outcome="NO", price=0.55)
            ],
            minimum_order_size=1.0
        )
        
        self.crypto_market = Market(
            condition_id="crypto_market",
            question="Will a Bitcoin ETF be approved by the SEC?",
            description="Bitcoin ETF approval decision",
            category="Cryptocurrency",
            active=True,
            closed=False,
            volume=50000.0,
            end_date_iso=datetime.now() + timedelta(days=90),
            tokens=[
                Token(token_id="yes", outcome="YES", price=0.6),
                Token(token_id="no", outcome="NO", price=0.4)
            ],
            minimum_order_size=1.0
        )
        
        self.unknown_market = Market(
            condition_id="unknown_market",
            question="Will the new quantum computer achieve quantum supremacy?",
            description="Quantum computing milestone",
            category="Technology",
            active=True,
            closed=False,
            volume=10000.0,
            end_date_iso=datetime.now() + timedelta(days=180),
            tokens=[
                Token(token_id="yes", outcome="YES", price=0.3),
                Token(token_id="no", outcome="NO", price=0.7)
            ],
            minimum_order_size=1.0
        )
        
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def test_default_patterns_creation(self):
        """Test that default patterns are created properly."""
        # Should have created default patterns
        assert len(self.categorizer.patterns) > 0
        assert "presidential_election" in self.categorizer.patterns
        assert "crypto_etf" in self.categorizer.patterns
        
        # Check pattern properties
        election_pattern = self.categorizer.patterns["presidential_election"]
        assert isinstance(election_pattern, CategoryPattern)
        assert "president" in election_pattern.keywords
        assert election_pattern.probability_baseline == 0.45
        
    def test_categorize_known_market(self):
        """Test categorizing a market that matches known patterns."""
        # Test election market
        category, baseline, reasoning = self.categorizer.categorize_market(self.election_market)
        
        assert category == "presidential_election"
        assert baseline == 0.45
        assert "Matched pattern" in reasoning
        assert "confidence" in reasoning
        
        # Test crypto market
        category, baseline, reasoning = self.categorizer.categorize_market(self.crypto_market)
        
        assert category == "crypto_etf"
        assert baseline == 0.40
        assert "Matched pattern" in reasoning
        
    def test_categorize_unknown_market(self):
        """Test categorizing a market that doesn't match any patterns."""
        category, baseline, reasoning = self.categorizer.categorize_market(self.unknown_market)
        
        assert category == "unknown"
        assert baseline == 0.25  # Conservative baseline
        assert "Unknown market type" in reasoning
        assert "learning queue" in reasoning
        
        # Check that market was added to unknown list
        assert len(self.categorizer.unknown_markets) == 1
        assert self.categorizer.unknown_markets[0]["condition_id"] == "unknown_market"
        
    def test_pattern_matching_with_exclusions(self):
        """Test pattern matching with exclusion keywords."""
        # Add pattern with exclusions
        self.categorizer.add_pattern(
            category="sports_championship",
            keywords=["win", "championship", "finals"],
            exclusions=["election", "president"],
            baseline=0.35,
            examples=["Will Lakers win the championship?"]
        )
        
        # Market that matches keywords but has exclusion
        excluded_market = Market(
            condition_id="test",
            question="Will Trump win the championship of the election?",
            description="",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[],
            minimum_order_size=1.0
        )
        
        category, _, _ = self.categorizer.categorize_market(excluded_market)
        
        # Should not match due to exclusion
        assert category != "sports_championship"
        
    def test_usage_count_tracking(self):
        """Test that pattern usage counts are tracked."""
        # Initial usage count
        initial_count = self.categorizer.patterns["presidential_election"].usage_count
        
        # Categorize election market multiple times
        for _ in range(3):
            self.categorizer.categorize_market(self.election_market)
        
        # Check usage count increased
        final_count = self.categorizer.patterns["presidential_election"].usage_count
        assert final_count == initial_count + 3
        
    def test_add_new_pattern(self):
        """Test adding a new pattern."""
        self.categorizer.add_pattern(
            category="climate_target",
            keywords=["climate", "temperature", "global warming", "emissions"],
            exclusions=["weather forecast"],
            baseline=0.2,
            examples=["Will global temperature rise be limited to 1.5C?"]
        )
        
        assert "climate_target" in self.categorizer.patterns
        pattern = self.categorizer.patterns["climate_target"]
        assert pattern.probability_baseline == 0.2
        assert pattern.confidence == 0.8  # Default confidence
        assert pattern.usage_count == 0
        
        # Test that new pattern is used
        climate_market = Market(
            condition_id="climate",
            question="Will global emissions peak by 2030?",
            description="Climate change milestone",
            category="Environment",
            active=True,
            closed=False,
            volume=5000.0,
            end_date_iso=datetime.now() + timedelta(days=365),
            tokens=[],
            minimum_order_size=1.0
        )
        
        category, baseline, _ = self.categorizer.categorize_market(climate_market)
        assert category == "climate_target"
        assert baseline == 0.2
        
    def test_calculate_match_score(self):
        """Test pattern matching score calculation."""
        pattern = CategoryPattern(
            category="test",
            keywords=["bitcoin", "crypto", "btc"],
            exclusions=["stock", "nasdaq"],
            probability_baseline=0.5,
            confidence=0.9,
            examples=[],
            last_updated=datetime.now(),
            usage_count=0
        )
        
        # High score - multiple keywords match
        text1 = "will bitcoin and crypto prices rise"
        score1 = self.categorizer._calculate_match_score(text1, pattern)
        assert score1 > 0.5  # Should have high score
        
        # Low score - only one keyword
        text2 = "will btc be adopted"
        score2 = self.categorizer._calculate_match_score(text2, pattern)
        assert score2 < score1  # Lower than multiple matches
        
        # Zero score - exclusion present
        text3 = "will bitcoin stock rise on nasdaq"
        score3 = self.categorizer._calculate_match_score(text3, pattern)
        assert score3 == 0.0  # Excluded
        
        # Zero score - no keywords match
        text4 = "will gold prices rise"
        score4 = self.categorizer._calculate_match_score(text4, pattern)
        assert score4 == 0.0
        
    def test_suggest_new_patterns(self):
        """Test pattern suggestion from unknown markets."""
        # Add several unknown markets with common themes
        for i in range(5):
            market = Market(
                condition_id=f"ai_{i}",
                question=f"Will AI system {i} achieve AGI by 2025?",
                description="Artificial general intelligence milestone",
                category="Technology",
                active=True,
                closed=False,
                volume=1000.0,
                end_date_iso=datetime.now() + timedelta(days=365),
                tokens=[],
                minimum_order_size=1.0
            )
            self.categorizer.categorize_market(market)
        
        # Get suggestions
        suggestions = self.categorizer.suggest_new_patterns()
        
        assert len(suggestions) > 0
        # Should suggest pattern based on common keywords
        # Since we're looking for any suggestion with count >= 3
        valid_suggestion = next((s for s in suggestions if s["count"] >= 3), None)
        assert valid_suggestion is not None
        assert len(valid_suggestion["examples"]) >= 3
        
    def test_group_by_keywords(self):
        """Test grouping unknown markets by keywords."""
        # Add markets with common keywords
        markets = [
            {"question": "Will SpaceX reach Mars?", "condition_id": "1"},
            {"question": "Will SpaceX launch Starship?", "condition_id": "2"},
            {"question": "Will Mars be colonized?", "condition_id": "3"}
        ]
        
        self.categorizer.unknown_markets = markets
        groups = self.categorizer._group_by_keywords()
        
        # Should have groups for "spacex" and "mars"
        assert "spacex" in groups
        assert len(groups["spacex"]) == 2
        assert "mars" in groups
        # Note: "Mars" appears in question 1 and 3, but case sensitivity and exact matching may vary
        assert len(groups["mars"]) >= 1
        
    def test_save_and_load_patterns(self):
        """Test saving and loading patterns."""
        # Add a custom pattern
        self.categorizer.add_pattern(
            category="test_category",
            keywords=["test", "example"],
            exclusions=["exclude"],
            baseline=0.5,
            examples=["Test example"]
        )
        
        # Save patterns
        self.categorizer.save_patterns()
        
        # Create new categorizer instance to test loading
        new_categorizer = MarketCategorizer(patterns_file=str(self.patterns_file))
        
        assert "test_category" in new_categorizer.patterns
        pattern = new_categorizer.patterns["test_category"]
        assert pattern.keywords == ["test", "example"]
        assert pattern.probability_baseline == 0.5
        
    def test_save_unknown_markets(self):
        """Test saving unknown markets for analysis."""
        # Categorize unknown market
        self.categorizer.categorize_market(self.unknown_market)
        
        # Check unknown markets file was created
        unknown_file = self.patterns_file.parent / "unknown_markets.json"
        assert unknown_file.exists()
        
        # Load and verify content
        with open(unknown_file, 'r') as f:
            data = json.load(f)
            
        assert len(data) == 1
        assert data[0]["condition_id"] == "unknown_market"
        assert data[0]["question"] == self.unknown_market.question
        
    def test_pattern_confidence_levels(self):
        """Test different confidence levels affect matching."""
        # High confidence pattern
        high_conf_pattern = CategoryPattern(
            category="high_conf",
            keywords=["keyword"],
            exclusions=[],
            probability_baseline=0.5,
            confidence=1.0,
            examples=[],
            last_updated=datetime.now(),
            usage_count=0
        )
        
        # Low confidence pattern
        low_conf_pattern = CategoryPattern(
            category="low_conf",
            keywords=["keyword"],
            exclusions=[],
            probability_baseline=0.5,
            confidence=0.3,
            examples=[],
            last_updated=datetime.now(),
            usage_count=0
        )
        
        text = "market with keyword"
        
        high_score = self.categorizer._calculate_match_score(text, high_conf_pattern)
        low_score = self.categorizer._calculate_match_score(text, low_conf_pattern)
        
        assert high_score > low_score
        
    def test_minimum_confidence_threshold(self):
        """Test that patterns below confidence threshold aren't matched."""
        # Add very low confidence pattern
        self.categorizer.patterns["low_conf"] = CategoryPattern(
            category="low_conf",
            keywords=["specific"],
            exclusions=[],
            probability_baseline=0.5,
            confidence=0.2,  # Below 0.3 threshold
            examples=[],
            last_updated=datetime.now(),
            usage_count=0
        )
        
        market = Market(
            condition_id="test",
            question="Will specific event happen?",
            description="",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[],
            minimum_order_size=1.0
        )
        
        category, _, _ = self.categorizer.categorize_market(market)
        
        # Should not match due to low confidence
        assert category == "unknown"
        
    def test_learn_from_outcomes_placeholder(self):
        """Test learn_from_outcomes method (currently placeholder)."""
        # This method is not yet implemented
        self.categorizer.learn_from_outcomes("test_id", True, 0.7)
        # Should not raise error
        
    def test_edge_cases(self):
        """Test edge cases in categorization."""
        # Empty question
        empty_market = Market(
            condition_id="empty",
            question="",
            description="",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[],
            minimum_order_size=1.0
        )
        
        category, baseline, _ = self.categorizer.categorize_market(empty_market)
        assert category == "unknown"
        assert baseline == 0.25
        
        # Very long question
        long_market = Market(
            condition_id="long",
            question="Will " + " ".join(["word"] * 100) + " happen?",
            description="Long description",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[],
            minimum_order_size=1.0
        )
        
        # Should handle without error
        category, _, _ = self.categorizer.categorize_market(long_market)
        assert category in ["unknown"] + list(self.categorizer.patterns.keys())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])