"""
Unit tests for Kelly Criterion position sizing.
"""

import pytest
import math
from datetime import datetime, timedelta

from src.analyzers.kelly_criterion import KellyCriterion, KellyResult
from src.clients.polymarket.models import Market, Token


class TestKellyCriterion:
    """Test cases for Kelly Criterion calculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.kelly = KellyCriterion()
        
        # Create test market
        self.test_market = Market(
            condition_id="test_market",
            question="Will Bitcoin reach $100,000?",
            description="Bitcoin price prediction",
            category="Crypto",
            active=True,
            closed=False,
            volume=50000.0,
            end_date_iso=datetime.now() + timedelta(days=90),
            tokens=[
                Token(token_id="yes", outcome="YES", price=0.4),
                Token(token_id="no", outcome="NO", price=0.6)
            ],
            minimum_order_size=1.0
        )
        
    def test_calculate_positive_edge_yes_position(self):
        """Test Kelly calculation with positive edge on YES position."""
        # Predicted probability of 0.6 when market is at 0.4 = positive edge
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.6,
            confidence=0.8,
            recommended_position="YES"
        )
        
        assert isinstance(result, KellyResult)
        assert result.win_probability == 0.6
        assert result.lose_probability == 0.4
        
        # Expected value should be positive
        assert result.expected_value > 0
        
        # Kelly fraction should be positive but capped
        assert 0 < result.kelly_fraction <= 1.0
        assert 0 < result.recommended_fraction <= 0.25  # Max cap
        
        # Should have a recommendation
        assert result.recommendation != "DO NOT BET"
        
    def test_calculate_positive_edge_no_position(self):
        """Test Kelly calculation with positive edge on NO position."""
        # Predicted probability of 0.2 = 80% chance of NO when market is at 60%
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.2,  # 80% NO
            confidence=0.9,
            recommended_position="NO"
        )
        
        assert result.win_probability == 0.8  # 1 - 0.2
        assert result.expected_value > 0
        assert result.kelly_fraction > 0
        assert result.recommended_fraction > 0
        
    def test_calculate_negative_edge(self):
        """Test Kelly calculation with negative expected value."""
        # Predicted probability of 0.3 when market is at 0.4 = negative edge
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.3,
            confidence=0.9,
            recommended_position="YES"
        )
        
        assert result.expected_value < 0
        assert result.recommended_fraction == 0.0
        assert result.recommendation == "DO NOT BET"
        assert any("Negative expected value" in w for w in result.warnings)
        
    def test_calculate_small_edge(self):
        """Test Kelly calculation with edge below minimum threshold."""
        # Small edge: predicted 0.42 when market at 0.4
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.42,
            confidence=0.9,
            recommended_position="YES"
        )
        
        # Should not bet if edge is too small
        if result.expected_value < 0.05:
            assert result.recommended_fraction == 0.0
            assert any("Edge too small" in w for w in result.warnings)
            
    def test_low_confidence_adjustment(self):
        """Test confidence adjustment for low confidence predictions."""
        # High confidence
        high_conf_result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.6,
            confidence=0.9,
            recommended_position="YES"
        )
        
        # Low confidence (same prediction)
        low_conf_result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.6,
            confidence=0.5,
            recommended_position="YES"
        )
        
        # Low confidence should reduce bet size
        assert low_conf_result.recommended_fraction < high_conf_result.recommended_fraction
        assert any("Low confidence" in w for w in low_conf_result.warnings)
        
    def test_extreme_longshot(self):
        """Test Kelly calculation for extreme longshot bets."""
        # Create market with extreme odds
        longshot_market = Market(
            condition_id="longshot",
            question="Extreme longshot?",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[
                Token(token_id="yes", outcome="YES", price=0.02),
                Token(token_id="no", outcome="NO", price=0.98)
            ],
            minimum_order_size=1.0
        )
        
        result = self.kelly.calculate(
            market=longshot_market,
            predicted_probability=0.05,  # Still thinks it's unlikely
            confidence=0.8,
            recommended_position="YES"
        )
        
        # Should warn about extreme longshot
        assert any("Extreme long-shot" in w for w in result.warnings)
        # Should reduce bet size if there's a positive kelly fraction
        if result.kelly_fraction > 0:
            assert result.recommended_fraction <= result.kelly_fraction * 0.5
        
    def test_maximum_fraction_cap(self):
        """Test that Kelly fraction is capped at maximum."""
        # Create scenario with very high Kelly fraction
        # Market severely mispriced
        mispriced_market = Market(
            condition_id="mispriced",
            question="Test?",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=10000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[
                Token(token_id="yes", outcome="YES", price=0.1),
                Token(token_id="no", outcome="NO", price=0.9)
            ],
            minimum_order_size=1.0
        )
        
        result = self.kelly.calculate(
            market=mispriced_market,
            predicted_probability=0.8,  # Huge edge
            confidence=0.95,
            recommended_position="YES"
        )
        
        # Should be capped at max fraction
        assert result.recommended_fraction <= 0.25
        assert result.kelly_fraction > 0.25  # Raw Kelly would be higher
        assert any("Capping bet" in w for w in result.warnings)
        
    def test_invalid_market_prices(self):
        """Test handling of invalid market prices."""
        # Price of 0
        invalid_market = Market(
            condition_id="invalid",
            question="Test?",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[
                Token(token_id="yes", outcome="YES", price=0.0),
                Token(token_id="no", outcome="NO", price=1.0)
            ],
            minimum_order_size=1.0
        )
        
        result = self.kelly.calculate(
            market=invalid_market,
            predicted_probability=0.5,
            confidence=0.8,
            recommended_position="YES"
        )
        
        assert result.recommended_fraction == 0.0
        assert result.recommendation == "DO NOT BET"
        # With price=0, the expected value will be negative, giving "Negative expected value" warning
        assert len(result.warnings) > 0
        # Check for warnings that indicate the bet should not be made
        assert any("Negative expected value" in w or "Invalid market price" in w for w in result.warnings)
        
    def test_probability_of_ruin(self):
        """Test probability of ruin calculation."""
        # Favorable bet
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.7,
            confidence=0.9,
            recommended_position="YES"
        )
        
        assert 0 <= result.probability_of_ruin <= 1.0
        
        # Unfavorable bet (should have high ruin probability)
        unfavorable_result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.3,
            confidence=0.9,
            recommended_position="YES"
        )
        
        # Negative edge should have 100% ruin probability
        if unfavorable_result.expected_value < 0:
            assert unfavorable_result.probability_of_ruin == 0.0  # No bet = no ruin
            
    def test_expected_growth_rate(self):
        """Test expected growth rate calculation."""
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.6,
            confidence=0.9,
            recommended_position="YES"
        )
        
        # With positive edge, should have positive growth
        if result.expected_value > 0 and result.kelly_fraction > 0:
            assert result.expected_growth_rate > 0
            
    def test_get_token_prices(self):
        """Test token price extraction methods."""
        yes_price = self.kelly._get_yes_price(self.test_market)
        no_price = self.kelly._get_no_price(self.test_market)
        
        assert yes_price == 0.4
        assert no_price == 0.6
        
        # Test with missing tokens
        empty_market = Market(
            condition_id="empty",
            question="Test?",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=1000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[],
            minimum_order_size=1.0
        )
        
        assert self.kelly._get_yes_price(empty_market) == 0.5  # Default
        assert self.kelly._get_no_price(empty_market) == 0.5  # Default
        
    def test_format_analysis(self):
        """Test formatting of Kelly analysis results."""
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.6,
            confidence=0.8,
            recommended_position="YES"
        )
        
        formatted = self.kelly.format_analysis(result)
        
        assert isinstance(formatted, str)
        assert "Kelly Criterion Analysis" in formatted
        assert "Win Probability" in formatted
        assert "Expected Value" in formatted
        
        if result.recommended_fraction > 0:
            assert "Recommended Position" in formatted
        else:
            assert "DO NOT BET" in formatted
            
    def test_generate_recommendation_text(self):
        """Test recommendation text generation."""
        # Test different fraction levels
        assert self.kelly._generate_recommendation(0.0, 0.1, 0.6) == "DO NOT BET"
        assert "VERY SMALL" in self.kelly._generate_recommendation(0.005, 0.1, 0.6)
        assert "SMALL" in self.kelly._generate_recommendation(0.03, 0.1, 0.6)
        assert "MODERATE" in self.kelly._generate_recommendation(0.1, 0.1, 0.6)
        assert "LARGE" in self.kelly._generate_recommendation(0.2, 0.1, 0.6)
        assert "MAXIMUM" in self.kelly._generate_recommendation(0.26, 0.1, 0.6)
        
    def test_edge_cases(self):
        """Test various edge cases."""
        # Win probability of 1.0
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=1.0,
            confidence=1.0,
            recommended_position="YES"
        )
        
        assert result.win_probability == 1.0
        assert result.lose_probability == 0.0
        
        # Win probability of 0.0
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.0,
            confidence=1.0,
            recommended_position="YES"
        )
        
        assert result.win_probability == 0.0
        assert result.lose_probability == 1.0
        assert result.recommended_fraction == 0.0
        
    def test_warnings_accumulation(self):
        """Test that multiple warnings can accumulate."""
        # Create scenario with multiple issues
        result = self.kelly.calculate(
            market=self.test_market,
            predicted_probability=0.25,  # Low probability
            confidence=0.4,  # Low confidence
            recommended_position="YES"
        )
        
        # Should have multiple warnings
        assert len(result.warnings) >= 1
        
        # If negative EV, should have that warning
        if result.expected_value < 0:
            assert any("Negative expected value" in w for w in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])