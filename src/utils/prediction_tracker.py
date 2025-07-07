"""
Prediction tracker for monitoring hit rate and performance over time.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

from src.analyzers.models import MarketOpportunity
from src.config.settings import settings

logger = logging.getLogger(__name__)


class PredictionRecord(BaseModel):
    """
    Record of a prediction made by the analyzer.
    """
    
    condition_id: str
    question: str
    predicted_position: str  # YES or NO
    predicted_probability: float
    current_market_price: float
    fair_value_price: float
    expected_return: float
    confidence_score: float
    overall_score: float
    risk_level: str
    reasoning: str
    
    # Tracking info
    prediction_date: datetime
    market_end_date: Optional[datetime] = None
    
    # Outcome (filled when market resolves)
    actual_outcome: Optional[str] = None  # YES, NO, or INVALID
    resolution_date: Optional[datetime] = None
    final_market_price: Optional[float] = None
    actual_return: Optional[float] = None
    prediction_correct: Optional[bool] = None
    
    @property
    def is_resolved(self) -> bool:
        """Check if prediction is resolved."""
        return self.actual_outcome is not None
        
    @property
    def days_to_resolution(self) -> Optional[int]:
        """Days from prediction to resolution."""
        if self.resolution_date:
            return (self.resolution_date - self.prediction_date).days
        return None


class PerformanceMetrics(BaseModel):
    """
    Performance metrics for predictions.
    """
    
    total_predictions: int
    resolved_predictions: int
    correct_predictions: int
    hit_rate: float
    
    average_confidence: float
    average_expected_return: float
    average_actual_return: float
    
    total_roi: float
    sharpe_ratio: Optional[float] = None
    
    predictions_by_risk: Dict[str, Dict[str, int]]  # risk_level -> {total, correct}
    predictions_by_confidence: Dict[str, Dict[str, int]]  # confidence_bucket -> {total, correct}
    
    last_updated: datetime


class PredictionTracker:
    """
    Tracks predictions and calculates performance metrics.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize prediction tracker.
        
        Args:
            data_dir: Directory to store tracking data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.predictions_file = self.data_dir / "predictions.jsonl"
        self.metrics_file = self.data_dir / "performance_metrics.json"
        
    def log_prediction(self, opportunity: MarketOpportunity) -> None:
        """
        Log a prediction for tracking.
        
        Args:
            opportunity: Market opportunity being predicted
        """
        # Only log high-confidence predictions
        if opportunity.score.confidence_score < 0.6:
            logger.debug(f"Skipping low-confidence prediction: {opportunity.condition_id}")
            return
            
        record = PredictionRecord(
            condition_id=opportunity.condition_id,
            question=opportunity.question,
            predicted_position=opportunity.recommended_position,
            predicted_probability=(
                opportunity.fair_yes_price if opportunity.recommended_position == "YES" 
                else opportunity.fair_no_price
            ),
            current_market_price=(
                opportunity.current_yes_price if opportunity.recommended_position == "YES"
                else opportunity.current_no_price
            ),
            fair_value_price=(
                opportunity.fair_yes_price if opportunity.recommended_position == "YES"
                else opportunity.fair_no_price
            ),
            expected_return=opportunity.expected_return,
            confidence_score=opportunity.score.confidence_score,
            overall_score=opportunity.score.overall_score,
            risk_level=opportunity.risk_level,
            reasoning=opportunity.reasoning,
            prediction_date=datetime.now(),
            market_end_date=opportunity.end_date
        )
        
        # Append to predictions file
        with open(self.predictions_file, "a") as f:
            f.write(record.model_dump_json() + "\n")
            
        logger.info(f"Logged prediction for {opportunity.condition_id}: {opportunity.recommended_position}")
        
    def update_outcome(
        self, 
        condition_id: str, 
        actual_outcome: str,
        final_price: float
    ) -> bool:
        """
        Update the outcome of a prediction.
        
        Args:
            condition_id: Market condition ID
            actual_outcome: Actual market outcome (YES, NO, or INVALID)
            final_price: Final market price
            
        Returns:
            bool: True if prediction was found and updated
        """
        predictions = self.load_predictions()
        updated = False
        
        for prediction in predictions:
            if (prediction.condition_id == condition_id and 
                not prediction.is_resolved):
                
                prediction.actual_outcome = actual_outcome
                prediction.resolution_date = datetime.now()
                prediction.final_market_price = final_price
                
                # Calculate if prediction was correct
                prediction.prediction_correct = (
                    prediction.predicted_position == actual_outcome
                )
                
                # Calculate actual return
                if prediction.prediction_correct:
                    if actual_outcome == "YES":
                        prediction.actual_return = (1.0 - prediction.current_market_price) / prediction.current_market_price * 100
                    else:
                        prediction.actual_return = (1.0 - prediction.current_market_price) / prediction.current_market_price * 100
                else:
                    prediction.actual_return = -prediction.current_market_price / prediction.current_market_price * 100
                    
                updated = True
                break
                
        if updated:
            self.save_predictions(predictions)
            self.update_metrics()
            logger.info(f"Updated outcome for {condition_id}: {actual_outcome}")
            
        return updated
        
    def load_predictions(self) -> List[PredictionRecord]:
        """
        Load all predictions from file.
        
        Returns:
            List[PredictionRecord]: List of all predictions
        """
        predictions = []
        
        if not self.predictions_file.exists():
            return predictions
            
        try:
            with open(self.predictions_file, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        predictions.append(PredictionRecord(**data))
        except Exception as e:
            logger.error(f"Error loading predictions: {e}")
            
        return predictions
        
    def save_predictions(self, predictions: List[PredictionRecord]) -> None:
        """
        Save predictions to file.
        
        Args:
            predictions: List of predictions to save
        """
        try:
            with open(self.predictions_file, "w") as f:
                for prediction in predictions:
                    f.write(prediction.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Error saving predictions: {e}")
            
    def calculate_metrics(self) -> PerformanceMetrics:
        """
        Calculate performance metrics.
        
        Returns:
            PerformanceMetrics: Calculated metrics
        """
        predictions = self.load_predictions()
        
        if not predictions:
            return PerformanceMetrics(
                total_predictions=0,
                resolved_predictions=0,
                correct_predictions=0,
                hit_rate=0.0,
                average_confidence=0.0,
                average_expected_return=0.0,
                average_actual_return=0.0,
                total_roi=0.0,
                predictions_by_risk={},
                predictions_by_confidence={},
                last_updated=datetime.now()
            )
            
        resolved = [p for p in predictions if p.is_resolved]
        correct = [p for p in resolved if p.prediction_correct]
        
        # Basic metrics
        total_predictions = len(predictions)
        resolved_predictions = len(resolved)
        correct_predictions = len(correct)
        hit_rate = correct_predictions / resolved_predictions if resolved_predictions > 0 else 0.0
        
        # Average metrics
        average_confidence = sum(p.confidence_score for p in predictions) / total_predictions
        average_expected_return = sum(p.expected_return for p in predictions) / total_predictions
        average_actual_return = (
            sum(p.actual_return for p in resolved if p.actual_return is not None) / resolved_predictions
            if resolved_predictions > 0 else 0.0
        )
        
        # Total ROI (assuming equal investment in each prediction)
        total_roi = sum(p.actual_return for p in resolved if p.actual_return is not None)
        
        # Breakdown by risk level
        predictions_by_risk = {}
        for risk_level in ["LOW", "MEDIUM", "HIGH"]:
            risk_predictions = [p for p in predictions if p.risk_level == risk_level]
            risk_resolved = [p for p in risk_predictions if p.is_resolved]
            risk_correct = [p for p in risk_resolved if p.prediction_correct]
            
            predictions_by_risk[risk_level] = {
                "total": len(risk_predictions),
                "resolved": len(risk_resolved),
                "correct": len(risk_correct),
                "hit_rate": len(risk_correct) / len(risk_resolved) if risk_resolved else 0.0
            }
            
        # Breakdown by confidence
        predictions_by_confidence = {}
        confidence_buckets = [
            ("0.6-0.7", 0.6, 0.7),
            ("0.7-0.8", 0.7, 0.8),
            ("0.8-0.9", 0.8, 0.9),
            ("0.9-1.0", 0.9, 1.0)
        ]
        
        for bucket_name, min_conf, max_conf in confidence_buckets:
            bucket_predictions = [
                p for p in predictions 
                if min_conf <= p.confidence_score < max_conf
            ]
            bucket_resolved = [p for p in bucket_predictions if p.is_resolved]
            bucket_correct = [p for p in bucket_resolved if p.prediction_correct]
            
            predictions_by_confidence[bucket_name] = {
                "total": len(bucket_predictions),
                "resolved": len(bucket_resolved),
                "correct": len(bucket_correct),
                "hit_rate": len(bucket_correct) / len(bucket_resolved) if bucket_resolved else 0.0
            }
            
        return PerformanceMetrics(
            total_predictions=total_predictions,
            resolved_predictions=resolved_predictions,
            correct_predictions=correct_predictions,
            hit_rate=hit_rate,
            average_confidence=average_confidence,
            average_expected_return=average_expected_return,
            average_actual_return=average_actual_return,
            total_roi=total_roi,
            predictions_by_risk=predictions_by_risk,
            predictions_by_confidence=predictions_by_confidence,
            last_updated=datetime.now()
        )
        
    def update_metrics(self) -> None:
        """Update and save performance metrics."""
        metrics = self.calculate_metrics()
        
        try:
            with open(self.metrics_file, "w") as f:
                f.write(metrics.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            
    def get_recent_predictions(self, days: int = 30) -> List[PredictionRecord]:
        """
        Get predictions from the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List[PredictionRecord]: Recent predictions
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        predictions = self.load_predictions()
        
        return [
            p for p in predictions 
            if p.prediction_date > cutoff_date
        ]
        
    def export_predictions_csv(self, filename: str) -> None:
        """
        Export predictions to CSV file.
        
        Args:
            filename: Output CSV filename
        """
        import csv
        
        predictions = self.load_predictions()
        
        if not predictions:
            logger.warning("No predictions to export")
            return
            
        fieldnames = [
            "condition_id", "question", "predicted_position", "predicted_probability",
            "current_market_price", "fair_value_price", "expected_return",
            "confidence_score", "overall_score", "risk_level", "prediction_date",
            "market_end_date", "actual_outcome", "resolution_date",
            "final_market_price", "actual_return", "prediction_correct"
        ]
        
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for prediction in predictions:
                row = prediction.model_dump()
                # Convert datetime objects to strings
                for field in ["prediction_date", "market_end_date", "resolution_date"]:
                    if row[field]:
                        row[field] = row[field].strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow(row)
                
        logger.info(f"Exported {len(predictions)} predictions to {filename}")


# Global instance
prediction_tracker = PredictionTracker()