"""
Advanced entertainment and awards market modeling.
"""

import re
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from src.clients.polymarket.models import Market
from src.clients.news.models import NewsArticle
from src.analyzers.bayesian_updater import BayesianUpdater, Evidence, EvidenceType, ProbabilityDistribution

logger = logging.getLogger(__name__)


class EntertainmentCategory(Enum):
    """Types of entertainment events."""
    OSCARS = "oscars"
    EMMYS = "emmys"
    GRAMMYS = "grammys"
    GOLDEN_GLOBES = "golden_globes"
    TV_RENEWAL = "tv_renewal"
    TV_CANCELLATION = "tv_cancellation"
    BOX_OFFICE = "box_office"
    STREAMING_RELEASE = "streaming_release"
    CELEBRITY_EVENT = "celebrity_event"
    GAME_AWARDS = "game_awards"


@dataclass
class MovieData:
    """Movie/show performance data."""
    title: str
    release_date: Optional[datetime]
    budget: Optional[float]
    current_revenue: Optional[float]
    critic_score: Optional[float]  # 0-100
    audience_score: Optional[float]  # 0-100
    genre: str
    studio: str
    director: str
    cast_star_power: float  # 0-1, measure of cast popularity
    awards_buzz: float  # 0-1, measure of awards campaign/buzz


@dataclass
class TVShowData:
    """TV show performance data."""
    title: str
    network: str
    seasons_aired: int
    current_viewership: float  # millions
    viewership_trend: str  # "increasing", "stable", "declining"
    critic_score: Optional[float]
    audience_score: Optional[float]
    production_cost: Optional[float]
    streaming_performance: Optional[float]  # 0-1, relative to platform average
    renewal_history: List[bool]  # Past renewal decisions


@dataclass
class AwardsPrediction:
    """Awards prediction data."""
    nominee: str
    category: str
    award_show: EntertainmentCategory
    betting_odds: Optional[float]
    critic_predictions: List[str]  # List of critics predicting this nominee
    guild_awards: List[str]  # Previous guild awards won
    campaign_strength: float  # 0-1, marketing campaign effectiveness
    narrative_strength: float  # 0-1, "story" appeal (comeback, overdue, etc.)


@dataclass
class CelebrityEventData:
    """Celebrity event prediction data."""
    celebrity: str
    event_type: str  # "marriage", "divorce", "retirement", etc.
    recent_activity: List[str]
    social_media_signals: float  # -1 to 1, sentiment
    tabloid_coverage: float  # 0-1, amount of coverage
    historical_patterns: List[str]  # Past similar events


