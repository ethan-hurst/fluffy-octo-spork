"""
Advanced weather and climate event prediction modeling.
"""

import re
import logging
import statistics
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from src.clients.polymarket.models import Market
from src.clients.news.models import NewsArticle
from src.analyzers.bayesian_updater import BayesianUpdater, Evidence, EvidenceType, ProbabilityDistribution

logger = logging.getLogger(__name__)


class WeatherEventType(Enum):
    """Types of weather/climate events."""
    HURRICANE = "hurricane"
    TEMPERATURE_RECORD = "temperature_record"
    RAINFALL = "rainfall"
    DROUGHT = "drought"
    SNOWFALL = "snowfall"
    TORNADO = "tornado"
    WILDFIRE = "wildfire"
    SEA_LEVEL = "sea_level"
    ICE_COVERAGE = "ice_coverage"
    CLIMATE_MILESTONE = "climate_milestone"


@dataclass
class HurricaneData:
    """Hurricane tracking and prediction data."""
    name: str
    current_category: int  # 1-5
    current_location: Tuple[float, float]  # lat, lon
    projected_path: List[Tuple[float, float]]
    wind_speed: float  # mph
    pressure: float  # mb
    movement_speed: float  # mph
    intensification_trend: str  # "strengthening", "stable", "weakening"
    model_consensus: float  # 0-1, agreement between models
    historical_analogs: List[str]  # Similar historical storms


@dataclass
class TemperatureData:
    """Temperature record data."""
    location: str
    current_temp: float
    record_temp: float
    record_date: datetime
    forecast_high: float
    forecast_confidence: float  # 0-1
    climate_trend: float  # degrees per decade
    urban_heat_island_effect: float  # adjustment factor
    el_nino_influence: float  # -1 to 1, negative for La Nina


@dataclass
class PrecipitationData:
    """Rainfall/snowfall data."""
    location: str
    current_total: float
    period_days: int
    normal_total: float
    record_total: float
    forecast_total: float
    soil_moisture: float  # 0-1, saturation level
    antecedent_conditions: str  # "dry", "normal", "wet"
    atmospheric_river: bool
    monsoon_strength: Optional[float]  # For applicable regions


@dataclass
class WildfireData:
    """Wildfire risk and activity data."""
    region: str
    current_fires: int
    acres_burned: float
    containment_percentage: float
    fuel_moisture: float  # percentage
    relative_humidity: float
    wind_speed: float
    temperature: float
    drought_index: float  # 0-5 scale
    red_flag_warnings: bool


@dataclass
class ClimateData:
    """Long-term climate milestone data."""
    metric: str  # "global_temp", "arctic_ice", "sea_level", etc.
    current_value: float
    milestone_value: float
    trend_rate: float  # per year
    acceleration: float  # change in trend rate
    model_projections: List[float]  # various model predictions
    confidence_interval: Tuple[float, float]


