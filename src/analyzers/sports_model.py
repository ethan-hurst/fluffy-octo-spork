"""
Advanced sports market modeling with performance data, injury reports, and historical patterns.
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


class SportType(Enum):
    """Types of sports."""
    NFL = "nfl"
    NBA = "nba"
    MLB = "mlb"
    NHL = "nhl"
    SOCCER = "soccer"
    COLLEGE_FOOTBALL = "college_football"
    COLLEGE_BASKETBALL = "college_basketball"


class EventType(Enum):
    """Types of sports events."""
    CHAMPIONSHIP = "championship"
    PLAYOFF_APPEARANCE = "playoff_appearance"
    COACHING_CHANGE = "coaching_change"
    PLAYER_RETIREMENT = "player_retirement"
    PLAYER_TRADE = "player_trade"
    AWARD_WINNER = "award_winner"
    SEASON_RECORD = "season_record"
    DRAFT_PICK = "draft_pick"


@dataclass
class TeamPerformance:
    """Team performance metrics."""
    team_name: str
    wins: int
    losses: int
    win_percentage: float
    points_for: float
    points_against: float
    strength_of_schedule: float
    injuries_key_players: int
    recent_form: str  # "hot", "cold", "average"
    playoff_position: Optional[int]
    championship_odds: Optional[float]


@dataclass
class PlayerStats:
    """Individual player statistics."""
    player_name: str
    age: int
    position: str
    games_played: int
    performance_rating: float  # 0-100 scale
    injury_history: List[str]
    contract_years_remaining: int
    recent_performance_trend: str  # "improving", "declining", "stable"


@dataclass
class CoachingData:
    """Coaching-related data."""
    coach_name: str
    years_with_team: int
    career_win_percentage: float
    playoff_appearances: int
    championships: int
    contract_years_remaining: int
    recent_pressure: str  # "high", "medium", "low"
    ownership_support: str  # "strong", "moderate", "weak"


@dataclass
class InjuryReport:
    """Injury report data."""
    player_name: str
    injury_type: str
    severity: str  # "minor", "moderate", "major"
    expected_return: Optional[datetime]
    games_missed: int
    position_importance: str  # "critical", "important", "depth"


class SportsMarketModel:
    """
    Advanced sports market model using performance data, injury reports, and historical patterns.
    """
    
    def __init__(self):
        """Initialize the sports model."""
        self.bayesian_updater = BayesianUpdater()
        self.team_databases = self._load_team_databases()
        self.historical_patterns = self._load_historical_patterns()
        self.coaching_change_patterns = self._load_coaching_change_patterns()
        
    def calculate_sports_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """
        Calculate probability for sports markets using comprehensive analysis.
        
        Args:
            market: Sports market to analyze
            news_articles: Related news articles
            
        Returns:
            ProbabilityDistribution: Probability with uncertainty bounds
        """
        sport_type = self._identify_sport(market)
        event_type = self._classify_sports_event(market)
        
        if event_type == EventType.COACHING_CHANGE:
            return self._calculate_coaching_change_probability(market, news_articles, sport_type)
        elif event_type == EventType.CHAMPIONSHIP:
            return self._calculate_championship_probability(market, news_articles, sport_type)
        elif event_type == EventType.PLAYER_RETIREMENT:
            return self._calculate_retirement_probability(market, news_articles, sport_type)
        elif event_type == EventType.PLAYER_TRADE:
            return self._calculate_trade_probability(market, news_articles, sport_type)
        elif event_type == EventType.PLAYOFF_APPEARANCE:
            return self._calculate_playoff_probability(market, news_articles, sport_type)
        elif event_type == EventType.AWARD_WINNER:
            return self._calculate_award_probability(market, news_articles, sport_type)
        else:
            # Fallback to general sports baseline
            return self._calculate_general_sports(market, news_articles, sport_type)
            
    def _identify_sport(self, market: Market) -> SportType:
        """Identify the sport from market question."""
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        if "nfl" in full_text or any(team in full_text for team in self._get_nfl_teams()):
            return SportType.NFL
        elif "nba" in full_text or any(team in full_text for team in self._get_nba_teams()):
            return SportType.NBA
        elif "mlb" in full_text or any(team in full_text for team in self._get_mlb_teams()):
            return SportType.MLB
        elif "nhl" in full_text or any(team in full_text for team in self._get_nhl_teams()):
            return SportType.NHL
        elif any(term in full_text for term in ["soccer", "football", "premier league", "champions league"]):
            return SportType.SOCCER
        elif any(term in full_text for term in ["college football", "ncaa football"]):
            return SportType.COLLEGE_FOOTBALL
        elif any(term in full_text for term in ["college basketball", "march madness", "ncaa tournament"]):
            return SportType.COLLEGE_BASKETBALL
        else:
            return SportType.NFL  # Default fallback
            
    def _classify_sports_event(self, market: Market) -> EventType:
        """Classify the type of sports event."""
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        if any(term in full_text for term in ["fire", "fired", "coach", "coaching change", "new coach"]):
            return EventType.COACHING_CHANGE
        elif any(term in full_text for term in ["championship", "super bowl", "world series", "stanley cup", "nba finals"]):
            return EventType.CHAMPIONSHIP
        elif any(term in full_text for term in ["retire", "retirement", "final season"]):
            return EventType.PLAYER_RETIREMENT
        elif any(term in full_text for term in ["trade", "traded", "deal", "acquire"]):
            return EventType.PLAYER_TRADE
        elif any(term in full_text for term in ["playoffs", "playoff", "postseason", "wild card"]):
            return EventType.PLAYOFF_APPEARANCE
        elif any(term in full_text for term in ["mvp", "award", "rookie of the year", "cy young", "defensive player"]):
            return EventType.AWARD_WINNER
        elif any(term in full_text for term in ["wins", "record", "season", "games"]):
            return EventType.SEASON_RECORD
        else:
            return EventType.CHAMPIONSHIP  # Default fallback
            
    def _calculate_coaching_change_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle],
        sport_type: SportType
    ) -> ProbabilityDistribution:
        """Calculate probability for coaching change markets."""
        
        # Extract team from market question
        team = self._extract_team_name(market.question, sport_type)
        
        # Get team performance and coaching data
        team_performance = self._get_team_performance(team, sport_type)
        coaching_data = self._get_coaching_data(team, sport_type)
        
        # Calculate base probability
        base_prob = self._calculate_coaching_change_base_probability(
            team_performance, coaching_data, sport_type
        )
        
        # Create evidence list
        evidence_list = []
        
        # Add team performance evidence
        if team_performance:
            performance_signal = self._evaluate_team_performance_for_coaching_change(team_performance)
            if abs(performance_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=performance_signal > 0,
                    strength=min(abs(performance_signal), 1.0),
                    confidence=0.8,
                    description=f"Team performance: {team_performance.recent_form} form, {team_performance.win_percentage:.1%} win rate",
                    source="team_performance"
                ))
                
        # Add coaching tenure/contract evidence
        if coaching_data:
            tenure_signal = self._evaluate_coaching_tenure_risk(coaching_data)
            if abs(tenure_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=tenure_signal > 0,
                    strength=min(abs(tenure_signal), 1.0),
                    confidence=0.7,
                    description=f"Coaching situation: {coaching_data.years_with_team} years tenure, {coaching_data.recent_pressure} pressure",
                    source="coaching_analysis"
                ))
                
        # Add news sentiment evidence
        news_sentiment = self._analyze_coaching_news_sentiment(news_articles, team)
        if abs(news_sentiment) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=news_sentiment > 0,
                strength=min(abs(news_sentiment), 1.0),
                confidence=0.6,
                description=f"Media sentiment: {'negative' if news_sentiment > 0 else 'supportive'} coaching coverage",
                source="sports_media"
            ))
            
        # Add historical pattern evidence
        historical_risk = self._get_historical_coaching_change_risk(sport_type, team_performance)
        if abs(historical_risk) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=historical_risk > 0,
                strength=min(abs(historical_risk), 1.0),
                confidence=0.5,
                description=f"Historical patterns suggest {'elevated' if historical_risk > 0 else 'reduced'} risk",
                source="historical_analysis"
            ))
        
        # Use Bayesian updating
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="sports"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
            
    def _calculate_championship_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle],
        sport_type: SportType
    ) -> ProbabilityDistribution:
        """Calculate probability for championship markets."""
        
        team = self._extract_team_name(market.question, sport_type)
        team_performance = self._get_team_performance(team, sport_type)
        
        # Base probability based on current standings and historical patterns
        base_prob = self._calculate_championship_base_probability(team_performance, sport_type)
        
        # Create evidence list
        evidence_list = []
        
        # Add current season performance
        if team_performance:
            performance_signal = self._evaluate_championship_performance(team_performance, sport_type)
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=performance_signal > 0,
                strength=min(abs(performance_signal), 1.0),
                confidence=0.8,
                description=f"Season performance: {team_performance.win_percentage:.1%} win rate, {team_performance.recent_form} form",
                source="season_performance"
            ))
            
        # Add injury/health evidence
        injury_impact = self._assess_injury_impact(team, sport_type)
        if abs(injury_impact) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=injury_impact < 0,  # Fewer injuries = better championship odds
                strength=min(abs(injury_impact), 1.0),
                confidence=0.7,
                description=f"Injury situation: {'concerning' if injury_impact > 0 else 'healthy'} roster",
                source="injury_analysis"
            ))
            
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="sports"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
            
    def _calculate_retirement_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle],
        sport_type: SportType
    ) -> ProbabilityDistribution:
        """Calculate probability for player retirement markets."""
        
        player = self._extract_player_name(market.question)
        player_stats = self._get_player_stats(player, sport_type)
        
        # Base probability based on age and performance trends
        base_prob = self._calculate_retirement_base_probability(player_stats, sport_type)
        
        # Create evidence list
        evidence_list = []
        
        # Add age and performance evidence
        if player_stats:
            age_signal = self._evaluate_retirement_age_factor(player_stats, sport_type)
            performance_signal = self._evaluate_retirement_performance_factor(player_stats)
            
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=age_signal > 0,
                strength=min(abs(age_signal), 1.0),
                confidence=0.8,
                description=f"Age factor: {player_stats.age} years old, {player_stats.recent_performance_trend} performance",
                source="player_analysis"
            ))
            
        # Add news/statement evidence
        retirement_sentiment = self._analyze_retirement_news_sentiment(news_articles, player)
        if abs(retirement_sentiment) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=retirement_sentiment > 0,
                strength=min(abs(retirement_sentiment), 1.0),
                confidence=0.7,
                description=f"Media coverage suggests {'retirement consideration' if retirement_sentiment > 0 else 'continued play'}",
                source="retirement_media"
            ))
            
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="sports"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
            
    def _extract_team_name(self, question: str, sport_type: SportType) -> Optional[str]:
        """Extract team name from market question."""
        question_lower = question.lower()
        
        if sport_type == SportType.NFL:
            teams = self._get_nfl_teams()
        elif sport_type == SportType.NBA:
            teams = self._get_nba_teams()
        elif sport_type == SportType.MLB:
            teams = self._get_mlb_teams()
        elif sport_type == SportType.NHL:
            teams = self._get_nhl_teams()
        else:
            teams = []
            
        for team in teams:
            if team.lower() in question_lower:
                return team
                
        return None
        
    def _extract_player_name(self, question: str) -> Optional[str]:
        """Extract player name from market question."""
        # Common player name patterns - fixed to handle names like "LeBron James"
        player_patterns = [
            r"will ([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+)",  # Matches "LeBron James"
            r"([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+) retire",
            r"([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+) will",
            r"([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+) to",  # "LeBron James to win"
        ]
        
        for pattern in player_patterns:
            match = re.search(pattern, question)
            if match:
                return match.group(1)
                
        return None
        
    def _get_team_performance(self, team: Optional[str], sport_type: SportType) -> Optional[TeamPerformance]:
        """
        Get team performance data.
        Note: Placeholder - in production would use ESPN API or similar.
        """
        if not team:
            return None
            
        # Simulate team performance data
        team_data = {
            "Chiefs": TeamPerformance(
                team_name="Kansas City Chiefs",
                wins=11, losses=3, win_percentage=0.786,
                points_for=28.5, points_against=18.2,
                strength_of_schedule=0.52, injuries_key_players=1,
                recent_form="hot", playoff_position=1, championship_odds=0.15
            ),
            "Jets": TeamPerformance(
                team_name="New York Jets",
                wins=4, losses=10, win_percentage=0.286,
                points_for=18.1, points_against=24.8,
                strength_of_schedule=0.48, injuries_key_players=4,
                recent_form="cold", playoff_position=None, championship_odds=0.001
            ),
            "Lakers": TeamPerformance(
                team_name="Los Angeles Lakers",
                wins=25, losses=20, win_percentage=0.556,
                points_for=115.2, points_against=112.8,
                strength_of_schedule=0.51, injuries_key_players=2,
                recent_form="average", playoff_position=8, championship_odds=0.05
            )
        }
        
        return team_data.get(team)
        
    def _get_coaching_data(self, team: Optional[str], sport_type: SportType) -> Optional[CoachingData]:
        """Get coaching data for a team."""
        if not team:
            return None
            
        # Simulate coaching data
        coaching_data = {
            "Chiefs": CoachingData(
                coach_name="Andy Reid",
                years_with_team=11, career_win_percentage=0.648,
                playoff_appearances=8, championships=1,
                contract_years_remaining=3, recent_pressure="low",
                ownership_support="strong"
            ),
            "Jets": CoachingData(
                coach_name="Robert Saleh",
                years_with_team=3, career_win_percentage=0.318,
                playoff_appearances=0, championships=0,
                contract_years_remaining=1, recent_pressure="high",
                ownership_support="weak"
            )
        }
        
        return coaching_data.get(team)
        
    def _get_player_stats(self, player: Optional[str], sport_type: SportType) -> Optional[PlayerStats]:
        """Get player statistics."""
        if not player:
            return None
            
        # Simulate player data
        player_data = {
            "Tom Brady": PlayerStats(
                player_name="Tom Brady",
                age=46, position="QB", games_played=16,
                performance_rating=85, injury_history=["shoulder", "knee"],
                contract_years_remaining=0, recent_performance_trend="declining"
            ),
            "LeBron James": PlayerStats(
                player_name="LeBron James",
                age=39, position="SF", games_played=70,
                performance_rating=88, injury_history=["ankle", "groin"],
                contract_years_remaining=1, recent_performance_trend="stable"
            )
        }
        
        return player_data.get(player)
        
    def _calculate_coaching_change_base_probability(
        self, 
        team_performance: Optional[TeamPerformance],
        coaching_data: Optional[CoachingData],
        sport_type: SportType
    ) -> float:
        """Calculate base probability for coaching change."""
        
        # League-specific base rates
        base_rates = {
            SportType.NFL: 0.20,  # ~6-7 coaches fired per year out of 32
            SportType.NBA: 0.25,  # Higher turnover in NBA
            SportType.MLB: 0.15,  # More patient with managers
            SportType.NHL: 0.22   # Similar to NFL
        }
        
        base_prob = base_rates.get(sport_type, 0.20)
        
        # Adjust based on team performance
        if team_performance:
            if team_performance.win_percentage < 0.3:
                base_prob *= 3.0  # Very poor performance
            elif team_performance.win_percentage < 0.4:
                base_prob *= 2.0  # Poor performance
            elif team_performance.win_percentage > 0.7:
                base_prob *= 0.3  # Good performance protects coaches
                
        # Adjust based on coaching situation
        if coaching_data:
            if coaching_data.years_with_team <= 2:
                base_prob *= 0.7  # New coaches get more time
            elif coaching_data.years_with_team >= 8:
                base_prob *= 0.5  # Veteran coaches have more job security
                
            if coaching_data.championships > 0:
                base_prob *= 0.4  # Championship coaches are safer
                
        return min(0.95, base_prob)
        
    def _evaluate_team_performance_for_coaching_change(self, team_performance: TeamPerformance) -> float:
        """Evaluate how team performance affects coaching change probability."""
        signal = 0.0
        
        # Win percentage impact
        if team_performance.win_percentage < 0.25:
            signal += 0.8  # Very strong signal for change
        elif team_performance.win_percentage < 0.4:
            signal += 0.5  # Strong signal
        elif team_performance.win_percentage > 0.75:
            signal -= 0.6  # Strong protection
            
        # Recent form impact
        if team_performance.recent_form == "cold":
            signal += 0.3
        elif team_performance.recent_form == "hot":
            signal -= 0.2
            
        # Playoff position impact
        if team_performance.playoff_position is None:
            signal += 0.2  # Missing playoffs increases risk
        elif team_performance.playoff_position <= 3:
            signal -= 0.3  # High seed protects coach
            
        return max(-1.0, min(1.0, signal))
        
    def _evaluate_coaching_tenure_risk(self, coaching_data: CoachingData) -> float:
        """Evaluate coaching tenure risk factors."""
        signal = 0.0
        
        # Pressure level
        pressure_signals = {"high": 0.4, "medium": 0.1, "low": -0.2}
        signal += pressure_signals.get(coaching_data.recent_pressure, 0.0)
        
        # Ownership support
        support_signals = {"weak": 0.5, "moderate": 0.0, "strong": -0.3}
        signal += support_signals.get(coaching_data.ownership_support, 0.0)
        
        # Contract situation
        if coaching_data.contract_years_remaining <= 1:
            signal += 0.3  # Lame duck coaches more vulnerable
            
        return max(-1.0, min(1.0, signal))
        
    def _calculate_championship_base_probability(
        self, 
        team_performance: Optional[TeamPerformance],
        sport_type: SportType
    ) -> float:
        """Calculate base championship probability."""
        
        # League-specific calculations
        if sport_type == SportType.NFL:
            base_prob = 1.0 / 32  # 32 teams
        elif sport_type == SportType.NBA:
            base_prob = 1.0 / 30  # 30 teams
        elif sport_type == SportType.MLB:
            base_prob = 1.0 / 30  # 30 teams
        elif sport_type == SportType.NHL:
            base_prob = 1.0 / 32  # 32 teams
        else:
            base_prob = 1.0 / 30
            
        # Adjust based on current performance
        if team_performance:
            if team_performance.championship_odds:
                # Use market odds if available
                return team_performance.championship_odds
                
            # Adjust based on win percentage and playoff position
            performance_multiplier = 1.0
            
            if team_performance.win_percentage > 0.8:
                performance_multiplier = 8.0  # Elite teams
            elif team_performance.win_percentage > 0.7:
                performance_multiplier = 4.0  # Very good teams
            elif team_performance.win_percentage > 0.6:
                performance_multiplier = 2.0  # Good teams
            elif team_performance.win_percentage < 0.4:
                performance_multiplier = 0.1  # Poor teams very unlikely
                
            base_prob *= performance_multiplier
            
        return min(0.8, base_prob)
        
    def _calculate_retirement_base_probability(
        self, 
        player_stats: Optional[PlayerStats],
        sport_type: SportType
    ) -> float:
        """Calculate base retirement probability."""
        
        if not player_stats:
            return 0.15  # Default retirement rate
            
        # Age-based baseline
        age = player_stats.age
        
        if sport_type in [SportType.NFL, SportType.NHL]:
            # More physical sports, earlier retirement
            if age < 28:
                base_prob = 0.02
            elif age < 32:
                base_prob = 0.05
            elif age < 35:
                base_prob = 0.15
            elif age < 38:
                base_prob = 0.35
            else:
                base_prob = 0.60
        else:
            # NBA, MLB - longer careers possible
            if age < 30:
                base_prob = 0.02
            elif age < 34:
                base_prob = 0.05
            elif age < 37:
                base_prob = 0.15
            elif age < 40:
                base_prob = 0.35
            else:
                base_prob = 0.55
                
        # Adjust for performance trends
        if player_stats.recent_performance_trend == "declining":
            base_prob *= 1.5
        elif player_stats.recent_performance_trend == "improving":
            base_prob *= 0.6
            
        # Contract situation
        if player_stats.contract_years_remaining == 0:
            base_prob *= 1.3  # Easier to retire without contract
            
        return min(0.95, base_prob)
        
    def _analyze_coaching_news_sentiment(self, news_articles: List[NewsArticle], team: Optional[str]) -> float:
        """Analyze news sentiment around coaching situation."""
        if not news_articles or not team:
            return 0.0
            
        negative_terms = [
            "fire", "fired", "hot seat", "pressure", "criticism", "frustrated",
            "disappointed", "change needed", "underperforming", "losing confidence"
        ]
        
        positive_terms = [
            "support", "backing", "confidence", "extension", "praise",
            "improvement", "development", "trust", "committed"
        ]
        
        sentiment_scores = []
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            if team.lower() in text or "coach" in text:
                positive_count = sum(1 for term in positive_terms if term in text)
                negative_count = sum(1 for term in negative_terms if term in text)
                
                if positive_count > 0 or negative_count > 0:
                    # Positive sentiment = bad for coaching change probability
                    sentiment = (negative_count - positive_count) / (positive_count + negative_count)
                    sentiment_scores.append(sentiment)
                    
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _analyze_retirement_news_sentiment(self, news_articles: List[NewsArticle], player: Optional[str]) -> float:
        """Analyze news sentiment around player retirement."""
        if not news_articles or not player:
            return 0.0
            
        retirement_terms = [
            "retire", "retirement", "final season", "hanging up", "calling it quits",
            "considering retirement", "thinking about", "legacy", "farewell"
        ]
        
        continuation_terms = [
            "return", "coming back", "another season", "not retiring", "continue playing",
            "still got it", "few more years", "not done yet"
        ]
        
        sentiment_scores = []
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            if player.lower() in text:
                retirement_count = sum(1 for term in retirement_terms if term in text)
                continuation_count = sum(1 for term in continuation_terms if term in text)
                
                if retirement_count > 0 or continuation_count > 0:
                    sentiment = (retirement_count - continuation_count) / (retirement_count + continuation_count)
                    sentiment_scores.append(sentiment)
                    
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _get_nfl_teams(self) -> List[str]:
        """Get list of NFL team names."""
        return [
            "Chiefs", "Bills", "Bengals", "Ravens", "Browns", "Steelers", "Titans", "Colts", 
            "Texans", "Jaguars", "Chargers", "Raiders", "Broncos", "Cowboys", "Giants", 
            "Eagles", "Commanders", "Packers", "Bears", "Lions", "Vikings", "Falcons", 
            "Panthers", "Saints", "Buccaneers", "Cardinals", "Rams", "49ers", "Seahawks",
            "Jets", "Dolphins", "Patriots"
        ]
        
    def _get_nba_teams(self) -> List[str]:
        """Get list of NBA team names."""
        return [
            "Lakers", "Warriors", "Celtics", "Heat", "Nets", "Knicks", "76ers", "Bucks",
            "Bulls", "Cavaliers", "Pistons", "Pacers", "Hawks", "Hornets", "Magic", "Wizards",
            "Raptors", "Nuggets", "Timberwolves", "Thunder", "Trail Blazers", "Jazz", "Suns",
            "Kings", "Clippers", "Mavericks", "Rockets", "Grizzlies", "Pelicans", "Spurs"
        ]
        
    def _get_mlb_teams(self) -> List[str]:
        """Get list of MLB team names."""
        return [
            "Yankees", "Red Sox", "Blue Jays", "Orioles", "Rays", "White Sox", "Indians", 
            "Tigers", "Royals", "Twins", "Astros", "Angels", "Athletics", "Mariners", "Rangers",
            "Braves", "Marlins", "Mets", "Phillies", "Nationals", "Cubs", "Reds", "Brewers",
            "Pirates", "Cardinals", "Diamondbacks", "Rockies", "Dodgers", "Padres", "Giants"
        ]
        
    def _get_nhl_teams(self) -> List[str]:
        """Get list of NHL team names."""
        return [
            "Bruins", "Sabres", "Red Wings", "Panthers", "Canadiens", "Senators", "Lightning",
            "Maple Leafs", "Hurricanes", "Blue Jackets", "Devils", "Islanders", "Rangers",
            "Flyers", "Penguins", "Capitals", "Blackhawks", "Avalanche", "Stars", "Wild",
            "Predators", "Blues", "Jets", "Flames", "Oilers", "Canucks", "Ducks", "Kings",
            "Sharks", "Coyotes", "Golden Knights", "Kraken"
        ]
        
    # Additional helper methods for other event types
    def _calculate_trade_probability(self, market: Market, news_articles: List[NewsArticle], sport_type: SportType) -> ProbabilityDistribution:
        """Calculate probability for trade markets."""
        base_prob = 0.25  # Generic trade probability
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
        
    def _calculate_playoff_probability(self, market: Market, news_articles: List[NewsArticle], sport_type: SportType) -> ProbabilityDistribution:
        """Calculate probability for playoff appearance markets."""
        base_prob = 0.40  # Varies by league structure
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
        
    def _calculate_award_probability(self, market: Market, news_articles: List[NewsArticle], sport_type: SportType) -> ProbabilityDistribution:
        """Calculate probability for award markets."""
        base_prob = 0.15  # Depends on number of candidates
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
        
    def _calculate_general_sports(self, market: Market, news_articles: List[NewsArticle], sport_type: SportType) -> ProbabilityDistribution:
        """Fallback for general sports markets."""
        base_prob = 0.35  # General sports baseline
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.4)
        
    def _evaluate_championship_performance(self, team_performance: TeamPerformance, sport_type: SportType) -> float:
        """Evaluate team performance for championship probability."""
        signal = 0.0
        
        # Win percentage signal
        if team_performance.win_percentage > 0.75:
            signal += 0.6
        elif team_performance.win_percentage > 0.65:
            signal += 0.3
        elif team_performance.win_percentage < 0.45:
            signal -= 0.6
            
        # Recent form
        form_signals = {"hot": 0.3, "average": 0.0, "cold": -0.4}
        signal += form_signals.get(team_performance.recent_form, 0.0)
        
        return max(-1.0, min(1.0, signal))
        
    def _assess_injury_impact(self, team: Optional[str], sport_type: SportType) -> float:
        """Assess impact of injuries on team performance."""
        if not team:
            return 0.0
            
        # Simulate injury assessment
        injury_impact = {
            "Chiefs": -0.1,  # Minor injuries
            "Jets": 0.4,     # Significant injuries
            "Lakers": 0.2    # Moderate injuries
        }
        
        return injury_impact.get(team, 0.0)
        
    def _evaluate_retirement_age_factor(self, player_stats: PlayerStats, sport_type: SportType) -> float:
        """Evaluate age factor for retirement probability."""
        age = player_stats.age
        
        if sport_type in [SportType.NFL, SportType.NHL]:
            if age >= 35:
                return 0.6
            elif age >= 32:
                return 0.3
            else:
                return -0.2
        else:  # NBA, MLB
            if age >= 38:
                return 0.6
            elif age >= 35:
                return 0.3
            else:
                return -0.2
                
    def _evaluate_retirement_performance_factor(self, player_stats: PlayerStats) -> float:
        """Evaluate performance factor for retirement."""
        if player_stats.recent_performance_trend == "declining":
            return 0.4
        elif player_stats.recent_performance_trend == "stable":
            return 0.0
        else:  # improving
            return -0.3
            
    def _get_historical_coaching_change_risk(self, sport_type: SportType, team_performance: Optional[TeamPerformance]) -> float:
        """Get historical coaching change risk patterns."""
        if not team_performance:
            return 0.0
            
        # Historical patterns suggest higher risk for underperforming teams
        if team_performance.win_percentage < 0.3:
            return 0.5
        elif team_performance.win_percentage > 0.7:
            return -0.3
        else:
            return 0.0
            
    def _load_team_databases(self) -> Dict:
        """Load team databases."""
        return {}
        
    def _load_historical_patterns(self) -> Dict:
        """Load historical sports patterns."""
        return {}
        
    def _load_coaching_change_patterns(self) -> Dict:
        """Load coaching change historical patterns."""
        return {}