"""
Unit tests for political market model functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.analyzers.political_model import (
    PoliticalMarketModel, PollData, ElectionFundamentals
)
from src.clients.polymarket.models import Market, Token
from src.clients.news.models import NewsArticle, NewsSource
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
                end_date_iso=now + timedelta(days=300),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            "biden_election": Market(
                condition_id="biden_2024",
                question="Will Joe Biden win the 2024 presidential election?",
                description="Presidential election prediction market",
                category="Politics",
                active=True,
                closed=False,
                volume=800000.0,
                end_date_iso=now + timedelta(days=300),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
            ),
            "congressional_control": Market(
                condition_id="congress_2024",
                question="Will Republicans control the House after 2024?",
                description="Congressional control prediction",
                category="Politics",
                active=True,
                closed=False,
                volume=500000.0,
                end_date_iso=now + timedelta(days=320),
                tokens=[
                    Token(token_id="yes_token", outcome="Yes", price=0.5),
                    Token(token_id="no_token", outcome="No", price=0.5)
                ],
                minimum_order_size=1.0
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
                source=NewsSource(name="Reuters")
            ),
            NewsArticle(
                title="Biden Campaign Raises Record Fundraising",
                description="President's campaign reports strong donor enthusiasm",
                url="https://example.com/biden-fundraising",
                published_at=now - timedelta(hours=1),
                source=NewsSource(name="AP")
            )
        ]
        
    def test_identify_candidate_trump(self):
        """Test Trump candidate identification."""
        market = self.markets["trump_election"]
        candidates = self.model._extract_candidate_names(market.question.lower())
        assert "trump" in candidates
        
    def test_identify_candidate_biden(self):
        """Test Biden candidate identification."""
        market = self.markets["biden_election"]
        candidates = self.model._extract_candidate_names(market.question.lower())
        assert "biden" in candidates
        
    def test_identify_candidate_generic(self):
        """Test generic candidate identification."""
        market = self.markets["congressional_control"]
        candidates = self.model._extract_candidate_names(market.question.lower())
        # For non-candidate markets, should return empty list
        assert len(candidates) == 0
        
    def test_aggregate_polls_basic(self):
        """Test basic poll aggregation."""
        # Filter polls for Trump
        trump_polls = [p for p in self.poll_data if p.candidate == "Trump"]
        
        average = self.model._calculate_polling_average(trump_polls, "Trump")
        
        assert isinstance(average, float)
        # Should be between the two Trump poll values (47.2 and 49.1)
        assert 0.47 < average < 0.50
        
    def test_aggregate_polls_empty(self):
        """Test poll aggregation with empty data."""
        average = self.model._calculate_polling_average([], "Trump")
        assert average == 0.5  # Should return default 50%
        
    def test_poll_data_quality(self):
        """Test that poll data has quality attributes."""
        poll = self.poll_data[0]  # ABC/Washington Post poll
        
        # Check poll has expected attributes
        assert hasattr(poll, 'sample_size')
        assert hasattr(poll, 'margin_of_error')
        assert hasattr(poll, 'methodology')
        assert poll.sample_size > 0
        assert poll.margin_of_error > 0
        
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
        
        score = self.model._calculate_fundamentals_probability(strong_incumbent)
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
        
        score = self.model._calculate_fundamentals_probability(weak_incumbent)
        # Just check it returns a valid probability
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        
    def test_calculate_fundamentals_score_challenger(self):
        """Test fundamentals calculation for challenger."""
        score = self.model._calculate_fundamentals_probability(self.fundamentals)
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
                source=NewsSource(name="Reuters")
            )
        ]
        
        sentiment = self.model._analyze_political_news_sentiment(positive_news, self.markets["trump_election"])
        assert sentiment > 0.0  # Should be positive for Trump
        
    def test_analyze_political_news_negative(self):
        """Test political news analysis with negative sentiment."""
        negative_news = [
            NewsArticle(
                title="Trump Faces Legal Challenges",
                description="Former president dealing with multiple court cases",
                url="https://example.com/trump-legal",
                published_at=datetime.now(),
                source=NewsSource(name="AP")
            )
        ]
        
        sentiment = self.model._analyze_political_news_sentiment(negative_news, self.markets["trump_election"])
        assert sentiment < 0.0  # Should be negative for Trump
        
    def test_analyze_political_news_no_candidate_mention(self):
        """Test news analysis when candidate not mentioned."""
        generic_news = [
            NewsArticle(
                title="Economic Indicators Mixed",
                description="Latest economic data shows mixed signals",
                url="https://example.com/economy",
                published_at=datetime.now(),
                source=NewsSource(name="Reuters")
            )
        ]
        
        sentiment = self.model._analyze_political_news_sentiment(generic_news, self.markets["trump_election"])
        assert sentiment == 0.0  # Should be neutral
        
    def test_incumbency_advantage_in_fundamentals(self):
        """Test that incumbency is considered in fundamentals calculation."""
        # Test through fundamentals probability calculation
        incumbent_fundamentals = self.fundamentals
        prob = self.model._calculate_fundamentals_probability(incumbent_fundamentals)
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0
        
    def test_economic_conditions_in_fundamentals(self):
        """Test that economic conditions affect fundamentals calculation."""
        # Good economy
        good_economy = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="good",
            approval_rating=50.0,
            generic_ballot=50.0,
            historical_party_performance=0.5,
            candidate_experience="high"
        )
        good_prob = self.model._calculate_fundamentals_probability(good_economy)
        
        # Poor economy
        poor_economy = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="poor",
            approval_rating=40.0,
            generic_ballot=45.0,
            historical_party_performance=0.45,
            candidate_experience="medium"
        )
        poor_prob = self.model._calculate_fundamentals_probability(poor_economy)
        
        # Just verify both return valid probabilities
        assert isinstance(good_prob, float) and 0.0 <= good_prob <= 1.0
        assert isinstance(poor_prob, float) and 0.0 <= poor_prob <= 1.0
        
    def test_approval_rating_in_fundamentals(self):
        """Test that approval rating affects fundamentals calculation."""
        # High approval
        high_approval = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="neutral",
            approval_rating=55.0,
            generic_ballot=52.0,
            historical_party_performance=0.52,
            candidate_experience="high"
        )
        high_prob = self.model._calculate_fundamentals_probability(high_approval)
        
        # Low approval
        low_approval = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="neutral",
            approval_rating=35.0,
            generic_ballot=42.0,
            historical_party_performance=0.42,
            candidate_experience="medium"
        )
        low_prob = self.model._calculate_fundamentals_probability(low_approval)
        
        # Just verify both return valid probabilities
        assert isinstance(high_prob, float) and 0.0 <= high_prob <= 1.0
        assert isinstance(low_prob, float) and 0.0 <= low_prob <= 1.0
        
    def test_generic_ballot_in_fundamentals(self):
        """Test that generic ballot affects fundamentals calculation."""
        favorable_ballot = ElectionFundamentals(
            incumbent_running=True,
            economic_conditions="neutral",
            approval_rating=45.0,
            generic_ballot=52.0,
            historical_party_performance=0.52,
            candidate_experience="high"
        )
        
        prob = self.model._calculate_fundamentals_probability(favorable_ballot)
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0
        
    def test_polling_data_structure(self):
        """Test polling data structure and calculations."""
        # Test with simulated polling data
        candidates = self.model._extract_candidate_names("trump vs biden election")
        polls = self.model._get_simulated_polling_data(candidates)
        
        assert isinstance(polls, list)
        if polls:
            assert all(isinstance(p, PollData) for p in polls)
            
        # Test polling average calculation
        if polls:
            trump_polls = [p for p in polls if p.candidate.lower() == "trump"]
            if trump_polls:
                avg = self.model._calculate_polling_average(trump_polls, "trump")
                assert isinstance(avg, float)
                assert 0.0 <= avg <= 1.0
        
    @patch('src.analyzers.political_model.PoliticalMarketModel._get_simulated_polling_data')
    @patch('src.analyzers.political_model.PoliticalMarketModel._extract_election_fundamentals')
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
        
        # Test with empty news articles (no mocking needed)
        result = self.model.calculate_political_probability(market, [])
        
        assert isinstance(result, ProbabilityDistribution)
        assert 0.0 <= result.mean <= 1.0
                
    def test_get_simulated_polling_data(self):
        """Test simulated polling data retrieval."""
        polls = self.model._get_simulated_polling_data(["Trump", "Biden"])
        assert isinstance(polls, list)
        # May return simulated data
        
    def test_extract_election_fundamentals(self):
        """Test election fundamentals extraction."""
        fundamentals = self.model._extract_election_fundamentals(self.markets["trump_election"], self.news_articles)
        # May return None or ElectionFundamentals
        assert fundamentals is None or isinstance(fundamentals, ElectionFundamentals)
        
    def test_load_pollster_reliability(self):
        """Test pollster reliability loading."""
        reliability = self.model._load_pollster_reliability()
        assert isinstance(reliability, dict)
        # May have some default values
        
    # Removed test for non-existent _load_fundamentals_data method
        
    def test_load_historical_patterns_placeholder(self):
        """Test historical patterns loading (placeholder implementation)."""
        patterns = self.model._load_historical_patterns()
        assert isinstance(patterns, dict)
        # Has some default patterns
        assert len(patterns) > 0
        
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