class EntertainmentMarketModel:
    """
    Advanced entertainment market model for awards, TV renewals, box office, etc.
    """
    
    def __init__(self):
        """Initialize the entertainment model."""
        self.bayesian_updater = BayesianUpdater()
        self.awards_databases = self._load_awards_databases()
        self.box_office_patterns = self._load_box_office_patterns()
        self.tv_renewal_patterns = self._load_tv_renewal_patterns()
        
    def calculate_entertainment_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """
        Calculate probability for entertainment markets.
        
        Args:
            market: Entertainment market to analyze
            news_articles: Related news articles
            
        Returns:
            ProbabilityDistribution: Probability with uncertainty bounds
        """
        category = self._identify_entertainment_category(market)
        
        if category in [EntertainmentCategory.OSCARS, EntertainmentCategory.EMMYS, 
                       EntertainmentCategory.GRAMMYS, EntertainmentCategory.GOLDEN_GLOBES]:
            return self._calculate_awards_probability(market, news_articles, category)
        elif category in [EntertainmentCategory.TV_RENEWAL, EntertainmentCategory.TV_CANCELLATION]:
            return self._calculate_tv_renewal_probability(market, news_articles)
        elif category == EntertainmentCategory.BOX_OFFICE:
            return self._calculate_box_office_probability(market, news_articles)
        elif category == EntertainmentCategory.CELEBRITY_EVENT:
            return self._calculate_celebrity_event_probability(market, news_articles)
        else:
            return self._calculate_general_entertainment(market, news_articles)
            
    def _identify_entertainment_category(self, market: Market) -> EntertainmentCategory:
        """Identify the entertainment category from market question."""
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        if any(term in full_text for term in ["oscar", "academy award", "best picture", "best actor"]):
            return EntertainmentCategory.OSCARS
        elif any(term in full_text for term in ["emmy", "television award", "outstanding drama"]):
            return EntertainmentCategory.EMMYS
        elif any(term in full_text for term in ["grammy", "music award", "album of the year"]):
            return EntertainmentCategory.GRAMMYS
        elif any(term in full_text for term in ["golden globe", "hfpa"]):
            return EntertainmentCategory.GOLDEN_GLOBES
        elif any(term in full_text for term in ["renewed", "renewal", "another season", "next season"]):
            return EntertainmentCategory.TV_RENEWAL
        elif any(term in full_text for term in ["cancelled", "canceled", "final season", "ending"]):
            return EntertainmentCategory.TV_CANCELLATION
        elif any(term in full_text for term in ["box office", "gross", "ticket sales", "$", "million"]):
            return EntertainmentCategory.BOX_OFFICE
        elif any(term in full_text for term in ["marry", "divorce", "split", "dating", "pregnant"]):
            return EntertainmentCategory.CELEBRITY_EVENT
        else:
            return EntertainmentCategory.STREAMING_RELEASE
            
    def _calculate_awards_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle],
        category: EntertainmentCategory
    ) -> ProbabilityDistribution:
        """Calculate probability for awards markets."""
        
        # Extract nominee and award category
        nominee, award_category = self._extract_awards_info(market.question)
        
        # Get awards prediction data
        prediction_data = self._get_awards_prediction_data(nominee, award_category, category)
        
        # Calculate base probability
        base_prob = self._calculate_awards_base_probability(prediction_data, category)
        
        # Create evidence list
        evidence_list = []
        
        # Add betting odds evidence
        if prediction_data and prediction_data.betting_odds:
            odds_signal = self._evaluate_betting_odds(prediction_data.betting_odds)
            if abs(odds_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.MARKET_BEHAVIOR,
                    positive_signal=odds_signal > 0,
                    strength=min(abs(odds_signal), 1.0),
                    confidence=0.7,
                    description=f"Betting markets favor at {prediction_data.betting_odds:.1f}:1",
                    source="betting_markets"
                ))
                
        # Add critic consensus evidence
        if prediction_data and prediction_data.critic_predictions:
            critic_signal = self._evaluate_critic_consensus(prediction_data.critic_predictions)
            if abs(critic_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=critic_signal > 0,
                    strength=min(abs(critic_signal), 1.0),
                    confidence=0.8,
                    description=f"{len(prediction_data.critic_predictions)} critics predicting win",
                    source="critic_consensus"
                ))
                
        # Add guild awards evidence (strong predictor for Oscars)
        if prediction_data and prediction_data.guild_awards:
            guild_signal = self._evaluate_guild_awards(prediction_data.guild_awards, category)
            if abs(guild_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=guild_signal > 0,
                    strength=min(abs(guild_signal), 1.0),
                    confidence=0.9,
                    description=f"Won {len(prediction_data.guild_awards)} guild awards",
                    source="guild_awards"
                ))
                
        # Add campaign strength evidence
        if prediction_data:
            campaign_signal = self._evaluate_campaign_strength(prediction_data.campaign_strength)
            if abs(campaign_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.MARKET_BEHAVIOR,
                    positive_signal=campaign_signal > 0,
                    strength=min(abs(campaign_signal), 1.0),
                    confidence=0.6,
                    description=f"{'Strong' if campaign_signal > 0 else 'Weak'} awards campaign",
                    source="campaign_analysis"
                ))
                
        # Add news buzz evidence
        news_buzz = self._analyze_awards_news_buzz(news_articles, nominee)
        if abs(news_buzz) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=news_buzz > 0,
                strength=min(abs(news_buzz), 1.0),
                confidence=0.5,
                description=f"{'Positive' if news_buzz > 0 else 'Negative'} media buzz",
                source="entertainment_media"
            ))
        
        # Use Bayesian updating
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="entertainment"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
            
    def _calculate_tv_renewal_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for TV renewal/cancellation markets."""
        
        # Extract show name
        show_name = self._extract_show_name(market.question)
        
        # Get show performance data
        show_data = self._get_tv_show_data(show_name)
        
        # Calculate base probability
        base_prob = self._calculate_tv_renewal_base_probability(show_data)
        
        # Create evidence list
        evidence_list = []
        
        # Add viewership evidence
        if show_data:
            viewership_signal = self._evaluate_tv_viewership(show_data)
            if abs(viewership_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.MARKET_BEHAVIOR,
                    positive_signal=viewership_signal > 0,
                    strength=min(abs(viewership_signal), 1.0),
                    confidence=0.8,
                    description=f"Viewership {show_data.viewership_trend}",
                    source="ratings_data"
                ))
                
        # Add critical reception evidence
        if show_data and show_data.critic_score:
            critical_signal = self._evaluate_critical_reception(show_data.critic_score)
            if abs(critical_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=critical_signal > 0,
                    strength=min(abs(critical_signal), 1.0),
                    confidence=0.6,
                    description=f"Critic score: {show_data.critic_score}/100",
                    source="critic_reviews"
                ))
                
        # Add production cost efficiency
        if show_data:
            cost_signal = self._evaluate_production_efficiency(show_data)
            if abs(cost_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.MARKET_BEHAVIOR,
                    positive_signal=cost_signal > 0,
                    strength=min(abs(cost_signal), 1.0),
                    confidence=0.7,
                    description=f"Production {'efficient' if cost_signal > 0 else 'expensive'}",
                    source="production_analysis"
                ))
                
        # Add news sentiment
        renewal_sentiment = self._analyze_renewal_news_sentiment(news_articles, show_name)
        if abs(renewal_sentiment) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=renewal_sentiment > 0,
                strength=min(abs(renewal_sentiment), 1.0),
                confidence=0.5,
                description=f"Media {'optimistic' if renewal_sentiment > 0 else 'pessimistic'} about renewal",
                source="tv_media"
            ))
        
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="entertainment"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
            
    def _calculate_box_office_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for box office performance markets."""
        
        # Extract movie and target
        movie_title, box_office_target = self._extract_box_office_info(market.question)
        
        # Get movie data
        movie_data = self._get_movie_data(movie_title)
        
        # Calculate base probability
        base_prob = self._calculate_box_office_base_probability(movie_data, box_office_target)
        
        # Create evidence list
        evidence_list = []
        
        # Add opening weekend tracking
        if movie_data and movie_data.current_revenue:
            tracking_signal = self._evaluate_box_office_tracking(movie_data, box_office_target)
            if abs(tracking_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.MARKET_BEHAVIOR,
                    positive_signal=tracking_signal > 0,
                    strength=min(abs(tracking_signal), 1.0),
                    confidence=0.8,
                    description=f"Tracking {'ahead of' if tracking_signal > 0 else 'behind'} target",
                    source="box_office_tracking"
                ))
                
        # Add genre/franchise factor
        if movie_data:
            genre_signal = self._evaluate_genre_performance(movie_data.genre)
            if abs(genre_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=genre_signal > 0,
                    strength=min(abs(genre_signal), 1.0),
                    confidence=0.6,
                    description=f"{movie_data.genre} films {'performing well' if genre_signal > 0 else 'underperforming'}",
                    source="genre_analysis"
                ))
                
        # Add star power factor
        if movie_data:
            star_signal = self._evaluate_star_power(movie_data.cast_star_power)
            if abs(star_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.MARKET_BEHAVIOR,
                    positive_signal=star_signal > 0,
                    strength=min(abs(star_signal), 1.0),
                    confidence=0.5,
                    description=f"{'Strong' if star_signal > 0 else 'Weak'} star power",
                    source="cast_analysis"
                ))
        
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="entertainment"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
            
    def _calculate_celebrity_event_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for celebrity event markets."""
        
        # Extract celebrity and event type
        celebrity, event_type = self._extract_celebrity_event_info(market.question)
        
        # Get celebrity data
        celebrity_data = self._get_celebrity_event_data(celebrity, event_type)
        
        # Calculate base probability
        base_prob = self._calculate_celebrity_event_base_probability(event_type)
        
        # Create evidence list
        evidence_list = []
        
        # Add social media signals
        if celebrity_data:
            social_signal = celebrity_data.social_media_signals
            if abs(social_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.SOCIAL_SENTIMENT,
                    positive_signal=social_signal > 0,
                    strength=min(abs(social_signal), 1.0),
                    confidence=0.6,
                    description=f"Social media {'hints' if social_signal > 0 else 'quiet'} about {event_type}",
                    source="social_media"
                ))
                
        # Add tabloid coverage
        if celebrity_data:
            tabloid_signal = self._evaluate_tabloid_coverage(celebrity_data.tabloid_coverage, event_type)
            if abs(tabloid_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.NEWS_SENTIMENT,
                    positive_signal=tabloid_signal > 0,
                    strength=min(abs(tabloid_signal), 1.0),
                    confidence=0.4,
                    description=f"{'Heavy' if tabloid_signal > 0 else 'Light'} tabloid speculation",
                    source="tabloid_media"
                ))
                
        # Add historical patterns
        if celebrity_data and celebrity_data.historical_patterns:
            history_signal = self._evaluate_celebrity_history(celebrity_data.historical_patterns, event_type)
            if abs(history_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=history_signal > 0,
                    strength=min(abs(history_signal), 1.0),
                    confidence=0.5,
                    description=f"Historical {'precedent' if history_signal > 0 else 'stability'}",
                    source="celebrity_history"
                ))
        
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="entertainment"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.4)
            
    def _extract_awards_info(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract nominee and category from awards market question."""
        # Common patterns for awards markets
        patterns = [
            r"Will (.+) win Best (.+)",
            r"(.+) to win (.+) award",
            r"(.+) for Best (.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).strip(), match.group(2).strip()
                
        return None, None
        
    def _extract_show_name(self, question: str) -> Optional[str]:
        """Extract TV show name from market question."""
        patterns = [
            r"Will (.+) be renewed",
            r"(.+) renewal",
            r"(.+) cancelled",
            r"(.+) get another season"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None
        
    def _extract_box_office_info(self, question: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract movie title and box office target."""
        # Pattern to find movie title and dollar amount
        pattern = r"Will (.+) gross over \$([0-9,]+)"
        match = re.search(pattern, question, re.IGNORECASE)
        
        if match:
            movie = match.group(1).strip()
            target = float(match.group(2).replace(',', ''))
            return movie, target
            
        return None, None
        
    def _extract_celebrity_event_info(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract celebrity name and event type."""
        event_patterns = {
            "marriage": ["marry", "married", "wedding"],
            "divorce": ["divorce", "split", "separate"],
            "baby": ["pregnant", "baby", "child"],
            "retirement": ["retire", "quit", "leave"]
        }
        
        for event_type, keywords in event_patterns.items():
            for keyword in keywords:
                if keyword in question.lower():
                    # Extract celebrity name (usually at start)
                    words = question.split()
                    if len(words) >= 2:
                        celebrity = " ".join(words[:2])  # First two words as name
                        return celebrity, event_type
                        
        return None, None
        
    def _calculate_awards_base_probability(
        self, 
        prediction_data: Optional[AwardsPrediction],
        category: EntertainmentCategory
    ) -> float:
        """Calculate base probability for awards."""
        
        # Category-specific base rates
        if category == EntertainmentCategory.OSCARS:
            # Oscars are relatively predictable with favorites
            if prediction_data and prediction_data.guild_awards:
                if len(prediction_data.guild_awards) >= 2:
                    return 0.75  # Strong guild support
                elif len(prediction_data.guild_awards) == 1:
                    return 0.45  # Some guild support
            return 0.20  # Default for no guild support
            
        elif category == EntertainmentCategory.EMMYS:
            # Emmys can be more unpredictable
            return 0.25
            
        elif category == EntertainmentCategory.GRAMMYS:
            # Grammys often surprise
            return 0.20
            
        elif category == EntertainmentCategory.GOLDEN_GLOBES:
            # Golden Globes love surprises
            return 0.22
            
        return 0.25  # Default
        
    def _calculate_tv_renewal_base_probability(
        self, 
        show_data: Optional[TVShowData]
    ) -> float:
        """Calculate base probability for TV renewal."""
        
        if not show_data:
            return 0.50  # Unknown show
            
        # Base rate by network type
        if show_data.network in ["Netflix", "HBO", "Apple TV+", "Amazon"]:
            base_prob = 0.65  # Streaming services renew more often
        elif show_data.network in ["CBS", "NBC", "ABC", "FOX"]:
            base_prob = 0.55  # Broadcast networks more selective
        else:
            base_prob = 0.60  # Cable networks
            
        # Adjust for season number
        if show_data.seasons_aired == 1:
            base_prob *= 0.8  # First season renewals harder
        elif show_data.seasons_aired >= 5:
            base_prob *= 1.1  # Established shows more likely
            
        # Adjust for viewership trend
        if show_data.viewership_trend == "increasing":
            base_prob *= 1.3
        elif show_data.viewership_trend == "declining":
            base_prob *= 0.7
            
        return min(0.90, max(0.10, base_prob))
        
    def _calculate_box_office_base_probability(
        self, 
        movie_data: Optional[MovieData],
        target: Optional[float]
    ) -> float:
        """Calculate base probability for box office targets."""
        
        if not movie_data or not target:
            return 0.30  # Default
            
        if not movie_data.budget:
            return 0.30
            
        # Compare target to budget multiples
        if movie_data.budget > 0:
            target_multiple = target / movie_data.budget
            
            if target_multiple < 1.0:
                return 0.70  # Breaking even is common
            elif target_multiple < 2.0:
                return 0.45  # 2x budget is moderate success
            elif target_multiple < 3.0:
                return 0.25  # 3x budget is major success
            else:
                return 0.10  # Blockbuster territory
        else:
            return 0.30
            
    def _calculate_celebrity_event_base_probability(self, event_type: str) -> float:
        """Calculate base probability for celebrity events."""
        
        base_rates = {
            "marriage": 0.15,  # Celebrity marriages less predictable
            "divorce": 0.25,   # Higher rate but still uncertain
            "baby": 0.20,      # Pregnancy announcements
            "retirement": 0.10 # Retirement announcements rare
        }
        
        return base_rates.get(event_type, 0.20)
        
    def _evaluate_betting_odds(self, odds: float) -> float:
        """Evaluate betting odds signal strength."""
        # Convert odds to implied probability
        implied_prob = 1.0 / (1.0 + odds)
        
        # Strong favorite
        if implied_prob > 0.7:
            return 0.6
        elif implied_prob > 0.5:
            return 0.3
        elif implied_prob < 0.2:
            return -0.5
        else:
            return 0.0
            
    def _evaluate_critic_consensus(self, predictions: List[str]) -> float:
        """Evaluate critic consensus signal."""
        if len(predictions) >= 10:
            return 0.7  # Strong consensus
        elif len(predictions) >= 5:
            return 0.4  # Moderate consensus
        elif len(predictions) >= 2:
            return 0.2  # Some support
        else:
            return -0.1  # Little support
            
    def _evaluate_guild_awards(self, guild_awards: List[str], category: EntertainmentCategory) -> float:
        """Evaluate guild awards as Oscar predictors."""
        if category != EntertainmentCategory.OSCARS:
            return 0.2 * len(guild_awards)  # Less predictive for other awards
            
        # For Oscars, guild awards are very predictive
        key_guilds = ["SAG", "DGA", "PGA", "WGA"]
        key_guild_wins = sum(1 for award in guild_awards if any(guild in award for guild in key_guilds))
        
        if key_guild_wins >= 3:
            return 0.8  # Sweep indicates strong favorite
        elif key_guild_wins >= 2:
            return 0.6
        elif key_guild_wins >= 1:
            return 0.4
        else:
            return 0.0
            
    def _evaluate_campaign_strength(self, strength: float) -> float:
        """Evaluate awards campaign effectiveness."""
        if strength > 0.8:
            return 0.4  # Strong campaigns help
        elif strength > 0.6:
            return 0.2
        elif strength < 0.3:
            return -0.3  # Weak campaign hurts chances
        else:
            return 0.0
            
    def _evaluate_tv_viewership(self, show_data: TVShowData) -> float:
        """Evaluate TV viewership signal."""
        # Different thresholds for different networks
        if show_data.network in ["Netflix", "HBO", "Amazon"]:
            threshold = 2.0  # Lower bar for streaming in millions
        else:
            threshold = 5.0  # Higher bar for broadcast
            
        if show_data.current_viewership > threshold * 1.5:
            signal = 0.6  # Strong viewership
        elif show_data.current_viewership > threshold:
            signal = 0.3  # Good viewership
        elif show_data.current_viewership < threshold * 0.5:
            signal = -0.6  # Poor viewership
        else:
            signal = 0.0
            
        # Adjust for trend
        if show_data.viewership_trend == "increasing":
            signal += 0.2
        elif show_data.viewership_trend == "declining":
            signal -= 0.3
            
        return max(-1.0, min(1.0, signal))
        
    def _evaluate_critical_reception(self, critic_score: float) -> float:
        """Evaluate critical reception impact."""
        if critic_score >= 85:
            return 0.4  # Critical darling
        elif critic_score >= 70:
            return 0.2  # Well received
        elif critic_score < 50:
            return -0.4  # Poorly received
        else:
            return 0.0
            
    def _evaluate_production_efficiency(self, show_data: TVShowData) -> float:
        """Evaluate production cost efficiency."""
        if not show_data.production_cost or show_data.current_viewership == 0:
            return 0.0
            
        # Cost per million viewers
        efficiency = show_data.production_cost / show_data.current_viewership
        
        if efficiency < 1.0:  # Very efficient
            return 0.4
        elif efficiency < 2.0:  # Reasonably efficient
            return 0.2
        elif efficiency > 5.0:  # Very expensive per viewer
            return -0.5
        else:
            return 0.0
            
    def _evaluate_box_office_tracking(self, movie_data: MovieData, target: float) -> float:
        """Evaluate box office tracking vs target."""
        if not movie_data.current_revenue:
            return 0.0
            
        # Calculate trajectory
        if movie_data.release_date:
            days_in_release = (datetime.now() - movie_data.release_date).days
            if days_in_release > 0:
                daily_average = movie_data.current_revenue / days_in_release
                projected_total = daily_average * 90  # Typical theatrical window
                
                ratio = projected_total / target
                
                if ratio > 1.2:
                    return 0.6  # Well ahead of target
                elif ratio > 1.0:
                    return 0.3  # On track
                elif ratio < 0.5:
                    return -0.6  # Far behind
                else:
                    return -0.2  # Behind target
                    
        return 0.0
        
    def _evaluate_genre_performance(self, genre: str) -> float:
        """Evaluate current genre performance trends."""
        # Current market trends (would be updated with real data)
        hot_genres = ["superhero", "horror", "animated", "sequel"]
        cold_genres = ["musical", "western", "drama", "original"]
        
        if any(g in genre.lower() for g in hot_genres):
            return 0.3
        elif any(g in genre.lower() for g in cold_genres):
            return -0.2
        else:
            return 0.0
            
    def _evaluate_star_power(self, star_power: float) -> float:
        """Evaluate star power impact on box office."""
        if star_power > 0.8:
            return 0.4  # A-list cast
        elif star_power > 0.6:
            return 0.2  # Known actors
        elif star_power < 0.3:
            return -0.2  # Unknown cast
        else:
            return 0.0
            
    def _evaluate_tabloid_coverage(self, coverage: float, event_type: str) -> float:
        """Evaluate tabloid coverage signal."""
        # Heavy coverage can indicate something brewing
        if coverage > 0.8:
            return 0.3
        elif coverage > 0.5:
            return 0.1
        elif coverage < 0.2:
            return -0.2  # Quiet usually means no event
        else:
            return 0.0
            
    def _evaluate_celebrity_history(self, patterns: List[str], event_type: str) -> float:
        """Evaluate celebrity's historical patterns."""
        relevant_patterns = [p for p in patterns if event_type in p.lower()]
        
        if len(relevant_patterns) >= 2:
            return 0.4  # Pattern suggests likelihood
        elif len(relevant_patterns) == 1:
            return 0.2
        else:
            return -0.1  # No pattern
            
    def _analyze_awards_news_buzz(self, news_articles: List[NewsArticle], nominee: Optional[str]) -> float:
        """Analyze news buzz around awards nominee."""
        if not news_articles or not nominee:
            return 0.0
            
        positive_terms = ["favorite", "frontrunner", "momentum", "sweep", "lock", "predicted"]
        negative_terms = ["underdog", "unlikely", "surprise", "dark horse", "upset"]
        
        sentiment_scores = []
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            if nominee.lower() in text:
                positive_count = sum(1 for term in positive_terms if term in text)
                negative_count = sum(1 for term in negative_terms if term in text)
                
                if positive_count > 0 or negative_count > 0:
                    sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                    sentiment_scores.append(sentiment)
                    
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _analyze_renewal_news_sentiment(self, news_articles: List[NewsArticle], show: Optional[str]) -> float:
        """Analyze news sentiment about TV renewal."""
        if not news_articles or not show:
            return 0.0
            
        renewal_positive = ["renewed", "picked up", "returning", "confirmed", "greenlit"]
        renewal_negative = ["cancelled", "ending", "final season", "axed", "not returning"]
        
        sentiment_scores = []
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            if show.lower() in text:
                positive_count = sum(1 for term in renewal_positive if term in text)
                negative_count = sum(1 for term in renewal_negative if term in text)
                
                if positive_count > 0 or negative_count > 0:
                    sentiment = (positive_count - negative_count) / (positive_count + negative_count)
                    sentiment_scores.append(sentiment)
                    
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _calculate_general_entertainment(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Fallback for general entertainment markets."""
        base_prob = 0.35  # General entertainment baseline
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.4)
        
    # Placeholder data loading methods
    def _load_awards_databases(self) -> Dict:
        """Load awards historical data."""
        return {}
        
    def _load_box_office_patterns(self) -> Dict:
        """Load box office performance patterns."""
        return {}
        
    def _load_tv_renewal_patterns(self) -> Dict:
        """Load TV renewal historical patterns."""
        return {}
        
    def _get_awards_prediction_data(
        self, 
        nominee: Optional[str], 
        category: Optional[str],
        award_show: EntertainmentCategory
    ) -> Optional[AwardsPrediction]:
        """Get awards prediction data (placeholder)."""
        # In production, would fetch from awards databases
        return None
        
    def _get_tv_show_data(self, show_name: Optional[str]) -> Optional[TVShowData]:
        """Get TV show performance data (placeholder)."""
        # In production, would fetch from ratings services
        return None
        
    def _get_movie_data(self, movie_title: Optional[str]) -> Optional[MovieData]:
        """Get movie performance data (placeholder)."""
        # In production, would fetch from box office services
        return None
        
    def _get_celebrity_event_data(
        self, 
        celebrity: Optional[str], 
        event_type: Optional[str]
    ) -> Optional[CelebrityEventData]:
        """Get celebrity event data (placeholder)."""
        # In production, would analyze social media and tabloid coverage
        return None