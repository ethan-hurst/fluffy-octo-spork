"""
Unit tests for BacktestingEngine functionality.
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from src.analyzers.backtesting import BacktestingEngine, BacktestPrediction, BacktestMetrics
from src.analyzers.models import MarketOpportunity, OpportunityScore
from src.clients.polymarket.models import Market, Token


class TestBacktestingEngine:
    """Test cases for BacktestingEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.engine = BacktestingEngine(data_dir=self.temp_dir)
        
        # Create test market
        self.test_market = Market(
            condition_id="test_market_123",
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
        
        # Create test opportunity
        self.test_opportunity = MarketOpportunity(
            condition_id="test_market_123",
            question="Will Bitcoin reach $100,000?",
            description="Bitcoin price prediction",
            category="Crypto",
            market_slug="bitcoin-100k",
            current_yes_price=0.4,
            current_no_price=0.6,
            current_spread=0.2,
            volume=50000.0,
            liquidity=10000.0,
            fair_yes_price=0.7,
            fair_no_price=0.3,
            expected_return=75.0,
            recommended_position="YES",
            score=OpportunityScore(
                value_score=0.8,
                confidence_score=0.85,
                volume_score=0.9,
                time_score=0.7,
                news_relevance_score=0.6
            ),
            end_date=datetime.now() + timedelta(days=90),
            reasoning="Strong bullish indicators",
            related_news=["Bitcoin surges", "Institutional adoption"]
        )
        
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def test_record_prediction(self):
        """Test recording a prediction."""
        # Record prediction
        self.engine.record_prediction(
            self.test_market,
            self.test_opportunity,
            model_version="v1.0"
        )
        
        # Check prediction was saved
        assert self.engine.predictions_file.exists()
        
        # Load and verify prediction
        with open(self.engine.predictions_file, "r") as f:
            data = json.loads(f.readline())
            
        assert data["condition_id"] == "test_market_123"
        assert data["predicted_probability"] == 0.7  # Fair YES price
        assert data["confidence"] == 0.85
        assert data["recommended_position"] == "YES"
        assert data["market_price"] == 0.4
        assert data["model_version"] == "v1.0"
        
    def test_update_outcome_yes(self):
        """Test updating prediction outcome to YES."""
        # First record a prediction
        self.engine.record_prediction(
            self.test_market,
            self.test_opportunity,
            model_version="v1.0"
        )
        
        # Update outcome
        self.engine.update_outcome(
            condition_id="test_market_123",
            outcome="YES",
            resolution_date=datetime.now() + timedelta(days=30),
            final_price=0.95
        )
        
        # Load and verify update
        predictions = self.engine._load_predictions()
        assert len(predictions) == 1
        
        pred = predictions[0]
        assert pred.actual_outcome == "YES"
        assert pred.was_correct is True  # Recommended YES, outcome YES
        assert pred.final_price == 0.95
        assert pred.brier_score is not None
        assert pred.log_score is not None
        
    def test_update_outcome_no(self):
        """Test updating prediction outcome to NO."""
        # Record prediction
        self.engine.record_prediction(
            self.test_market,
            self.test_opportunity,
            model_version="v1.0"
        )
        
        # Update outcome
        self.engine.update_outcome(
            condition_id="test_market_123",
            outcome="NO",
            resolution_date=datetime.now() + timedelta(days=30),
            final_price=0.05
        )
        
        # Load and verify
        predictions = self.engine._load_predictions()
        pred = predictions[0]
        
        assert pred.actual_outcome == "NO"
        assert pred.was_correct is False  # Recommended YES, outcome NO
        assert pred.brier_score > 0  # Should have high error
        
    def test_update_outcome_invalid(self):
        """Test updating prediction outcome to INVALID."""
        # Record prediction
        self.engine.record_prediction(
            self.test_market,
            self.test_opportunity
        )
        
        # Update outcome
        self.engine.update_outcome(
            condition_id="test_market_123",
            outcome="INVALID"
        )
        
        # Load and verify
        predictions = self.engine._load_predictions()
        pred = predictions[0]
        
        assert pred.actual_outcome == "INVALID"
        assert pred.was_correct is None  # Don't count invalid markets
        
    def test_update_outcome_no_prediction(self):
        """Test updating outcome with no matching prediction."""
        # Try to update non-existent prediction
        self.engine.update_outcome(
            condition_id="non_existent",
            outcome="YES"
        )
        
        # Should handle gracefully (logged warning)
        
    def test_run_backtest_basic(self):
        """Test running a basic backtest."""
        # Create test market 1
        market1 = Market(
            condition_id="test_0",
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
        
        opportunity1 = MarketOpportunity(
            condition_id="test_0",
            question="Will Bitcoin reach $100,000?",
            description="Bitcoin price prediction",
            category="Crypto",
            market_slug="bitcoin-100k",
            current_yes_price=0.4,
            current_no_price=0.6,
            current_spread=0.2,
            volume=50000.0,
            liquidity=10000.0,
            fair_yes_price=0.7,
            fair_no_price=0.3,
            expected_return=75.0,
            recommended_position="YES",
            score=OpportunityScore(
                value_score=0.8,
                confidence_score=0.85,
                volume_score=0.9,
                time_score=0.7,
                news_relevance_score=0.6
            ),
            end_date=datetime.now() + timedelta(days=90),
            reasoning="Strong bullish indicators",
            related_news=["Bitcoin surges", "Institutional adoption"]
        )
        
        # Create test market 2
        market2 = Market(
            condition_id="test_1",
            question="Test 2?",
            description="Test",
            category="Test",
            active=True,
            closed=False,
            volume=10000.0,
            end_date_iso=datetime.now() + timedelta(days=30),
            tokens=[
                Token(token_id="yes", outcome="YES", price=0.3),
                Token(token_id="no", outcome="NO", price=0.7)
            ],
            minimum_order_size=1.0
        )
        
        opportunity2 = MarketOpportunity(
            condition_id="test_1",
            question="Test 2?",
            description="Test",
            category="Test",
            market_slug="test-2",
            current_yes_price=0.3,
            current_no_price=0.7,
            current_spread=0.4,
            volume=10000.0,
            liquidity=5000.0,
            fair_yes_price=0.2,
            fair_no_price=0.8,
            expected_return=50.0,
            recommended_position="NO",
            score=OpportunityScore(
                value_score=0.7,
                confidence_score=0.8,
                volume_score=0.6,
                time_score=0.5,
                news_relevance_score=0.4
            ),
            end_date=datetime.now() + timedelta(days=30),
            reasoning="Test reasoning",
            related_news=[]
        )
        
        # Record and resolve predictions
        self.engine.record_prediction(market1, opportunity1)
        self.engine.update_outcome("test_0", "YES")  # Correct prediction
        
        self.engine.record_prediction(market2, opportunity2)
        self.engine.update_outcome("test_1", "YES")  # Incorrect prediction (recommended NO)
        
        # Run backtest
        metrics = self.engine.run_backtest()
        
        assert metrics.total_predictions == 2
        assert metrics.correct_predictions == 1
        assert metrics.accuracy == 0.5
        assert metrics.mean_brier_score > 0
        
    def test_run_backtest_with_filters(self):
        """Test running backtest with filters."""
        # Record old prediction
        old_market = self.test_market
        old_market.condition_id = "old_market"
        old_opportunity = self.test_opportunity
        old_opportunity.condition_id = "old_market"
        
        self.engine.record_prediction(old_market, old_opportunity, model_version="v1.0")
        
        # Manually set old date
        predictions = self.engine._load_predictions()
        predictions[0].prediction_date = datetime.now() - timedelta(days=100)
        self.engine._save_predictions(predictions)
        
        # Update outcome
        self.engine.update_outcome("old_market", "YES")
        
        # Record recent prediction (different version)
        new_market = self.test_market
        new_market.condition_id = "new_market"
        new_opportunity = self.test_opportunity
        new_opportunity.condition_id = "new_market"
        
        self.engine.record_prediction(new_market, new_opportunity, model_version="v2.0")
        self.engine.update_outcome("new_market", "NO")
        
        # Test model version filter
        metrics_v1 = self.engine.run_backtest(model_version="v1.0")
        assert metrics_v1.total_predictions == 1
        
        # Test days filter
        metrics_old = self.engine.run_backtest(min_days_since_prediction=50)
        assert metrics_old.total_predictions == 1
        
    def test_calculate_prediction_metrics(self):
        """Test calculation of individual prediction metrics."""
        # Create prediction
        pred = BacktestPrediction(
            condition_id="test",
            question="Test?",
            predicted_probability=0.8,
            confidence=0.9,
            recommended_position="YES",
            market_price=0.3,
            prediction_date=datetime.now(),
            model_version="v1.0"
        )
        
        # Set outcome and calculate metrics
        pred.actual_outcome = "YES"
        self.engine._calculate_prediction_metrics(pred)
        
        assert pred.was_correct is True
        assert pred.brier_score == (0.8 - 1.0) ** 2  # Small error
        assert pred.log_score < 0  # Log of probability < 1
        assert pred.calibration_error == abs(0.8 - 1.0)
        
    def test_backtest_metrics_calculation(self):
        """Test comprehensive metrics calculation."""
        # Create varied predictions
        predictions = [
            BacktestPrediction(
                condition_id="p1",
                question="Q1?",
                predicted_probability=0.9,
                confidence=0.95,
                recommended_position="YES",
                market_price=0.6,
                prediction_date=datetime.now() - timedelta(days=50),
                model_version="v1.0",
                actual_outcome="YES",
                resolution_date=datetime.now() - timedelta(days=45),
                was_correct=True,
                brier_score=0.01,
                log_score=-0.1,
                calibration_error=0.1
            ),
            BacktestPrediction(
                condition_id="p2",
                question="Q2?",
                predicted_probability=0.3,
                confidence=0.4,
                recommended_position="NO",
                market_price=0.7,
                prediction_date=datetime.now() - timedelta(days=10),
                model_version="v1.0",
                actual_outcome="NO",
                resolution_date=datetime.now() - timedelta(days=5),
                was_correct=True,
                brier_score=0.09,
                log_score=-0.3,
                calibration_error=0.3
            ),
            BacktestPrediction(
                condition_id="p3",
                question="Q3?",
                predicted_probability=0.7,
                confidence=0.6,
                recommended_position="YES",
                market_price=0.5,
                prediction_date=datetime.now() - timedelta(days=25),
                model_version="v1.0",
                actual_outcome="NO",
                resolution_date=datetime.now() - timedelta(days=20),
                was_correct=False,
                brier_score=0.49,
                log_score=-1.2,
                calibration_error=0.7
            )
        ]
        
        metrics = self.engine._calculate_backtest_metrics(predictions)
        
        assert metrics.total_predictions == 3
        assert metrics.correct_predictions == 2
        assert metrics.accuracy == 2/3
        assert metrics.high_confidence_accuracy == 1.0  # Only p1 has high conf
        assert metrics.low_confidence_accuracy == 1.0  # Only p2 has low conf
        # Note: p1 has predicted probability 0.9, which is exactly at the boundary
        # The test checks for < 0.1 or > 0.9, so 0.9 may not be included as extreme
        # Let's check if there are any extreme predictions first
        extreme_preds = [
            p for p in predictions 
            if p.predicted_probability < 0.1 or p.predicted_probability > 0.9
        ]
        if extreme_preds:
            assert metrics.extreme_predictions_accuracy == 1.0
        else:
            assert metrics.extreme_predictions_accuracy == 0.0
        
    def test_confidence_correlation(self):
        """Test confidence-accuracy correlation calculation."""
        predictions = [
            BacktestPrediction(
                condition_id=f"p{i}",
                question="Q?",
                predicted_probability=0.5,
                confidence=conf,
                recommended_position="YES",
                market_price=0.5,
                prediction_date=datetime.now(),
                model_version="v1.0",
                was_correct=correct
            )
            for i, (conf, correct) in enumerate([
                (0.9, True),
                (0.8, True),
                (0.7, True),
                (0.6, False),
                (0.5, False),
                (0.4, False)
            ])
        ]
        
        correlation = self.engine._calculate_confidence_correlation(predictions)
        
        # Should have positive correlation (higher confidence = higher accuracy)
        assert correlation > 0.5
        
    def test_market_deviation_analysis(self):
        """Test market deviation analysis."""
        predictions = [
            # Small deviation: predicted 0.45, market 0.4
            BacktestPrediction(
                condition_id="p1",
                question="Q1?",
                predicted_probability=0.45,
                confidence=0.8,
                recommended_position="YES",
                market_price=0.4,
                prediction_date=datetime.now(),
                model_version="v1.0",
                was_correct=True
            ),
            # Large deviation: predicted 0.9, market 0.1
            BacktestPrediction(
                condition_id="p2",
                question="Q2?",
                predicted_probability=0.9,
                confidence=0.8,
                recommended_position="YES",
                market_price=0.1,
                prediction_date=datetime.now(),
                model_version="v1.0",
                was_correct=False
            )
        ]
        
        analysis = self.engine._analyze_market_deviations(predictions)
        
        assert "small_deviation" in analysis
        assert "large_deviation" in analysis
        assert analysis["small_deviation"] == 1.0  # 100% accuracy
        assert analysis["large_deviation"] == 0.0  # 0% accuracy
        
    def test_time_to_resolution_analysis(self):
        """Test time to resolution analysis."""
        base_date = datetime.now()
        predictions = [
            # 3 days to resolution
            BacktestPrediction(
                condition_id="p1",
                question="Q1?",
                predicted_probability=0.6,
                confidence=0.8,
                recommended_position="YES",
                market_price=0.5,
                prediction_date=base_date - timedelta(days=3),
                resolution_date=base_date,
                model_version="v1.0",
                was_correct=True
            ),
            # 20 days to resolution
            BacktestPrediction(
                condition_id="p2",
                question="Q2?",
                predicted_probability=0.6,
                confidence=0.8,
                recommended_position="YES",
                market_price=0.5,
                prediction_date=base_date - timedelta(days=20),
                resolution_date=base_date,
                model_version="v1.0",
                was_correct=False
            ),
            # 60 days to resolution
            BacktestPrediction(
                condition_id="p3",
                question="Q3?",
                predicted_probability=0.6,
                confidence=0.8,
                recommended_position="YES",
                market_price=0.5,
                prediction_date=base_date - timedelta(days=60),
                resolution_date=base_date,
                model_version="v1.0",
                was_correct=True
            )
        ]
        
        analysis = self.engine._analyze_time_to_resolution(predictions)
        
        assert analysis["0-7d"] == 1.0  # 100% accuracy
        assert analysis["7-30d"] == 0.0  # 0% accuracy
        assert analysis["30d+"] == 1.0  # 100% accuracy
        
    def test_generate_report(self):
        """Test report generation."""
        metrics = BacktestMetrics(
            total_predictions=100,
            correct_predictions=75,
            accuracy=0.75,
            mean_predicted_probability=0.65,
            actual_success_rate=0.70,
            calibration_error=0.05,
            mean_brier_score=0.15,
            mean_log_score=-0.5,
            high_confidence_accuracy=0.85,
            low_confidence_accuracy=0.60,
            confidence_correlation=0.45,
            accuracy_by_category={"crypto": 0.8, "politics": 0.7},
            sample_sizes_by_category={"crypto": 60, "politics": 40},
            accuracy_by_time_to_resolution={"0-7d": 0.9, "7-30d": 0.75, "30d+": 0.65},
            extreme_predictions_accuracy=0.80,
            market_deviation_analysis={"small_deviation": 0.85, "large_deviation": 0.55}
        )
        
        report = self.engine.generate_report(metrics)
        
        assert "Backtest Performance Report" in report
        assert "Total Predictions: 100" in report
        assert "Accuracy: 75.0%" in report
        assert "Calibration Error: 5.0%" in report
        assert "High Confidence Accuracy" in report
        assert "Market Deviation Analysis" in report
        assert "Time to Resolution Analysis" in report
        
    def test_empty_metrics(self):
        """Test empty metrics generation."""
        metrics = self.engine._empty_metrics()
        
        assert metrics.total_predictions == 0
        assert metrics.accuracy == 0.0
        assert metrics.accuracy_by_category == {}
        
        # Test report with empty metrics
        report = self.engine.generate_report(metrics)
        assert "No Data Available" in report
        
    def test_load_save_predictions(self):
        """Test loading and saving predictions."""
        # Create test predictions
        predictions = [
            BacktestPrediction(
                condition_id="test1",
                question="Q1?",
                predicted_probability=0.6,
                confidence=0.8,
                recommended_position="YES",
                market_price=0.4,
                prediction_date=datetime.now(),
                model_version="v1.0"
            ),
            BacktestPrediction(
                condition_id="test2",
                question="Q2?",
                predicted_probability=0.3,
                confidence=0.7,
                recommended_position="NO",
                market_price=0.7,
                prediction_date=datetime.now(),
                model_version="v1.0"
            )
        ]
        
        # Save predictions
        self.engine._save_predictions(predictions)
        
        # Load and verify
        loaded = self.engine._load_predictions()
        assert len(loaded) == 2
        assert loaded[0].condition_id == "test1"
        assert loaded[1].condition_id == "test2"
        
    def test_invalid_prediction_data(self):
        """Test handling of invalid prediction data."""
        # Write invalid JSON to predictions file
        with open(self.engine.predictions_file, "w") as f:
            f.write("invalid json\n")
            f.write('{"condition_id": "valid", "question": "Q?", "predicted_probability": 0.5, "confidence": 0.8, "recommended_position": "YES", "market_price": 0.4, "prediction_date": "2024-01-01T00:00:00", "model_version": "v1.0"}\n')
        
        # Should skip invalid lines
        predictions = self.engine._load_predictions()
        assert len(predictions) == 1
        assert predictions[0].condition_id == "valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])