class WeatherClimateModel:
    """
    Advanced weather and climate event prediction model.
    """
    
    def __init__(self):
        """Initialize the weather/climate model."""
        self.bayesian_updater = BayesianUpdater()
        self.hurricane_models = self._load_hurricane_models()
        self.climate_models = self._load_climate_models()
        self.historical_patterns = self._load_historical_weather_patterns()
        
    def calculate_weather_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """
        Calculate probability for weather/climate markets.
        
        Args:
            market: Weather/climate market to analyze
            news_articles: Related news articles
            
        Returns:
            ProbabilityDistribution: Probability with uncertainty bounds
        """
        event_type = self._identify_weather_event_type(market)
        
        if event_type == WeatherEventType.HURRICANE:
            return self._calculate_hurricane_probability(market, news_articles)
        elif event_type == WeatherEventType.TEMPERATURE_RECORD:
            return self._calculate_temperature_record_probability(market, news_articles)
        elif event_type in [WeatherEventType.RAINFALL, WeatherEventType.SNOWFALL]:
            return self._calculate_precipitation_probability(market, news_articles, event_type)
        elif event_type == WeatherEventType.WILDFIRE:
            return self._calculate_wildfire_probability(market, news_articles)
        elif event_type == WeatherEventType.CLIMATE_MILESTONE:
            return self._calculate_climate_milestone_probability(market, news_articles)
        else:
            return self._calculate_general_weather(market, news_articles)
            
    def _identify_weather_event_type(self, market: Market) -> WeatherEventType:
        """Identify the type of weather event from market question."""
        question = market.question.lower()
        description = (market.description or "").lower()
        full_text = f"{question} {description}"
        
        if any(term in full_text for term in ["hurricane", "tropical storm", "cyclone", "typhoon"]):
            return WeatherEventType.HURRICANE
        elif any(term in full_text for term in ["temperature record", "hottest", "coldest", "degrees"]):
            return WeatherEventType.TEMPERATURE_RECORD
        elif any(term in full_text for term in ["rainfall", "rain", "precipitation", "inches of rain"]):
            return WeatherEventType.RAINFALL
        elif any(term in full_text for term in ["snow", "snowfall", "blizzard"]):
            return WeatherEventType.SNOWFALL
        elif any(term in full_text for term in ["wildfire", "acres burned", "fire season"]):
            return WeatherEventType.WILDFIRE
        elif any(term in full_text for term in ["drought", "dry conditions"]):
            return WeatherEventType.DROUGHT
        elif any(term in full_text for term in ["tornado", "tornadoes", "ef"]):
            return WeatherEventType.TORNADO
        elif any(term in full_text for term in ["sea level", "ice coverage", "arctic ice", "global temperature"]):
            return WeatherEventType.CLIMATE_MILESTONE
        else:
            return WeatherEventType.TEMPERATURE_RECORD  # Default
            
    def _calculate_hurricane_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for hurricane-related markets."""
        
        # Extract hurricane details
        hurricane_name, target_location = self._extract_hurricane_info(market.question)
        
        # Get current hurricane data
        hurricane_data = self._get_hurricane_data(hurricane_name)
        
        # Calculate base probability
        base_prob = self._calculate_hurricane_base_probability(hurricane_data, target_location)
        
        # Create evidence list
        evidence_list = []
        
        # Add model consensus evidence
        if hurricane_data:
            model_signal = self._evaluate_model_consensus(hurricane_data.model_consensus)
            if abs(model_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=model_signal > 0,
                    strength=min(abs(model_signal), 1.0),
                    confidence=0.9,
                    description=f"Forecast models {'agree' if model_signal > 0 else 'diverge'} on path",
                    source="weather_models"
                ))
                
        # Add intensification trend evidence
        if hurricane_data:
            intensity_signal = self._evaluate_intensification_trend(hurricane_data)
            if abs(intensity_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=intensity_signal > 0,
                    strength=min(abs(intensity_signal), 1.0),
                    confidence=0.8,
                    description=f"Storm is {hurricane_data.intensification_trend}",
                    source="nhc_analysis"
                ))
                
        # Add historical analog evidence
        if hurricane_data and hurricane_data.historical_analogs:
            analog_signal = self._evaluate_historical_analogs(
                hurricane_data.historical_analogs, target_location
            )
            if abs(analog_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=analog_signal > 0,
                    strength=min(abs(analog_signal), 1.0),
                    confidence=0.6,
                    description=f"Historical analogs {'support' if analog_signal > 0 else 'oppose'} impact",
                    source="historical_data"
                ))
                
        # Add news/expert commentary
        expert_sentiment = self._analyze_weather_expert_sentiment(news_articles, hurricane_name)
        if abs(expert_sentiment) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=expert_sentiment > 0,
                strength=min(abs(expert_sentiment), 1.0),
                confidence=0.5,
                description=f"Meteorologists {'concerned' if expert_sentiment > 0 else 'optimistic'}",
                source="weather_media"
            ))
        
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="weather"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.7)
            
    def _calculate_temperature_record_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for temperature record markets."""
        
        # Extract location and temperature details
        location, record_type, threshold = self._extract_temperature_info(market.question)
        
        # Get temperature data
        temp_data = self._get_temperature_data(location)
        
        # Calculate base probability
        base_prob = self._calculate_temperature_base_probability(temp_data, record_type, threshold)
        
        # Create evidence list
        evidence_list = []
        
        # Add forecast confidence
        if temp_data:
            forecast_signal = self._evaluate_temperature_forecast(temp_data, threshold)
            if abs(forecast_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=forecast_signal > 0,
                    strength=min(abs(forecast_signal), 1.0),
                    confidence=temp_data.forecast_confidence,
                    description=f"Forecast {'supports' if forecast_signal > 0 else 'opposes'} record",
                    source="weather_forecast"
                ))
                
        # Add climate trend evidence
        if temp_data:
            trend_signal = self._evaluate_climate_trend(temp_data, record_type)
            if abs(trend_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=trend_signal > 0,
                    strength=min(abs(trend_signal), 1.0),
                    confidence=0.7,
                    description=f"Climate trend {'favorable' if trend_signal > 0 else 'unfavorable'}",
                    source="climate_analysis"
                ))
                
        # Add El Niño/La Niña influence
        if temp_data and abs(temp_data.el_nino_influence) > 0.3:
            enso_signal = self._evaluate_enso_influence(temp_data.el_nino_influence, record_type)
            if abs(enso_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=enso_signal > 0,
                    strength=min(abs(enso_signal), 1.0),
                    confidence=0.6,
                    description=f"{'El Niño' if temp_data.el_nino_influence > 0 else 'La Niña'} influence",
                    source="enso_analysis"
                ))
        
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="weather"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
            
    def _calculate_precipitation_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle],
        event_type: WeatherEventType
    ) -> ProbabilityDistribution:
        """Calculate probability for precipitation (rain/snow) markets."""
        
        # Extract precipitation details
        location, amount, timeframe = self._extract_precipitation_info(market.question)
        
        # Get precipitation data
        precip_data = self._get_precipitation_data(location, event_type)
        
        # Calculate base probability
        base_prob = self._calculate_precipitation_base_probability(
            precip_data, amount, timeframe, event_type
        )
        
        # Create evidence list
        evidence_list = []
        
        # Add forecast evidence
        if precip_data:
            forecast_signal = self._evaluate_precipitation_forecast(precip_data, amount)
            if abs(forecast_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=forecast_signal > 0,
                    strength=min(abs(forecast_signal), 1.0),
                    confidence=0.8,
                    description=f"Forecast {'exceeds' if forecast_signal > 0 else 'below'} target",
                    source="precipitation_forecast"
                ))
                
        # Add soil moisture/antecedent conditions
        if precip_data:
            soil_signal = self._evaluate_soil_conditions(precip_data)
            if abs(soil_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=soil_signal > 0,
                    strength=min(abs(soil_signal), 1.0),
                    confidence=0.6,
                    description=f"Soil conditions {precip_data.antecedent_conditions}",
                    source="hydrological_analysis"
                ))
                
        # Add atmospheric river evidence (if applicable)
        if precip_data and precip_data.atmospheric_river:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=True,
                strength=0.8,
                confidence=0.9,
                description="Atmospheric river present",
                source="atmospheric_analysis"
            ))
        
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="weather"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
            
    def _calculate_wildfire_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for wildfire markets."""
        
        # Extract wildfire details
        region, acres_threshold = self._extract_wildfire_info(market.question)
        
        # Get wildfire data
        fire_data = self._get_wildfire_data(region)
        
        # Calculate base probability
        base_prob = self._calculate_wildfire_base_probability(fire_data, acres_threshold)
        
        # Create evidence list
        evidence_list = []
        
        # Add fuel moisture evidence
        if fire_data:
            fuel_signal = self._evaluate_fuel_conditions(fire_data)
            if abs(fuel_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=fuel_signal > 0,
                    strength=min(abs(fuel_signal), 1.0),
                    confidence=0.8,
                    description=f"Fuel moisture {'critical' if fuel_signal > 0 else 'adequate'}",
                    source="fire_weather_analysis"
                ))
                
        # Add weather conditions
        if fire_data:
            weather_signal = self._evaluate_fire_weather(fire_data)
            if abs(weather_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=weather_signal > 0,
                    strength=min(abs(weather_signal), 1.0),
                    confidence=0.7,
                    description=f"Fire weather {'extreme' if weather_signal > 0 else 'moderate'}",
                    source="weather_conditions"
                ))
                
        # Add red flag warnings
        if fire_data and fire_data.red_flag_warnings:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.EXPERT_OPINION,
                positive_signal=True,
                strength=0.7,
                confidence=0.9,
                description="Red flag warnings active",
                source="nws_warnings"
            ))
        
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="weather"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
            
    def _calculate_climate_milestone_probability(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Calculate probability for climate milestone markets."""
        
        # Extract climate metric details
        metric, milestone, timeframe = self._extract_climate_info(market.question)
        
        # Get climate data
        climate_data = self._get_climate_data(metric)
        
        # Calculate base probability
        base_prob = self._calculate_climate_base_probability(climate_data, milestone, timeframe)
        
        # Create evidence list
        evidence_list = []
        
        # Add trend analysis
        if climate_data:
            trend_signal = self._evaluate_climate_trend_strength(climate_data, milestone)
            if abs(trend_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=trend_signal > 0,
                    strength=min(abs(trend_signal), 1.0),
                    confidence=0.8,
                    description=f"Trend {'accelerating' if trend_signal > 0 else 'slowing'}",
                    source="climate_trend_analysis"
                ))
                
        # Add model consensus
        if climate_data and climate_data.model_projections:
            model_signal = self._evaluate_climate_models(
                climate_data.model_projections, milestone
            )
            if abs(model_signal) > 0.1:
                evidence_list.append(self.bayesian_updater.create_evidence(
                    evidence_type=EvidenceType.EXPERT_OPINION,
                    positive_signal=model_signal > 0,
                    strength=min(abs(model_signal), 1.0),
                    confidence=0.7,
                    description=f"Climate models {'agree' if model_signal > 0 else 'uncertain'}",
                    source="climate_models"
                ))
                
        # Add recent observations
        observation_signal = self._analyze_climate_observations(news_articles, metric)
        if abs(observation_signal) > 0.1:
            evidence_list.append(self.bayesian_updater.create_evidence(
                evidence_type=EvidenceType.NEWS_SENTIMENT,
                positive_signal=observation_signal > 0,
                strength=min(abs(observation_signal), 1.0),
                confidence=0.6,
                description=f"Recent observations {'concerning' if observation_signal > 0 else 'stable'}",
                source="climate_observations"
            ))
        
        if evidence_list:
            return self.bayesian_updater.update_probability(
                prior=base_prob,
                evidence_list=evidence_list,
                market_type="climate"
            )
        else:
            return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.6)
            
    def _extract_hurricane_info(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract hurricane name and target location."""
        # Pattern: "Will Hurricane [Name] hit [Location]"
        pattern = r"Hurricane (\w+).*?(hit|reach|impact|landfall).*?([A-Za-z\s]+)"
        match = re.search(pattern, question, re.IGNORECASE)
        
        if match:
            return match.group(1), match.group(3).strip()
            
        return None, None
        
    def _extract_temperature_info(self, question: str) -> Tuple[Optional[str], str, Optional[float]]:
        """Extract location, record type, and temperature threshold."""
        # Patterns for temperature records
        hot_pattern = r"([A-Za-z\s]+).*?(hottest|temperature.*?exceed|reach).*?(\d+)"
        cold_pattern = r"([A-Za-z\s]+).*?(coldest|temperature.*?below|drop).*?(\d+)"
        
        hot_match = re.search(hot_pattern, question, re.IGNORECASE)
        if hot_match:
            return hot_match.group(1).strip(), "hot", float(hot_match.group(3))
            
        cold_match = re.search(cold_pattern, question, re.IGNORECASE)
        if cold_match:
            return cold_match.group(1).strip(), "cold", float(cold_match.group(3))
            
        return None, "hot", None
        
    def _extract_precipitation_info(self, question: str) -> Tuple[Optional[str], Optional[float], Optional[int]]:
        """Extract location, amount, and timeframe for precipitation."""
        # Pattern: "[Location] receive [X] inches of [rain/snow] in [Y days]"
        pattern = r"([A-Za-z\s]+).*?(\d+\.?\d*)\s*inch.*?(rain|snow).*?(\d+)\s*day"
        match = re.search(pattern, question, re.IGNORECASE)
        
        if match:
            location = match.group(1).strip()
            amount = float(match.group(2))
            days = int(match.group(4))
            return location, amount, days
            
        return None, None, None
        
    def _extract_wildfire_info(self, question: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract region and acres threshold for wildfire markets."""
        # Pattern: "[Region] wildfire season burn [X] acres"
        pattern = r"([A-Za-z\s]+).*?burn.*?(\d+[,\d]*)\s*acres"
        match = re.search(pattern, question, re.IGNORECASE)
        
        if match:
            region = match.group(1).strip()
            acres = float(match.group(2).replace(',', ''))
            return region, acres
            
        return None, None
        
    def _extract_climate_info(self, question: str) -> Tuple[Optional[str], Optional[float], Optional[int]]:
        """Extract climate metric, milestone value, and timeframe."""
        # Common climate metrics
        metrics = {
            "global temperature": r"global.*?temperature.*?(\d+\.?\d*)",
            "arctic ice": r"arctic.*?ice.*?(\d+\.?\d*)",
            "sea level": r"sea.*?level.*?(\d+\.?\d*)",
            "co2": r"co2.*?(\d+)"
        }
        
        for metric, pattern in metrics.items():
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                milestone = float(match.group(1))
                
                # Extract timeframe
                year_match = re.search(r"(\d{4})", question)
                if year_match:
                    year = int(year_match.group(1))
                    years_remaining = year - datetime.now().year
                    return metric, milestone, years_remaining
                    
        return None, None, None
        
    def _calculate_hurricane_base_probability(
        self, 
        hurricane_data: Optional[HurricaneData],
        target_location: Optional[str]
    ) -> float:
        """Calculate base probability for hurricane impact."""
        
        if not hurricane_data or not target_location:
            return 0.20  # Default if no data
            
        # Base probability by category
        category_probs = {
            1: 0.15,  # Cat 1 hurricanes often change path
            2: 0.20,
            3: 0.25,  # Major hurricanes more predictable
            4: 0.30,
            5: 0.35   # Cat 5 storms have momentum
        }
        
        base_prob = category_probs.get(hurricane_data.current_category, 0.20)
        
        # Adjust for distance (simplified)
        # In reality, would calculate distance from current position to target
        if hurricane_data.movement_speed < 10:
            base_prob *= 0.8  # Slow storms less predictable
        elif hurricane_data.movement_speed > 20:
            base_prob *= 1.1  # Fast storms more direct
            
        return min(0.90, max(0.05, base_prob))
        
    def _calculate_temperature_base_probability(
        self, 
        temp_data: Optional[TemperatureData],
        record_type: str,
        threshold: Optional[float]
    ) -> float:
        """Calculate base probability for temperature records."""
        
        if not temp_data or not threshold:
            return 0.10  # Records are generally rare
            
        # Calculate how far threshold is from current record
        if record_type == "hot":
            gap = threshold - temp_data.record_temp
            if gap <= 0:
                return 0.05  # Already at or above record
            elif gap <= 2:
                return 0.15  # Close to record
            elif gap <= 5:
                return 0.08  # Significant gap
            else:
                return 0.02  # Very unlikely
        else:  # cold
            gap = temp_data.record_temp - threshold
            if gap <= 0:
                return 0.05
            elif gap <= 2:
                return 0.12
            elif gap <= 5:
                return 0.06
            else:
                return 0.02
                
    def _calculate_precipitation_base_probability(
        self, 
        precip_data: Optional[PrecipitationData],
        amount: Optional[float],
        timeframe: Optional[int],
        event_type: WeatherEventType
    ) -> float:
        """Calculate base probability for precipitation amounts."""
        
        if not precip_data or not amount or not timeframe:
            return 0.20
            
        # Calculate how unusual the amount is
        if precip_data.normal_total > 0:
            ratio = amount / precip_data.normal_total
            
            if ratio < 1.5:
                base_prob = 0.40  # Moderate excess
            elif ratio < 2.0:
                base_prob = 0.25  # Significant excess
            elif ratio < 3.0:
                base_prob = 0.10  # Major excess
            else:
                base_prob = 0.03  # Extreme event
                
            # Adjust for antecedent conditions
            if precip_data.antecedent_conditions == "wet":
                base_prob *= 1.3  # Easier to get high totals
            elif precip_data.antecedent_conditions == "dry":
                base_prob *= 0.7  # Harder to get high totals
                
            return min(0.85, max(0.02, base_prob))
        else:
            return 0.20
            
    def _calculate_wildfire_base_probability(
        self, 
        fire_data: Optional[WildfireData],
        acres_threshold: Optional[float]
    ) -> float:
        """Calculate base probability for wildfire acres burned."""
        
        if not fire_data or not acres_threshold:
            return 0.25
            
        # Base probability by drought index
        drought_probs = {
            0: 0.10,  # No drought
            1: 0.20,  # Abnormally dry
            2: 0.35,  # Moderate drought
            3: 0.50,  # Severe drought
            4: 0.65,  # Extreme drought
            5: 0.80   # Exceptional drought
        }
        
        base_prob = drought_probs.get(int(fire_data.drought_index), 0.30)
        
        # Adjust for current season progress
        if fire_data.acres_burned > 0 and acres_threshold > 0:
            progress_ratio = fire_data.acres_burned / acres_threshold
            
            if progress_ratio > 0.7:
                base_prob *= 1.5  # Already most of the way there
            elif progress_ratio > 0.5:
                base_prob *= 1.2
            elif progress_ratio < 0.2:
                base_prob *= 0.8  # Long way to go
                
        return min(0.90, max(0.05, base_prob))
        
    def _calculate_climate_base_probability(
        self, 
        climate_data: Optional[ClimateData],
        milestone: Optional[float],
        years_remaining: Optional[int]
    ) -> float:
        """Calculate base probability for climate milestones."""
        
        if not climate_data or not milestone or not years_remaining:
            return 0.30
            
        if years_remaining <= 0:
            return 0.01  # Already passed deadline
            
        # Calculate required rate to reach milestone
        gap = milestone - climate_data.current_value
        required_rate = gap / years_remaining
        
        # Compare to current trend
        if climate_data.trend_rate > 0:
            rate_ratio = required_rate / climate_data.trend_rate
            
            if rate_ratio < 0.5:
                base_prob = 0.80  # Well ahead of pace
            elif rate_ratio < 1.0:
                base_prob = 0.60  # On pace
            elif rate_ratio < 1.5:
                base_prob = 0.35  # Need acceleration
            elif rate_ratio < 2.0:
                base_prob = 0.15  # Significant acceleration needed
            else:
                base_prob = 0.05  # Unlikely acceleration
                
            # Adjust for acceleration trend
            if climate_data.acceleration > 0:
                base_prob *= 1.2  # Positive acceleration helps
            elif climate_data.acceleration < 0:
                base_prob *= 0.8  # Negative acceleration hurts
                
            return min(0.95, max(0.02, base_prob))
        else:
            return 0.30
            
    def _evaluate_model_consensus(self, consensus: float) -> float:
        """Evaluate hurricane model consensus strength."""
        if consensus > 0.8:
            return 0.6  # Strong agreement
        elif consensus > 0.6:
            return 0.3  # Good agreement
        elif consensus < 0.3:
            return -0.4  # Poor agreement
        else:
            return 0.0
            
    def _evaluate_intensification_trend(self, hurricane_data: HurricaneData) -> float:
        """Evaluate hurricane intensification trend."""
        if hurricane_data.intensification_trend == "strengthening":
            return 0.3  # Strengthening storms more dangerous
        elif hurricane_data.intensification_trend == "weakening":
            return -0.4  # Weakening storms less likely to impact
        else:
            return 0.0
            
    def _evaluate_historical_analogs(self, analogs: List[str], target: Optional[str]) -> float:
        """Evaluate historical hurricane analogs."""
        if not analogs or not target:
            return 0.0
            
        # In reality, would check if historical analogs hit the target
        # Simplified version
        if len(analogs) >= 3:
            return 0.4  # Multiple similar storms suggest pattern
        elif len(analogs) >= 1:
            return 0.2
        else:
            return 0.0
            
    def _evaluate_temperature_forecast(self, temp_data: TemperatureData, threshold: float) -> float:
        """Evaluate temperature forecast vs threshold."""
        gap = temp_data.forecast_high - threshold
        
        if gap > 5:
            return 0.7  # Forecast well above threshold
        elif gap > 2:
            return 0.4  # Forecast above threshold
        elif gap > 0:
            return 0.2  # Forecast slightly above
        elif gap > -2:
            return -0.2  # Forecast slightly below
        else:
            return -0.6  # Forecast well below
            
    def _evaluate_climate_trend(self, temp_data: TemperatureData, record_type: str) -> float:
        """Evaluate climate trend impact on temperature records."""
        if record_type == "hot":
            if temp_data.climate_trend > 0.3:  # Strong warming trend
                return 0.4
            elif temp_data.climate_trend > 0.1:
                return 0.2
            elif temp_data.climate_trend < -0.1:
                return -0.3
        else:  # cold records
            if temp_data.climate_trend > 0.3:  # Warming makes cold records harder
                return -0.4
            elif temp_data.climate_trend < -0.1:  # Cooling trend
                return 0.3
                
        return 0.0
        
    def _evaluate_enso_influence(self, enso: float, record_type: str) -> float:
        """Evaluate El Niño/La Niña influence."""
        if record_type == "hot":
            if enso > 0.5:  # Strong El Niño
                return 0.3  # Tends to increase temperatures
            elif enso < -0.5:  # Strong La Niña
                return -0.2  # Tends to decrease temperatures
        else:  # cold records
            if enso > 0.5:
                return -0.2
            elif enso < -0.5:
                return 0.2
                
        return 0.0
        
    def _evaluate_precipitation_forecast(self, precip_data: PrecipitationData, amount: float) -> float:
        """Evaluate precipitation forecast vs target."""
        if precip_data.forecast_total > amount * 1.2:
            return 0.6  # Forecast well above target
        elif precip_data.forecast_total > amount:
            return 0.3  # Forecast above target
        elif precip_data.forecast_total > amount * 0.8:
            return -0.2  # Forecast slightly below
        else:
            return -0.5  # Forecast well below
            
    def _evaluate_soil_conditions(self, precip_data: PrecipitationData) -> float:
        """Evaluate soil moisture impact on precipitation."""
        if precip_data.antecedent_conditions == "wet":
            return 0.3  # Wet soil enhances runoff/accumulation
        elif precip_data.antecedent_conditions == "dry":
            return -0.2  # Dry soil absorbs more
        else:
            return 0.0
            
    def _evaluate_fuel_conditions(self, fire_data: WildfireData) -> float:
        """Evaluate wildfire fuel conditions."""
        if fire_data.fuel_moisture < 10:
            return 0.7  # Critical fuel moisture
        elif fire_data.fuel_moisture < 15:
            return 0.4  # Low fuel moisture
        elif fire_data.fuel_moisture > 25:
            return -0.5  # High moisture reduces risk
        else:
            return 0.0
            
    def _evaluate_fire_weather(self, fire_data: WildfireData) -> float:
        """Evaluate fire weather conditions."""
        # Combine temperature, humidity, and wind
        risk_score = 0.0
        
        if fire_data.temperature > 95:
            risk_score += 0.3
        elif fire_data.temperature > 85:
            risk_score += 0.1
            
        if fire_data.relative_humidity < 20:
            risk_score += 0.3
        elif fire_data.relative_humidity < 30:
            risk_score += 0.1
            
        if fire_data.wind_speed > 25:
            risk_score += 0.4
        elif fire_data.wind_speed > 15:
            risk_score += 0.2
            
        return min(1.0, risk_score)
        
    def _evaluate_climate_trend_strength(self, climate_data: ClimateData, milestone: float) -> float:
        """Evaluate climate trend strength toward milestone."""
        gap = milestone - climate_data.current_value
        
        if climate_data.trend_rate > 0 and gap > 0:
            # Moving toward milestone
            if climate_data.acceleration > 0:
                return 0.5  # Accelerating toward milestone
            else:
                return 0.2  # Steady progress
        elif climate_data.trend_rate < 0 and gap > 0:
            return -0.6  # Moving away from milestone
        else:
            return 0.0
            
    def _evaluate_climate_models(self, projections: List[float], milestone: float) -> float:
        """Evaluate climate model consensus."""
        if not projections:
            return 0.0
            
        # Check how many models predict reaching milestone
        exceeding = sum(1 for p in projections if p >= milestone)
        ratio = exceeding / len(projections)
        
        if ratio > 0.8:
            return 0.6  # Strong model agreement
        elif ratio > 0.6:
            return 0.3  # Good agreement
        elif ratio < 0.2:
            return -0.5  # Models disagree
        else:
            return 0.0
            
    def _analyze_weather_expert_sentiment(self, news_articles: List[NewsArticle], event: Optional[str]) -> float:
        """Analyze meteorologist sentiment from news."""
        if not news_articles or not event:
            return 0.0
            
        concern_terms = ["dangerous", "catastrophic", "major", "significant", "threat", "risk"]
        calm_terms = ["weakening", "dissipating", "minimal", "unlikely", "low risk"]
        
        sentiment_scores = []
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            if event.lower() in text:
                concern_count = sum(1 for term in concern_terms if term in text)
                calm_count = sum(1 for term in calm_terms if term in text)
                
                if concern_count > 0 or calm_count > 0:
                    sentiment = (concern_count - calm_count) / (concern_count + calm_count)
                    sentiment_scores.append(sentiment)
                    
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _analyze_climate_observations(self, news_articles: List[NewsArticle], metric: Optional[str]) -> float:
        """Analyze recent climate observations from news."""
        if not news_articles or not metric:
            return 0.0
            
        acceleration_terms = ["faster than expected", "accelerating", "unprecedented", "record-breaking"]
        stability_terms = ["slowing", "stabilizing", "plateau", "pause"]
        
        sentiment_scores = []
        
        for article in news_articles:
            text = f"{article.title} {article.description or ''}".lower()
            
            if metric.lower() in text:
                accel_count = sum(1 for term in acceleration_terms if term in text)
                stable_count = sum(1 for term in stability_terms if term in text)
                
                if accel_count > 0 or stable_count > 0:
                    sentiment = (accel_count - stable_count) / (accel_count + stable_count)
                    sentiment_scores.append(sentiment)
                    
        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        
    def _calculate_general_weather(
        self, 
        market: Market, 
        news_articles: List[NewsArticle]
    ) -> ProbabilityDistribution:
        """Fallback for general weather markets."""
        base_prob = 0.30  # General weather baseline
        return self.bayesian_updater._create_distribution_from_point(base_prob, confidence=0.5)
        
    # Placeholder data loading methods
    def _load_hurricane_models(self) -> Dict:
        """Load hurricane forecast models."""
        return {}
        
    def _load_climate_models(self) -> Dict:
        """Load climate projection models."""
        return {}
        
    def _load_historical_weather_patterns(self) -> Dict:
        """Load historical weather patterns."""
        return {}
        
    def _get_hurricane_data(self, name: Optional[str]) -> Optional[HurricaneData]:
        """Get current hurricane data (placeholder)."""
        # In production, would fetch from NHC API
        return None
        
    def _get_temperature_data(self, location: Optional[str]) -> Optional[TemperatureData]:
        """Get temperature data (placeholder)."""
        # In production, would fetch from weather services
        return None
        
    def _get_precipitation_data(
        self, 
        location: Optional[str], 
        event_type: WeatherEventType
    ) -> Optional[PrecipitationData]:
        """Get precipitation data (placeholder)."""
        # In production, would fetch from weather services
        return None
        
    def _get_wildfire_data(self, region: Optional[str]) -> Optional[WildfireData]:
        """Get wildfire data (placeholder)."""
        # In production, would fetch from fire weather services
        return None
        
    def _get_climate_data(self, metric: Optional[str]) -> Optional[ClimateData]:
        """Get climate data (placeholder)."""
        # In production, would fetch from climate monitoring services
        return None