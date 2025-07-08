"""
Unit tests for political market model functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.analyzers.political_model import (
    PoliticalMarketModel, PollData, ElectionFundamentals
)
from src.clients.polymarket.models import Market
from src.clients.news.models import NewsArticle
from src.analyzers.bayesian_updater import ProbabilityDistribution


class TestPoliticalMarketModel:
    """Test cases for PoliticalMarketModel."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.model = PoliticalMarketModel()
        
        # Create test markets
        now = datetime.now()
        self.markets = {
            "trump_election": Market(
                condition_id="trump_2024",
                question="Will Donald Trump win the 2024 presidential election?",
                description="Presidential election prediction market",
                category="Politics",
                active=True,
                closed=False,
                volume=1000000.0,
                end_date_iso=now + timedelta(days=300)
            ),
            "biden_election": Market(
                condition_id="biden_2024",
                question="Will Joe Biden win the 2024 presidential election?",
                description="Presidential election prediction market",
                category="Politics",
                active=True,
                closed=False,
                volume=800000.0,
                end_date_iso=now + timedelta(days=300)
            ),
            "congressional_control": Market(
                condition_id="congress_2024",
                question="Will Republicans control the House after 2024?",
                description="Congressional control prediction",
                category="Politics",
                active=True,
                closed=False,
                volume=500000.0,
                end_date_iso=now + timedelta(days=320)
            )
        }
        
        # Create test poll data
        self.poll_data = [
            PollData(
                candidate="Trump",
                percentage=47.2,
                poll_date=now - timedelta(days=2),
                sample_size=1200,
                pollster="ABC/Washington Post",
                methodology="RV",
                margin_of_error=3.1,
                likely_voters=False
            ),
            PollData(
                candidate="Biden",
                percentage=45.8,
                poll_date=now - timedelta(days=2),
                sample_size=1200,
                pollster="ABC/Washington Post",
                methodology="RV",
                margin_of_error=3.1,
                likely_voters=False
            ),
            PollData(
                candidate="Trump",
                percentage=49.1,
                poll_date=now - timedelta(days=5),
                sample_size=800,
                pollster="CNN",
                methodology="LV",
                margin_of_error=3.5,
                likely_voters=True
            )
        ]
        
        # Create test fundamentals
        self.fundamentals = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="neutral",
            approval_rating=43.2,
            generic_ballot=48.5,
            historical_party_performance=0.48,
            candidate_experience="high"
        )
        
        # Create test news articles
        self.news_articles = [
            NewsArticle(
                title="Trump Leads in Latest Polling",
                description="Former president showing strength in key battleground states",
                url="https://example.com/trump-leads",
                published_at=now - timedelta(hours=2),
                source="Reuters"
            ),
            NewsArticle(
                title="Biden Campaign Raises Record Fundraising",
                description="President's campaign reports strong donor enthusiasm",
                url="https://example.com/biden-fundraising",
                published_at=now - timedelta(hours=1),
                source="AP"
            )
        ]
        
    def test_identify_candidate_trump(self):
        """Test Trump candidate identification."""
        market = self.markets["trump_election"]
        candidate = self.model._identify_candidate(market)
        assert candidate == "Trump"
        
    def test_identify_candidate_biden(self):
        """Test Biden candidate identification."""
        market = self.markets["biden_election"]
        candidate = self.model._identify_candidate(market)
        assert candidate == "Biden"
        
    def test_identify_candidate_generic(self):
        """Test generic candidate identification."""
        market = self.markets["congressional_control"]
        candidate = self.model._identify_candidate(market)
        assert candidate == "Republican"  # Should identify party from question
        
    def test_aggregate_polls_basic(self):
        """Test basic poll aggregation."""
        # Filter polls for Trump
        trump_polls = [p for p in self.poll_data if p.candidate == "Trump"]
        
        aggregated = self.model._aggregate_polls(trump_polls)
        
        assert isinstance(aggregated, dict)
        assert "weighted_average" in aggregated
        assert "confidence" in aggregated
        assert "sample_size" in aggregated
        assert "recency_weight" in aggregated
        
        # Should be between the two Trump poll values
        assert 47.0 < aggregated["weighted_average"] < 50.0
        
    def test_aggregate_polls_empty(self):
        """Test poll aggregation with empty data."""
        aggregated = self.model._aggregate_polls([])
        assert aggregated["weighted_average"] == 0.0
        assert aggregated["confidence"] == 0.0
        
    def test_weight_by_quality_high_quality(self):
        """Test poll quality weighting for high quality polls."""
        poll = self.poll_data[0]  # ABC/Washington Post poll
        weight = self.model._weight_by_quality(poll)
        
        assert weight > 0.5  # Should be high quality
        
    def test_weight_by_quality_low_quality(self):
        """Test poll quality weighting for low quality polls."""
        low_quality_poll = PollData(
            candidate="Trump",
            percentage=50.0,
            poll_date=datetime.now() - timedelta(days=20),
            sample_size=300,
            pollster="Unknown Pollster",
            methodology="IVR",
            margin_of_error=5.0,
            likely_voters=False
        )
        
        weight = self.model._weight_by_quality(low_quality_poll)
        assert weight < 0.5  # Should be lower quality
        
    def test_weight_by_recency_recent(self):
        """Test recency weighting for recent polls."""
        recent_poll = self.poll_data[0]  # 2 days old
        weight = self.model._weight_by_recency(recent_poll)
        
        assert weight > 0.8  # Should be high for recent poll
        
    def test_weight_by_recency_old(self):
        """Test recency weighting for old polls."""
        old_poll = PollData(
            candidate="Trump",
            percentage=50.0,
            poll_date=datetime.now() - timedelta(days=30),
            sample_size=1000,
            pollster="Pollster",
            methodology="RV",
            margin_of_error=3.0,
            likely_voters=True
        )
        
        weight = self.model._weight_by_recency(old_poll)
        assert weight < 0.5  # Should be low for old poll
        
    def test_calculate_fundamentals_score_strong_incumbent(self):
        """Test fundamentals calculation for strong incumbent."""
        strong_incumbent = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="good",
            approval_rating=52.0,
            generic_ballot=51.0,
            historical_party_performance=0.52,
            candidate_experience="high"
        )
        
        score = self.model._calculate_fundamentals_score(strong_incumbent, "Biden")
        assert score > 0.5  # Should favor incumbent
        
    def test_calculate_fundamentals_score_weak_incumbent(self):
        """Test fundamentals calculation for weak incumbent."""
        weak_incumbent = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="poor",
            approval_rating=38.0,
            generic_ballot=45.0,
            historical_party_performance=0.45,
            candidate_experience="medium"
        )
        
        score = self.model._calculate_fundamentals_score(weak_incumbent, "Biden")
        assert score < 0.5  # Should hurt incumbent
        
    def test_calculate_fundamentals_score_challenger(self):
        """Test fundamentals calculation for challenger."""
        score = self.model._calculate_fundamentals_score(self.fundamentals, "Trump")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        
    def test_analyze_political_news_positive(self):
        """Test political news analysis with positive sentiment."""
        positive_news = [
            NewsArticle(
                title="Trump Rallies Energize Base",
                description="Strong turnout and enthusiasm at recent campaign events",
                url="https://example.com/trump-rallies",
                published_at=datetime.now(),
                source="Reuters"
            )
        ]
        
        sentiment = self.model._analyze_political_news(positive_news, "Trump")
        assert sentiment > 0.0  # Should be positive for Trump
        
    def test_analyze_political_news_negative(self):
        """Test political news analysis with negative sentiment."""
        negative_news = [
            NewsArticle(
                title="Trump Faces Legal Challenges",
                description="Former president dealing with multiple court cases",
                url="https://example.com/trump-legal",
                published_at=datetime.now(),
                source="AP"
            )
        ]
        
        sentiment = self.model._analyze_political_news(negative_news, "Trump")
        assert sentiment < 0.0  # Should be negative for Trump
        
    def test_analyze_political_news_no_candidate_mention(self):
        """Test news analysis when candidate not mentioned."""
        generic_news = [
            NewsArticle(
                title="Economic Indicators Mixed",
                description="Latest economic data shows mixed signals",
                url="https://example.com/economy",
                published_at=datetime.now(),
                source="Reuters"
            )
        ]
        
        sentiment = self.model._analyze_political_news(generic_news, "Trump")
        assert sentiment == 0.0  # Should be neutral
        
    def test_get_incumbency_advantage_incumbent(self):
        """Test incumbency advantage calculation."""
        advantage = self.model._get_incumbency_advantage(self.fundamentals, "Biden")
        assert advantage > 0.0  # Should provide advantage
        
    def test_get_incumbency_advantage_challenger(self):
        """Test incumbency advantage for challenger."""
        advantage = self.model._get_incumbency_advantage(self.fundamentals, "Trump")
        assert advantage < 0.0  # Should be disadvantage
        
    def test_get_economic_factor_good_economy(self):
        """Test economic factor with good economy."""
        good_economy = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="good",
            approval_rating=50.0,
            generic_ballot=50.0,
            historical_party_performance=0.5,
            candidate_experience="high"
        )
        
        factor = self.model._get_economic_factor(good_economy, "Biden")
        assert factor > 0.0  # Should help incumbent
        
    def test_get_economic_factor_poor_economy(self):
        """Test economic factor with poor economy."""
        poor_economy = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="poor",
            approval_rating=40.0,
            generic_ballot=45.0,
            historical_party_performance=0.45,
            candidate_experience="medium"
        )
        
        factor = self.model._get_economic_factor(poor_economy, "Biden")
        assert factor < 0.0  # Should hurt incumbent
        
    def test_get_approval_factor_high_approval(self):
        """Test approval factor with high approval."""
        high_approval = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="neutral",
            approval_rating=55.0,
            generic_ballot=52.0,
            historical_party_performance=0.52,
            candidate_experience="high"
        )
        
        factor = self.model._get_approval_factor(high_approval, "Biden")
        assert factor > 0.0  # Should help incumbent
        
    def test_get_approval_factor_low_approval(self):
        """Test approval factor with low approval."""
        low_approval = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="neutral",
            approval_rating=35.0,
            generic_ballot=42.0,
            historical_party_performance=0.42,
            candidate_experience="medium"
        )
        
        factor = self.model._get_approval_factor(low_approval, "Biden")
        assert factor < 0.0  # Should hurt incumbent
        
    def test_get_generic_ballot_factor_favoring_party(self):
        """Test generic ballot factor favoring party."""
        favorable_ballot = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="neutral",
            approval_rating=45.0,
            generic_ballot=52.0,
            historical_party_performance=0.52,
            candidate_experience="high"
        )
        
        factor = self.model._get_generic_ballot_factor(favorable_ballot, "Biden")
        assert factor > 0.0  # Should help Democrats
        
    def test_simulate_polling_error_basic(self):
        """Test polling error simulation."""
        base_prob = 0.5
        poll_quality = 0.8
        
        error = self.model._simulate_polling_error(base_prob, poll_quality)
        assert isinstance(error, float)
        # Error should be relatively small for high quality polls
        assert abs(error) < 0.1
        
    def test_simulate_polling_error_low_quality(self):
        """Test polling error with low quality polls."""
        base_prob = 0.5
        poll_quality = 0.3
        
        error = self.model._simulate_polling_error(base_prob, poll_quality)
        assert isinstance(error, float)
        # Error should be larger for low quality polls
        assert abs(error) < 0.2  # But still reasonable
        
    @patch('src.analyzers.political_model.PoliticalMarketModel._get_polling_data')
    @patch('src.analyzers.political_model.PoliticalMarketModel._get_election_fundamentals')
    def test_calculate_political_probability_with_data(self, mock_fundamentals, mock_polling):
        """Test full political probability calculation with mocked data."""
        # Mock polling data
        mock_polling.return_value = self.poll_data
        
        # Mock fundamentals
        mock_fundamentals.return_value = self.fundamentals
        
        market = self.markets["trump_election"]
        result = self.model.calculate_political_probability(market, self.news_articles)
        
        assert isinstance(result, ProbabilityDistribution)
        assert 0.0 <= result.mean <= 1.0
        assert result.lower_bound <= result.mean <= result.upper_bound
        
    def test_calculate_political_probability_no_data(self):
        """Test political probability calculation with no data."""
        market = self.markets["trump_election"]
        
        with patch.object(self.model, '_get_polling_data', return_value=[]):
            with patch.object(self.model, '_get_election_fundamentals', return_value=None):
                result = self.model.calculate_political_probability(market, [])
                
                assert isinstance(result, ProbabilityDistribution)
                assert 0.0 <= result.mean <= 1.0
                
    def test_get_polling_data_placeholder(self):
        """Test polling data retrieval (placeholder implementation)."""
        polls = self.model._get_polling_data("Trump")
        assert isinstance(polls, list)
        # Should return empty list in current implementation
        
    def test_get_election_fundamentals_placeholder(self):
        """Test election fundamentals retrieval (placeholder implementation)."""
        fundamentals = self.model._get_election_fundamentals("2024")
        # Should return None in current implementation
        assert fundamentals is None
        
    def test_load_polling_databases_placeholder(self):
        """Test polling database loading (placeholder implementation)."""
        databases = self.model._load_polling_databases()
        assert isinstance(databases, dict)
        assert len(databases) == 0  # Empty in current implementation
        
    def test_load_fundamentals_data_placeholder(self):
        """Test fundamentals data loading (placeholder implementation)."""
        data = self.model._load_fundamentals_data()
        assert isinstance(data, dict)
        assert len(data) == 0  # Empty in current implementation
        
    def test_load_historical_patterns_placeholder(self):
        """Test historical patterns loading (placeholder implementation)."""
        patterns = self.model._load_historical_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) == 0  # Empty in current implementation
        
    def test_poll_data_creation(self):
        """Test PollData dataclass creation."""
        poll = PollData(
            candidate="Test Candidate",
            percentage=50.0,
            poll_date=datetime.now(),
            sample_size=1000,
            pollster="Test Pollster"
        )
        
        assert poll.candidate == "Test Candidate"
        assert poll.percentage == 50.0
        assert poll.sample_size == 1000
        assert poll.pollster == "Test Pollster"
        assert poll.methodology == "unknown"  # Default value
        assert poll.margin_of_error == 3.0  # Default value
        assert poll.likely_voters is True  # Default value
        
    def test_election_fundamentals_creation(self):
        """Test ElectionFundamentals dataclass creation."""
        fundamentals = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="good",
            approval_rating=55.0,
            generic_ballot=52.0,
            historical_party_performance=0.52,
            candidate_experience="high"
        )
        
        assert fundamentals.incumbent_running is True
        assert fundamentals.economic_conditions == "good"
        assert fundamentals.approval_rating == 55.0
        assert fundamentals.generic_ballot == 52.0
        assert fundamentals.historical_party_performance == 0.52
        assert fundamentals.candidate_experience == "high"


if __name__ == "__main__":
    pytest.main([__file__])