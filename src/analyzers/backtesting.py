"""
Backtesting system for validating model predictions.

This module provides tools to evaluate prediction accuracy and calibration
by testing against historical market outcomes.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from statistics import mean, stdev
import math

from src.clients.polymarket.models import Market
from src.analyzers.models import MarketOpportunity

logger = logging.getLogger(__name__)


@dataclass
class BacktestPrediction:
    """A prediction made for backtesting."""
    
    condition_id: str
    question: str
    predicted_probability: float
    confidence: float
    recommended_position: str
    market_price: float
    prediction_date: datetime
    model_version: str
    
    # Outcome (filled when market resolves)
    actual_outcome: Optional[str] = None  # "YES", "NO", "INVALID"
    resolution_date: Optional[datetime] = None
    final_price: Optional[float] = None
    
    # Performance metrics (calculated)
    was_correct: Optional[bool] = None
    brier_score: Optional[float] = None  # Quadratic scoring rule
    log_score: Optional[float] = None    # Logarithmic scoring rule
    calibration_error: Optional[float] = None
    
    
@dataclass 
class BacktestMetrics:
    """Comprehensive backtesting metrics."""
    
    # Basic accuracy
    total_predictions: int
    correct_predictions: int
    accuracy: float
    
    # Probability calibration
    mean_predicted_probability: float
    actual_success_rate: float
    calibration_error: float
    
    # Scoring rules
    mean_brier_score: float
    mean_log_score: float
    
    # Confidence analysis
    high_confidence_accuracy: float  # Accuracy when confidence > 0.8
    low_confidence_accuracy: float   # Accuracy when confidence < 0.5
    confidence_correlation: float    # Correlation between confidence and accuracy
    
    # Market type breakdown
    accuracy_by_category: Dict[str, float]
    sample_sizes_by_category: Dict[str, int]
    
    # Time analysis
    accuracy_by_time_to_resolution: Dict[str, float]  # "0-7d", "7-30d", "30d+"
    
    # Edge case analysis
    extreme_predictions_accuracy: float  # Accuracy for predictions > 0.9 or < 0.1
    market_deviation_analysis: Dict[str, float]  # Accuracy by deviation from market
    

class BacktestingEngine:
    """
    Engine for running backtests and validating model performance.
    """
    
    def __init__(self, data_dir: str = "data/backtests"):
        """Initialize backtesting engine."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.predictions_file = self.data_dir / "predictions.jsonl"
        
    def record_prediction(
        self,
        market: Market,
        opportunity: MarketOpportunity,
        model_version: str = "current"
    ) -> None:
        """
        Record a prediction for later backtesting.
        
        Args:
            market: Market being predicted
            opportunity: Model's opportunity analysis
            model_version: Version identifier for the model
        """
        prediction = BacktestPrediction(
            condition_id=market.condition_id,
            question=market.question,
            predicted_probability=(
                opportunity.fair_yes_price if opportunity.recommended_position == "YES" 
                else opportunity.fair_no_price
            ),
            confidence=opportunity.score.confidence_score,
            recommended_position=opportunity.recommended_position,
            market_price=(
                opportunity.current_yes_price if opportunity.recommended_position == "YES"
                else opportunity.current_no_price
            ),
            prediction_date=datetime.now(),
            model_version=model_version
        )
        
        # Append to predictions file
        with open(self.predictions_file, "a") as f:
            f.write(json.dumps(asdict(prediction), default=str) + "\n")
            
        logger.info(f"Recorded prediction for {market.condition_id}")
        
    def update_outcome(
        self,
        condition_id: str,
        outcome: str,
        resolution_date: Optional[datetime] = None,
        final_price: Optional[float] = None
    ) -> None:
        """
        Update the outcome of a previously recorded prediction.
        
        Args:
            condition_id: Market condition ID
            outcome: "YES", "NO", or "INVALID"
            resolution_date: When market was resolved
            final_price: Final market price before resolution
        """
        predictions = self._load_predictions()
        updated = False
        
        for pred in predictions:
            if pred.condition_id == condition_id and pred.actual_outcome is None:
                pred.actual_outcome = outcome
                pred.resolution_date = resolution_date or datetime.now()
                pred.final_price = final_price
                
                # Calculate performance metrics
                self._calculate_prediction_metrics(pred)
                updated = True
                
        if updated:
            self._save_predictions(predictions)
            logger.info(f"Updated outcome for {condition_id}: {outcome}")
        else:
            logger.warning(f"No pending prediction found for {condition_id}")
            
    def run_backtest(
        self,
        model_version: Optional[str] = None,
        min_days_since_prediction: int = 0,
        category_filter: Optional[str] = None
    ) -> BacktestMetrics:
        """
        Run comprehensive backtest analysis.
        
        Args:
            model_version: Filter by model version
            min_days_since_prediction: Only include predictions made N+ days ago
            category_filter: Filter by market category
            
        Returns:
            BacktestMetrics: Comprehensive analysis results
        """
        predictions = self._load_predictions()
        
        # Filter predictions
        filtered_predictions = []
        cutoff_date = datetime.now() - timedelta(days=min_days_since_prediction)
        
        for pred in predictions:
            # Skip unresolved predictions
            if pred.actual_outcome is None:
                continue
                
            # Apply filters
            if model_version and pred.model_version != model_version:
                continue
            if pred.prediction_date > cutoff_date:
                continue
            # Note: category_filter would need market data to implement
                
            filtered_predictions.append(pred)
            
        if not filtered_predictions:
            logger.warning("No predictions found matching criteria")
            return self._empty_metrics()
            
        logger.info(f"Analyzing {len(filtered_predictions)} predictions")
        
        # Calculate comprehensive metrics
        return self._calculate_backtest_metrics(filtered_predictions)
        
    def _load_predictions(self) -> List[BacktestPrediction]:
        """Load all predictions from storage."""
        predictions = []
        
        if not self.predictions_file.exists():
            return predictions
            
        with open(self.predictions_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    # Convert datetime strings back to datetime objects
                    if data.get("prediction_date"):
                        data["prediction_date"] = datetime.fromisoformat(data["prediction_date"])
                    if data.get("resolution_date"):
                        data["resolution_date"] = datetime.fromisoformat(data["resolution_date"])
                    predictions.append(BacktestPrediction(**data))
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Skipping invalid prediction line: {e}")
                    
        return predictions
        
    def _save_predictions(self, predictions: List[BacktestPrediction]) -> None:
        """Save all predictions to storage."""
        with open(self.predictions_file, "w") as f:
            for pred in predictions:
                f.write(json.dumps(asdict(pred), default=str) + "\n")
                
    def _calculate_prediction_metrics(self, prediction: BacktestPrediction) -> None:
        """Calculate performance metrics for a single prediction."""
        if prediction.actual_outcome is None:
            return
            
        # Determine if prediction was correct
        if prediction.actual_outcome == "INVALID":
            prediction.was_correct = None  # Don't count invalid markets
            return
            
        # Check if recommended position matched outcome
        position_correct = (
            (prediction.recommended_position == "YES" and prediction.actual_outcome == "YES") or
            (prediction.recommended_position == "NO" and prediction.actual_outcome == "NO")
        )
        prediction.was_correct = position_correct
        
        # Calculate probability for scoring rules
        if prediction.recommended_position == "YES":
            predicted_prob = prediction.predicted_probability
        else:
            predicted_prob = 1.0 - prediction.predicted_probability
            
        actual_outcome_binary = 1.0 if prediction.actual_outcome == "YES" else 0.0
        
        # Brier Score: (predicted_prob - actual_outcome)^2
        prediction.brier_score = (predicted_prob - actual_outcome_binary) ** 2
        
        # Log Score: log(predicted_prob) if correct, log(1-predicted_prob) if wrong
        # Clamp probabilities to avoid log(0)
        clamped_prob = max(0.001, min(0.999, predicted_prob))
        if actual_outcome_binary == 1.0:
            prediction.log_score = math.log(clamped_prob)
        else:
            prediction.log_score = math.log(1.0 - clamped_prob)
            
        # Calibration error: |predicted_prob - actual_outcome|
        prediction.calibration_error = abs(predicted_prob - actual_outcome_binary)
        
    def _calculate_backtest_metrics(self, predictions: List[BacktestPrediction]) -> BacktestMetrics:
        """Calculate comprehensive metrics from predictions."""
        # Filter out invalid outcomes for most metrics
        valid_predictions = [p for p in predictions if p.was_correct is not None]
        
        if not valid_predictions:
            return self._empty_metrics()
            
        # Basic accuracy
        correct_count = sum(1 for p in valid_predictions if p.was_correct)
        accuracy = correct_count / len(valid_predictions)
        
        # Probability calibration
        predicted_probs = []
        actual_outcomes = []
        
        for pred in valid_predictions:
            if pred.recommended_position == "YES":
                predicted_probs.append(pred.predicted_probability)
            else:
                predicted_probs.append(1.0 - pred.predicted_probability)
            actual_outcomes.append(1.0 if pred.actual_outcome == "YES" else 0.0)
            
        mean_predicted = mean(predicted_probs)
        actual_success_rate = mean(actual_outcomes)
        calibration_error = abs(mean_predicted - actual_success_rate)
        
        # Scoring rules
        brier_scores = [p.brier_score for p in valid_predictions if p.brier_score is not None]
        log_scores = [p.log_score for p in valid_predictions if p.log_score is not None]
        
        mean_brier = mean(brier_scores) if brier_scores else 0.0
        mean_log = mean(log_scores) if log_scores else 0.0
        
        # Confidence analysis
        high_conf_preds = [p for p in valid_predictions if p.confidence > 0.8]
        low_conf_preds = [p for p in valid_predictions if p.confidence < 0.5]
        
        high_conf_accuracy = (
            sum(1 for p in high_conf_preds if p.was_correct) / len(high_conf_preds)
            if high_conf_preds else 0.0
        )
        
        low_conf_accuracy = (
            sum(1 for p in low_conf_preds if p.was_correct) / len(low_conf_preds)
            if low_conf_preds else 0.0
        )
        
        # Confidence correlation (simplified)
        confidence_correlation = self._calculate_confidence_correlation(valid_predictions)
        
        # Extreme predictions analysis
        extreme_preds = [
            p for p in valid_predictions 
            if p.predicted_probability < 0.1 or p.predicted_probability > 0.9
        ]
        extreme_accuracy = (
            sum(1 for p in extreme_preds if p.was_correct) / len(extreme_preds)
            if extreme_preds else 0.0
        )
        
        # Market deviation analysis
        market_deviation_analysis = self._analyze_market_deviations(valid_predictions)
        
        # Time to resolution analysis  
        time_analysis = self._analyze_time_to_resolution(valid_predictions)
        
        return BacktestMetrics(
            total_predictions=len(valid_predictions),
            correct_predictions=correct_count,
            accuracy=accuracy,
            mean_predicted_probability=mean_predicted,
            actual_success_rate=actual_success_rate,
            calibration_error=calibration_error,
            mean_brier_score=mean_brier,
            mean_log_score=mean_log,
            high_confidence_accuracy=high_conf_accuracy,
            low_confidence_accuracy=low_conf_accuracy,
            confidence_correlation=confidence_correlation,
            accuracy_by_category={},  # Would need market metadata to implement
            sample_sizes_by_category={},
            accuracy_by_time_to_resolution=time_analysis,
            extreme_predictions_accuracy=extreme_accuracy,
            market_deviation_analysis=market_deviation_analysis
        )
        
    def _calculate_confidence_correlation(self, predictions: List[BacktestPrediction]) -> float:
        """Calculate correlation between confidence and accuracy."""
        if len(predictions) < 2:
            return 0.0
            
        # Simple correlation calculation
        confidences = [p.confidence for p in predictions]
        accuracies = [1.0 if p.was_correct else 0.0 for p in predictions]
        
        # Calculate Pearson correlation
        n = len(predictions)
        sum_conf = sum(confidences)
        sum_acc = sum(accuracies)
        sum_conf_acc = sum(c * a for c, a in zip(confidences, accuracies))
        sum_conf_sq = sum(c * c for c in confidences)
        sum_acc_sq = sum(a * a for a in accuracies)
        
        numerator = n * sum_conf_acc - sum_conf * sum_acc
        denominator = math.sqrt(
            (n * sum_conf_sq - sum_conf * sum_conf) *
            (n * sum_acc_sq - sum_acc * sum_acc)
        )
        
        return numerator / denominator if denominator > 0 else 0.0
        
    def _analyze_market_deviations(self, predictions: List[BacktestPrediction]) -> Dict[str, float]:
        """Analyze accuracy by deviation from market price."""
        deviations = {
            "small_deviation": [],  # < 2x market price
            "medium_deviation": [], # 2-5x market price  
            "large_deviation": []   # > 5x market price
        }
        
        for pred in predictions:
            if pred.market_price <= 0:
                continue
                
            # Calculate how much our prediction deviated from market
            if pred.recommended_position == "YES":
                our_price = pred.predicted_probability
            else:
                our_price = 1.0 - pred.predicted_probability
                
            deviation_ratio = our_price / pred.market_price
            
            if deviation_ratio < 2.0:
                deviations["small_deviation"].append(pred.was_correct)
            elif deviation_ratio < 5.0:
                deviations["medium_deviation"].append(pred.was_correct)
            else:
                deviations["large_deviation"].append(pred.was_correct)
                
        # Calculate accuracy for each deviation category
        result = {}
        for category, outcomes in deviations.items():
            if outcomes:
                result[category] = sum(outcomes) / len(outcomes)
            else:
                result[category] = 0.0
                
        return result
        
    def _analyze_time_to_resolution(self, predictions: List[BacktestPrediction]) -> Dict[str, float]:
        """Analyze accuracy by time between prediction and resolution."""
        time_buckets = {
            "0-7d": [],
            "7-30d": [], 
            "30d+": []
        }
        
        for pred in predictions:
            if not pred.resolution_date:
                continue
                
            days_to_resolution = (pred.resolution_date - pred.prediction_date).days
            
            if days_to_resolution <= 7:
                time_buckets["0-7d"].append(pred.was_correct)
            elif days_to_resolution <= 30:
                time_buckets["7-30d"].append(pred.was_correct)
            else:
                time_buckets["30d+"].append(pred.was_correct)
                
        # Calculate accuracy for each time bucket
        result = {}
        for bucket, outcomes in time_buckets.items():
            if outcomes:
                result[bucket] = sum(outcomes) / len(outcomes)
            else:
                result[bucket] = 0.0
                
        return result
        
    def _empty_metrics(self) -> BacktestMetrics:
        """Return empty metrics when no data available."""
        return BacktestMetrics(
            total_predictions=0,
            correct_predictions=0,
            accuracy=0.0,
            mean_predicted_probability=0.0,
            actual_success_rate=0.0,
            calibration_error=0.0,
            mean_brier_score=0.0,
            mean_log_score=0.0,
            high_confidence_accuracy=0.0,
            low_confidence_accuracy=0.0,
            confidence_correlation=0.0,
            accuracy_by_category={},
            sample_sizes_by_category={},
            accuracy_by_time_to_resolution={},
            extreme_predictions_accuracy=0.0,
            market_deviation_analysis={}
        )
        
    def generate_report(self, metrics: BacktestMetrics) -> str:
        """Generate human-readable backtest report."""
        if metrics.total_predictions == 0:
            return "📊 **Backtest Report: No Data Available**"
            
        lines = []
        lines.append("📊 **Backtest Performance Report**")
        lines.append("=" * 50)
        lines.append("")
        
        # Basic performance
        lines.append("📈 **Overall Performance:**")
        lines.append(f"• Total Predictions: {metrics.total_predictions}")
        lines.append(f"• Accuracy: {metrics.accuracy:.1%}")
        lines.append(f"• Correct Predictions: {metrics.correct_predictions}")
        lines.append("")
        
        # Calibration
        lines.append("🎯 **Calibration Analysis:**")
        lines.append(f"• Average Predicted Probability: {metrics.mean_predicted_probability:.1%}")
        lines.append(f"• Actual Success Rate: {metrics.actual_success_rate:.1%}")
        lines.append(f"• Calibration Error: {metrics.calibration_error:.1%}")
        lines.append("")
        
        # Scoring rules
        lines.append("📏 **Scoring Metrics:**")
        lines.append(f"• Brier Score: {metrics.mean_brier_score:.3f} (lower is better)")
        lines.append(f"• Log Score: {metrics.mean_log_score:.3f} (higher is better)")
        lines.append("")
        
        # Confidence analysis
        lines.append("🔍 **Confidence Analysis:**")
        lines.append(f"• High Confidence Accuracy (>80%): {metrics.high_confidence_accuracy:.1%}")
        lines.append(f"• Low Confidence Accuracy (<50%): {metrics.low_confidence_accuracy:.1%}")
        lines.append(f"• Confidence-Accuracy Correlation: {metrics.confidence_correlation:.3f}")
        lines.append("")
        
        # Special cases
        lines.append("⚡ **Edge Case Analysis:**")
        lines.append(f"• Extreme Predictions Accuracy: {metrics.extreme_predictions_accuracy:.1%}")
        
        if metrics.market_deviation_analysis:
            lines.append("")
            lines.append("📊 **Market Deviation Analysis:**")
            for category, accuracy in metrics.market_deviation_analysis.items():
                lines.append(f"• {category.replace('_', ' ').title()}: {accuracy:.1%}")
                
        if metrics.accuracy_by_time_to_resolution:
            lines.append("")
            lines.append("⏰ **Time to Resolution Analysis:**")
            for timeframe, accuracy in metrics.accuracy_by_time_to_resolution.items():
                lines.append(f"• {timeframe}: {accuracy:.1%}")
                
        return "\n".join(lines)