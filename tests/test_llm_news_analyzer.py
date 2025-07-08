"""
Unit tests for LLM-powered news analysis functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from src.analyzers.llm_news_analyzer import (
    LLMNewsAnalyzer, MarketNewsAnalysis, NewsAnalysisResult
)
from src.clients.polymarket.models import Market
from src.clients.news.models import NewsArticle


class TestLLMNewsAnalyzer:
    """Test cases for LLMNewsAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = LLMNewsAnalyzer()
        
        # Create test market
        now = datetime.now()
        self.market = Market(
            condition_id="test_market_1",
            question="Will Donald Trump win the 2024 presidential election?",
            description="Presidential election prediction market",
            category="Politics",
            active=True,
            closed=False,
            volume=1000000.0,
            end_date_iso=now + timedelta(days=300)
        )
        
        # Create test news articles
        self.news_articles = [
            NewsArticle(
                title="Trump Leads in Latest Polling Data",
                description="Former president shows strong support in key battleground states according to new poll",
                url="https://example.com/trump-polling",
                published_at=now - timedelta(hours=2),
                source="Reuters"
            ),
            NewsArticle(
                title="Biden Campaign Raises Record Fundraising",
                description="President's reelection campaign reports unprecedented donor enthusiasm and financial support",
                url="https://example.com/biden-fundraising",
                published_at=now - timedelta(hours=1),
                source="Associated Press"
            ),
            NewsArticle(
                title="Election Security Measures Enhanced",
                description="States implement new voting technology and verification systems for upcoming election",
                url="https://example.com/election-security",
                published_at=now - timedelta(hours=3),
                source="Washington Post"
            ),
            NewsArticle(
                title="Partisan Blog Claims Election Fraud",
                description="Unverified claims about voting irregularities spread on social media",
                url="https://example.com/partisan-blog",
                published_at=now - timedelta(hours=4),
                source="Unknown Blog"
            )
        ]
        
    def test_news_analysis_creation(self):
        """Test NewsAnalysis dataclass creation."""
        analysis = NewsAnalysis(
            overall_sentiment=0.3,
            sentiment_confidence=0.8,
            news_impact_score=0.65,
            credible_sources_count=3,
            total_sources_count=5,
            probability_adjustment=0.05,
            key_insights=["Strong polling data", "High fundraising activity"],
            confidence_factors=["Multiple credible sources", "Recent data"],
            uncertainty_factors=["Conflicting narratives", "Early in cycle"]
        )
        
        assert analysis.overall_sentiment == 0.3
        assert analysis.sentiment_confidence == 0.8
        assert analysis.news_impact_score == 0.65
        assert analysis.credible_sources_count == 3
        assert analysis.total_sources_count == 5
        assert analysis.probability_adjustment == 0.05
        assert len(analysis.key_insights) == 2
        assert len(analysis.confidence_factors) == 2
        assert len(analysis.uncertainty_factors) == 2
        
    def test_source_credibility_creation(self):
        """Test SourceCredibility dataclass creation."""
        credibility = SourceCredibility(
            source_name="Reuters",
            credibility_score=0.9,
            bias_score=0.1,
            reliability_rating="high",
            fact_check_history=0.95,
            editorial_standards="excellent"
        )
        
        assert credibility.source_name == "Reuters"
        assert credibility.credibility_score == 0.9
        assert credibility.bias_score == 0.1
        assert credibility.reliability_rating == "high"
        assert credibility.fact_check_history == 0.95
        assert credibility.editorial_standards == "excellent"
        
    @pytest.mark.asyncio
    @patch('src.analyzers.llm_news_analyzer.LLMNewsAnalyzer._call_claude_api')
    async def test_analyze_market_news_success(self, mock_api_call):
        """Test successful market news analysis."""
        # Mock Claude API response
        mock_api_call.return_value = {
            "sentiment_score": 0.25,
            "confidence": 0.8,
            "impact_score": 0.7,
            "probability_adjustment": 0.04,
            "key_insights": [
                "Polling data shows Trump with slight advantage",
                "Biden campaign demonstrates strong organizational capacity"
            ],
            "confidence_factors": [
                "Multiple credible news sources",
                "Recent polling data"
            ],
            "uncertainty_factors": [
                "Early in election cycle",
                "Polling margins within error bounds"
            ]
        }
        
        result = await self.analyzer.analyze_market_news(self.market, self.news_articles)
        
        assert isinstance(result, NewsAnalysis)
        assert result.overall_sentiment == 0.25
        assert result.sentiment_confidence == 0.8
        assert result.news_impact_score == 0.7
        assert result.probability_adjustment == 0.04
        assert result.credible_sources_count == 3  # Reuters, AP, WashPost
        assert result.total_sources_count == 4
        assert len(result.key_insights) == 2
        
        # Verify API was called
        mock_api_call.assert_called_once()
        
    @pytest.mark.asyncio
    @patch('src.analyzers.llm_news_analyzer.LLMNewsAnalyzer._call_claude_api')
    async def test_analyze_market_news_api_failure(self, mock_api_call):
        """Test market news analysis when API fails."""
        # Mock API failure
        mock_api_call.side_effect = Exception("API Error")
        
        result = await self.analyzer.analyze_market_news(self.market, self.news_articles)
        
        # Should return fallback analysis
        assert isinstance(result, NewsAnalysis)
        assert result.overall_sentiment == 0.0  # Neutral fallback
        assert result.sentiment_confidence < 0.5  # Low confidence
        assert result.probability_adjustment == 0.0  # No adjustment
        assert "fallback analysis" in result.key_insights[0].lower()
        
    @pytest.mark.asyncio
    async def test_analyze_market_news_no_articles(self):
        """Test market news analysis with no articles."""
        result = await self.analyzer.analyze_market_news(self.market, [])
        
        assert isinstance(result, NewsAnalysis)
        assert result.overall_sentiment == 0.0
        assert result.sentiment_confidence == 0.0
        assert result.news_impact_score == 0.0
        assert result.credible_sources_count == 0
        assert result.total_sources_count == 0
        assert result.probability_adjustment == 0.0
        
    def test_assess_source_credibility_high_credibility(self):
        """Test source credibility assessment for high-credibility sources."""
        reuters_cred = self.analyzer._assess_source_credibility("Reuters")
        
        assert reuters_cred.credibility_score > 0.8
        assert reuters_cred.reliability_rating == "high"
        assert reuters_cred.bias_score < 0.3
        
    def test_assess_source_credibility_medium_credibility(self):
        """Test source credibility assessment for medium-credibility sources."""
        medium_cred = self.analyzer._assess_source_credibility("Local News Channel")
        
        assert 0.4 < medium_cred.credibility_score < 0.8
        assert medium_cred.reliability_rating == "medium"
        
    def test_assess_source_credibility_low_credibility(self):
        """Test source credibility assessment for low-credibility sources."""
        low_cred = self.analyzer._assess_source_credibility("Unknown Blog")
        
        assert low_cred.credibility_score < 0.5
        assert low_cred.reliability_rating == "low"
        assert low_cred.bias_score > 0.5
        
    def test_assess_source_credibility_known_biased(self):
        """Test source credibility assessment for known biased sources."""
        biased_cred = self.analyzer._assess_source_credibility("Partisan News Network")
        
        assert biased_cred.bias_score > 0.6
        assert biased_cred.credibility_score < 0.6
        
    def test_count_credible_sources(self):
        """Test counting credible sources from article list."""
        credible_count = self.analyzer._count_credible_sources(self.news_articles)
        
        # Reuters, Associated Press, Washington Post should be credible
        # Unknown Blog should not be
        assert credible_count == 3
        
    def test_count_credible_sources_empty(self):
        """Test counting credible sources with empty list."""
        credible_count = self.analyzer._count_credible_sources([])
        assert credible_count == 0
        
    def test_prepare_analysis_prompt(self):
        """Test analysis prompt preparation."""
        prompt = self.analyzer._prepare_analysis_prompt(self.market, self.news_articles)
        
        assert isinstance(prompt, str)
        assert self.market.question in prompt
        assert "Trump" in prompt  # From market question
        assert "Reuters" in prompt  # From news sources
        assert "sentiment" in prompt.lower()
        assert "probability" in prompt.lower()
        
    def test_prepare_analysis_prompt_no_articles(self):
        """Test analysis prompt preparation with no articles."""
        prompt = self.analyzer._prepare_analysis_prompt(self.market, [])
        
        assert isinstance(prompt, str)
        assert self.market.question in prompt
        assert "no recent news" in prompt.lower()
        
    @patch('src.analyzers.llm_news_analyzer.LLMNewsAnalyzer._call_claude_api')
    def test_call_claude_api_mock(self, mock_api):
        """Test Claude API call mocking."""
        mock_response = {
            "sentiment_score": 0.5,
            "confidence": 0.7,
            "impact_score": 0.6
        }
        mock_api.return_value = mock_response
        
        result = self.analyzer._call_claude_api("test prompt")
        assert result == mock_response
        mock_api.assert_called_once_with("test prompt")
        
    def test_parse_claude_response_valid(self):
        """Test parsing valid Claude API response."""
        response_text = '''
        {
            "sentiment_score": 0.3,
            "confidence": 0.8,
            "impact_score": 0.7,
            "probability_adjustment": 0.05,
            "key_insights": ["Insight 1", "Insight 2"],
            "confidence_factors": ["Factor 1"],
            "uncertainty_factors": ["Uncertainty 1"]
        }
        '''
        
        result = self.analyzer._parse_claude_response(response_text)
        
        assert result["sentiment_score"] == 0.3
        assert result["confidence"] == 0.8
        assert result["impact_score"] == 0.7
        assert result["probability_adjustment"] == 0.05
        assert len(result["key_insights"]) == 2
        
    def test_parse_claude_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        invalid_response = "This is not valid JSON"
        
        result = self.analyzer._parse_claude_response(invalid_response)
        
        # Should return default values
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.3
        assert result["impact_score"] == 0.0
        
    def test_parse_claude_response_missing_fields(self):
        """Test parsing response with missing fields."""
        incomplete_response = '''
        {
            "sentiment_score": 0.4,
            "confidence": 0.6
        }
        '''
        
        result = self.analyzer._parse_claude_response(incomplete_response)
        
        assert result["sentiment_score"] == 0.4
        assert result["confidence"] == 0.6
        assert result["impact_score"] == 0.0  # Default value
        assert result["probability_adjustment"] == 0.0  # Default value
        
    def test_create_fallback_analysis(self):
        """Test fallback analysis creation."""
        fallback = self.analyzer._create_fallback_analysis(self.news_articles)
        
        assert isinstance(fallback, NewsAnalysis)
        assert fallback.overall_sentiment == 0.0
        assert fallback.sentiment_confidence < 0.5
        assert fallback.probability_adjustment == 0.0
        assert fallback.credible_sources_count == 3  # Still counts credible sources
        assert "fallback" in fallback.key_insights[0].lower()
        
    def test_create_fallback_analysis_no_articles(self):
        """Test fallback analysis with no articles."""
        fallback = self.analyzer._create_fallback_analysis([])
        
        assert isinstance(fallback, NewsAnalysis)
        assert fallback.credible_sources_count == 0
        assert fallback.total_sources_count == 0
        
    def test_validate_analysis_response_valid(self):
        """Test validation of valid analysis response."""
        valid_response = {
            "sentiment_score": 0.3,
            "confidence": 0.8,
            "impact_score": 0.7,
            "probability_adjustment": 0.05,
            "key_insights": ["Insight 1"],
            "confidence_factors": ["Factor 1"],
            "uncertainty_factors": ["Uncertainty 1"]
        }
        
        is_valid = self.analyzer._validate_analysis_response(valid_response)
        assert is_valid is True
        
    def test_validate_analysis_response_invalid_ranges(self):
        """Test validation with values outside valid ranges."""
        invalid_response = {
            "sentiment_score": 1.5,  # Outside [-1, 1] range
            "confidence": -0.2,      # Outside [0, 1] range
            "impact_score": 2.0,     # Outside [0, 1] range
            "probability_adjustment": 0.5,  # Outside [-0.2, 0.2] range
            "key_insights": ["Insight 1"],
            "confidence_factors": ["Factor 1"],
            "uncertainty_factors": ["Uncertainty 1"]
        }
        
        is_valid = self.analyzer._validate_analysis_response(invalid_response)
        assert is_valid is False
        
    def test_validate_analysis_response_missing_required(self):
        """Test validation with missing required fields."""
        incomplete_response = {
            "sentiment_score": 0.3,
            # Missing other required fields
        }
        
        is_valid = self.analyzer._validate_analysis_response(incomplete_response)
        assert is_valid is False
        
    def test_get_source_bias_score_neutral(self):
        """Test bias score for neutral sources."""
        bias_score = self.analyzer._get_source_bias_score("Reuters")
        assert bias_score < 0.3  # Should be low bias
        
    def test_get_source_bias_score_biased(self):
        """Test bias score for known biased sources."""
        bias_score = self.analyzer._get_source_bias_score("Highly Partisan Network")
        assert bias_score > 0.5  # Should be high bias
        
    def test_get_source_reliability_rating_high(self):
        """Test reliability rating for high-quality sources."""
        rating = self.analyzer._get_source_reliability_rating("Associated Press")
        assert rating == "high"
        
    def test_get_source_reliability_rating_low(self):
        """Test reliability rating for low-quality sources."""
        rating = self.analyzer._get_source_reliability_rating("Random Blog")
        assert rating == "low"
        
    def test_calculate_news_impact_score_high_credibility(self):
        """Test news impact calculation with high credibility sources."""
        impact = self.analyzer._calculate_news_impact_score(
            credible_count=3,
            total_count=4,
            recency_hours=2.0
        )
        
        assert impact > 0.5  # Should be significant impact
        
    def test_calculate_news_impact_score_low_credibility(self):
        """Test news impact calculation with low credibility sources."""
        impact = self.analyzer._calculate_news_impact_score(
            credible_count=1,
            total_count=5,
            recency_hours=48.0  # Old news
        )
        
        assert impact < 0.5  # Should be lower impact
        
    def test_calculate_news_impact_score_no_sources(self):
        """Test news impact calculation with no sources."""
        impact = self.analyzer._calculate_news_impact_score(
            credible_count=0,
            total_count=0,
            recency_hours=0.0
        )
        
        assert impact == 0.0
        
    def test_extract_key_topics(self):
        """Test key topic extraction from articles."""
        topics = self.analyzer._extract_key_topics(self.news_articles)
        
        assert isinstance(topics, list)
        assert len(topics) > 0
        # Should extract relevant keywords from article titles/descriptions
        
    def test_extract_key_topics_empty(self):
        """Test key topic extraction with no articles."""
        topics = self.analyzer._extract_key_topics([])
        assert topics == []
        
    def test_calculate_recency_weight_recent(self):
        """Test recency weight calculation for recent articles."""
        recent_time = datetime.now() - timedelta(hours=1)
        weight = self.analyzer._calculate_recency_weight(recent_time)
        
        assert weight > 0.8  # Should be high weight for recent news
        
    def test_calculate_recency_weight_old(self):
        """Test recency weight calculation for old articles."""
        old_time = datetime.now() - timedelta(days=7)
        weight = self.analyzer._calculate_recency_weight(old_time)
        
        assert weight < 0.3  # Should be low weight for old news
        
    def test_source_credibility_databases_initialization(self):
        """Test that source credibility databases are properly initialized."""
        # Test high credibility sources
        assert "reuters" in self.analyzer.high_credibility_sources
        assert "associated press" in self.analyzer.high_credibility_sources
        assert "bbc" in self.analyzer.high_credibility_sources
        
        # Test medium credibility sources
        assert len(self.analyzer.medium_credibility_sources) > 0
        
        # Test low credibility sources
        assert len(self.analyzer.low_credibility_sources) > 0
        
        # Test biased sources
        assert len(self.analyzer.biased_sources) > 0


if __name__ == "__main__":
    pytest.main([__file__])