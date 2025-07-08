"""
Advanced political market modeling with polling data integration.
"""

import re
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.clients.polymarket.models import Market
from src.clients.news.models import NewsArticle
from src.analyzers.bayesian_updater import BayesianUpdater, Evidence, EvidenceType, ProbabilityDistribution

logger = logging.getLogger(__name__)


@dataclass
class PollData:
    """Individual poll data point."""
    candidate: str
    percentage: float
    poll_date: datetime
    sample_size: int
    pollster: str
    methodology: str = "unknown"
    margin_of_error: float = 3.0
    likely_voters: bool = True


@dataclass
class ElectionFundamentals:
    """Election fundamentals data."""
    incumbent_running: bool
    economic_conditions: str  # "good", "neutral", "poor"
    approval_rating: Optional[float]
    generic_ballot: Optional[float]  # Generic D vs R preference
    historical_party_performance: float
    candidate_experience: str  # "high", "medium", "low"


class PoliticalMarketModel:
    """
    Advanced political market model using polling data, fundamentals, and historical patterns.
    """
    
    def __init__(self):
        """Initialize the political model."""
        self.bayesian_updater = BayesianUpdater()
        self.pollster_reliability = self._load_pollster_reliability()
        self.historical_patterns = self._load_historical_patterns()
        
    def calculate_political_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """
        Calculate probability for political markets using sophisticated modeling.
        
        Args:
            market: Political market to analyze
            news_articles: Related news articles
            
        Returns:
            ProbabilityDistribution: Probability with uncertainty bounds
        """
        market_type = self._classify_political_market(market)
        
        if market_type == "presidential_election":
            return self._calculate_presidential_election(market, news_articles)
        elif market_type == "congressional_election":
            return self._calculate_congressional_election(market, news_articles)
        elif market_type == "policy_implementation":
            return self._calculate_policy_probability(market, news_articles)
        elif market_type == "political_event":
            return self._calculate_political_event(market, news_articles)
        else:
            # Fallback to general political baseline
            return self._calculate_general_political(market, news_articles)
            
    def _classify_political_market(self, market: Market) -> str:
        """Classify the type of political market."""
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        if any(term in full_text for term in ["president", "presidential election", "win presidency"]):
            return "presidential_election"
        elif any(term in full_text for term in ["congress", "senate", "house", "congressional"]):
            return "congressional_election"
        elif any(term in full_text for term in ["bill", "law", "policy", "sign", "pass", "approve"]):
            return "policy_implementation"
        else:
            return "political_event"
            
    def _calculate_presidential_election(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for presidential election markets."""
        
        # Step 1: Get base probability from fundamentals
        fundamentals = self._extract_election_fundamentals(market, news_articles)
        base_prob = self._calculate_fundamentals_probability(fundamentals)
        
        # Step 2: Get polling-based probability
        polling_prob = self._calculate_polling_probability(market)
        
        # Step 3: Create evidence list for Bayesian updating
        evidence_list = []
        
        # Add polling evidence
        if polling_prob:
            # Strength based on how far polling is from 50%
            strength = abs(polling_prob - 0.5) * 2
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.POLLING_DATA,
                positive_signal=polling_prob > 0.5,
                strength=strength,
                confidence=0.8,  # High confidence in polling aggregate
                description=f"Polling average suggests {polling_prob:.1%} probability",
                source="polling_aggregate"
            ))
            
        # Add fundamentals evidence
        fundamentals_signal = fundamentals.approval_rating or 0.5
        if fundamentals_signal != 0.5:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=fundamentals_signal > 0.5,
                strength=abs(fundamentals_signal - 0.5) * 2,
                confidence=0.7,
                description=f"Election fundamentals suggest {fundamentals_signal:.1%}",
                source="fundamentals_model"
            ))
            
        # Add news sentiment evidence
        news_sentiment = self._analyze_political_news_sentiment(news_articles, market)
        if abs(news_sentiment) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=news_sentiment > 0,
                strength=min(abs(news_sentiment), 1.0),
                confidence=0.6,
                description=f"News sentiment: {'positive' if news_sentiment > 0 else 'negative'}",
                source="news_analysis"
            ))
            
        # Use Bayesian updating to combine evidence
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="political"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
            
    def _calculate_polling_probability(self, market: Market) -> Optional[float]:
        """
        Calculate probability based on polling data.
        Note: This is a placeholder - in production you'd integrate with real polling APIs.
        """
        question = market.question.lower()
        
        # Extract candidate names from market question
        candidates = self._extract_candidate_names(question)
        
        if not candidates:
            return None
            
        # Simulate polling data (in production, fetch from APIs)
        simulated_polls = self._get_simulated_polling_data(candidates)
        
        if not simulated_polls:
            return None
            
        # Calculate polling average with recency weighting
        return self._calculate_polling_average(simulated_polls, candidates[0])
        
    def _extract_candidate_names(self, question: str) -> List[str]:
        """Extract candidate names from market question."""
        # Common political figures (expand this list)
        known_candidates = [
            "trump", "biden", "harris", "desantis", "ramaswamy", 
            "christie", "haley", "vivek", "pence", "kennedy"
        ]
        
        found_candidates = []
        for candidate in known_candidates:
            if candidate in question:
                found_candidates.append(candidate)
                
        return found_candidates
        
    def _get_simulated_polling_data(self, candidates: List[str]) -> List[PollData]:
        """
        Simulate polling data. In production, this would fetch from real APIs.
        """
        # This is a placeholder - real implementation would use:
        # - FiveThirtyEight API
        # - RealClearPolitics scraping
        # - Direct pollster APIs
        
        if "trump" in candidates:
            return [
                PollData("trump", 48.5, datetime.now() - timedelta(days=1), 1200, "CNN", margin_of_error=3.0),
                PollData("trump", 47.2, datetime.now() - timedelta(days=3), 800, "FOX", margin_of_error=3.5),
                PollData("trump", 49.1, datetime.now() - timedelta(days=5), 1000, "ABC", margin_of_error=3.2),
            ]
        elif "biden" in candidates:
            return [
                PollData("biden", 51.2, datetime.now() - timedelta(days=1), 1200, "CNN", margin_of_error=3.0),
                PollData("biden", 50.8, datetime.now() - timedelta(days=3), 800, "FOX", margin_of_error=3.5),
                PollData("biden", 52.1, datetime.now() - timedelta(days=5), 1000, "ABC", margin_of_error=3.2),
            ]
            
        return []
        
    def _calculate_polling_average(self, polls: List[PollData], candidate: str) -> float:
        """Calculate weighted polling average for a candidate."""
        if not polls:
            return 0.5
            
        # Weight polls by recency and sample size
        weighted_sum = 0.0
        total_weight = 0.0
        
        for poll in polls:
            # Recency weight (more recent polls get higher weight)
            days_old = (datetime.now() - poll.poll_date).days
            recency_weight = max(0.1, 1.0 - (days_old / 30.0))  # Decay over 30 days
            
            # Sample size weight
            size_weight = min(2.0, poll.sample_size / 500.0)  # Normalize around 500
            
            # Pollster reliability weight
            reliability_weight = self.pollster_reliability.get(poll.pollster.lower(), 1.0)
            
            total_poll_weight = recency_weight * size_weight * reliability_weight
            
            weighted_sum += (poll.percentage / 100.0) * total_poll_weight
            total_weight += total_poll_weight
            
        return weighted_sum / total_weight if total_weight > 0 else 0.5
        
    def _extract_election_fundamentals(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ElectionFundamentals:
        """Extract election fundamentals from market and news data."""
        question = market.question.lower()
        
        # Determine if incumbent is running
        incumbent_running = any(name in question for name in ["biden", "trump"]) and "2024" in question
        
        # Analyze economic sentiment from news
        economic_conditions = self._analyze_economic_sentiment(news_articles)
        
        # Simulate other fundamentals (in production, fetch from real sources)
        return ElectionFundamentals(
            incumbent_running=incumbent_running,
            economic_conditions=economic_conditions,
            approval_rating=0.45 if "biden" in question else 0.48,  # Placeholder
            generic_ballot=0.49,  # Placeholder
            historical_party_performance=0.48,  # Slight Republican historical advantage
            candidate_experience="high"
        )
        
    def _calculate_fundamentals_probability(self, fundamentals: ElectionFundamentals) -> float:
        """Calculate probability based on election fundamentals model."""
        base_prob = 0.5  # Start with even odds
        
        # Incumbent advantage/disadvantage
        if fundamentals.incumbent_running:
            if fundamentals.approval_rating and fundamentals.approval_rating > 0.5:
                base_prob += 0.05  # Incumbent with good approval
            else:
                base_prob -= 0.03  # Incumbent with poor approval
                
        # Economic conditions effect
        if fundamentals.economic_conditions == "good":
            base_prob += 0.04
        elif fundamentals.economic_conditions == "poor":
            base_prob -= 0.06
            
        # Generic ballot
        if fundamentals.generic_ballot:
            base_prob += (fundamentals.generic_ballot - 0.5) * 0.8
            
        return max(0.1, min(0.9, base_prob))
        
    def _analyze_economic_sentiment(self, news_articles: List[NewsArticle]) -> str:
        """Analyze economic sentiment from news articles."""
        if not news_articles:
            return "neutral"
            
        positive_economic_terms = [
            "economic growth", "job growth", "gdp growth", "stock market up",
            "unemployment down", "wages up", "economic recovery"
        ]
        
        negative_economic_terms = [
            "recession", "economic downturn", "job losses", "unemployment up",
            "inflation", "market crash", "economic crisis"
        ]
        
        positive_count = 0
        negative_count = 0
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            positive_count += sum(1 for term in positive_economic_terms if term in text)
            negative_count += sum(1 for term in negative_economic_terms if term in text)
            
        if positive_count > negative_count * 1.5:
            return "good"
        elif negative_count > positive_count * 1.5:
            return "poor"
        else:
            return "neutral"
            
    def _analyze_political_news_sentiment(
        self, 
        news_articles: List[NewsArticle], 
        market: Market
    ) -> float:
        """Analyze political news sentiment specific to the market."""
        if not news_articles:
            return 0.0
            
        # Extract key entities from market question
        question = market.question.lower()
        entities = self._extract_political_entities(question)
        
        sentiment_scores = []
        
        for article in news_articles:
            article_text = f"{article.title} {article.description or ''}".lower()
            
            # Check if article mentions relevant entities
            if any(entity in article_text for entity in entities):
                sentiment = self._calculate_article_political_sentiment(article_text, entities)
                sentiment_scores.append(sentiment)
                
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _extract_political_entities(self, question: str) -> List[str]:
        """Extract political entities (candidates, parties) from question."""
        entities = []
        
        # Candidates
        candidates = ["trump", "biden", "harris", "desantis", "haley"]
        entities.extend([c for c in candidates if c in question])
        
        # Parties
        if "republican" in question or "gop" in question:
            entities.append("republican")
        if "democrat" in question or "democratic" in question:
            entities.append("democratic")
            
        return entities
        
    def _calculate_article_political_sentiment(self, text: str, entities: List[str]) -> float:
        """Calculate sentiment of an article towards specific political entities."""
        positive_terms = [
            "wins", "leads", "ahead", "strong", "popular", "successful",
            "gains", "momentum", "support", "endorsement", "victory"
        ]
        
        negative_terms = [
            "loses", "behind", "weak", "unpopular", "scandal", "controversy",
            "declines", "struggles", "criticism", "defeat", "problems"
        ]
        
        # Look for sentiment near entity mentions
        sentiment_score = 0.0
        entity_mentions = 0
        
        for entity in entities:
            if entity in text:
                entity_mentions += 1
                # Look at words near the entity mention
                entity_pos = text.find(entity)
                context_start = max(0, entity_pos - 100)
                context_end = min(len(text), entity_pos + 100)
                context = text[context_start:context_end]
                
                positive_count = sum(1 for term in positive_terms if term in context)
                negative_count = sum(1 for term in negative_terms if term in context)
                
                if positive_count > 0 or negative_count > 0:
                    sentiment_score += (positive_count - negative_count) / (positive_count + negative_count)
                    
        return sentiment_score / entity_mentions if entity_mentions > 0 else 0.0
        
    def _calculate_congressional_election(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for congressional election markets."""
        # Simplified implementation - could be expanded significantly
        base_prob = 0.48  # Slight Republican historical advantage in midterms
        
        evidence_list = [
            self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=True,
                strength=0.3,
                confidence=0.6,
                description="Historical congressional patterns",
                source="historical_analysis"
            )
        ]
        
        return self.bayesian_updater.update_probability(
            prior=base_prob,
            evidence_list=evidence_list,
            market_type="political"
        )
        
    def _calculate_policy_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for policy implementation markets."""
        question = market.question.lower()
        
        # Analyze political control
        has_unified_government = self._analyze_political_control(news_articles)
        
        if has_unified_government:
            base_prob = 0.65  # Higher chance with unified control
        else:
            base_prob = 0.25  # Lower chance with divided government
            
        # Check if it's early in presidency
        if "first" in question and ("month" in question or "100 days" in question):
            base_prob += 0.15  # Honeymoon period boost
            
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
        
    def _calculate_political_event(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for general political events."""
        base_prob = 0.35  # Conservative baseline for political events
        
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
        
    def _calculate_general_political(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Fallback for unclassified political markets."""
        base_prob = 0.40  # Generic political baseline
        
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.4)
        
    def _analyze_political_control(self, news_articles: List[NewsArticle]) -> bool:
        """Determine if there's unified government control."""
        # Simplified analysis - could be much more sophisticated
        return True  # Placeholder
        
    def _load_pollster_reliability(self) -> Dict[str, float]:
        """Load pollster reliability ratings."""
        return {
            "cnn": 1.2,
            "abc": 1.1,
            "cbs": 1.1,
            "nbc": 1.1,
            "fox": 1.0,
            "quinnipiac": 1.3,
            "marist": 1.2,
            "monmouth": 1.3,
            "reuters": 1.1,
            "ipsos": 1.0,
            "rasmussen": 0.8,  # Known Republican lean
            "trafalgar": 0.7,  # Known Republican lean
        }
        
    def _load_historical_patterns(self) -> Dict[str, float]:
        """Load historical political patterns."""
        return {
            "midterm_incumbent_loss": 0.75,  # Incumbent party usually loses midterms
            "presidential_incumbent_advantage": 0.55,  # Slight incumbent advantage
            "economic_voting_correlation": 0.8,  # Strong correlation with economy
        }