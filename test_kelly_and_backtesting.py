"""
Test Kelly Criterion and backtesting integration.
"""

import asyncio
from datetime import datetime, timedelta

from src.analyzers.market_analyzer import MarketAnalyzer
from src.analyzers.backtesting import BacktestingEngine
from src.clients.polymarket.models import Market, Token, MarketPrice


async def test_kelly_criterion_integration():
    """Test Kelly Criterion integration with market analysis."""
    
    print("Testing Kelly Criterion Integration\n")
    
    # Create test markets
    merger_market = Market(
        condition_id="x_truth_social_merger",
        question="X and Truth Social merger announced before August?",
        description="Will X and Truth Social merge before July 31, 2025",
        category="Technology",
        active=True,
        closed=False,
        volume=50000.0,
        end_date_iso=datetime(2025, 7, 31),
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.006),  # 0.6%
            Token(token_id="no", outcome="No", price=0.994)     # 99.4%
        ],
        minimum_order_size=1.0
    )
    
    reasonable_market = Market(
        condition_id="fed_rates_march",
        question="Will the Fed raise rates in March 2025?",
        description="Federal Reserve interest rate decision",
        category="Economics",
        active=True,
        closed=False,
        volume=500000.0,
        end_date_iso=datetime(2025, 3, 31),
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.65),
            Token(token_id="no", outcome="No", price=0.35)
        ],
        minimum_order_size=1.0
    )
    
    # Initialize analyzer
    analyzer = MarketAnalyzer()
    
    # Create price objects
    merger_price = MarketPrice(
        condition_id=merger_market.condition_id,
        yes_price=0.006,
        no_price=0.994,
        spread=0.988
    )
    
    fed_price = MarketPrice(
        condition_id=reasonable_market.condition_id,
        yes_price=0.65,
        no_price=0.35,
        spread=0.30
    )
    
    # Analyze extreme merger market
    print("=== X/Truth Social Merger Analysis ===")
    merger_opportunity = await analyzer._analyze_single_market(merger_market, merger_price, [])
    
    if merger_opportunity:
        print(f"Market Question: {merger_opportunity.question}")
        print(f"Recommended Position: {merger_opportunity.recommended_position}")
        print(f"Current Price: {merger_opportunity.current_yes_price:.1%}")
        print(f"Fair Price: {merger_opportunity.fair_yes_price:.1%}")
        print(f"Risk Level: {merger_opportunity.risk_level}")
    else:
        print("❌ Market was filtered out (too low volume or spread)")
        # Let's bypass the analyzer and test Kelly directly
        from src.analyzers.kelly_criterion import KellyCriterion
        kelly_calc = KellyCriterion()
        kelly_result = kelly_calc.calculate(
            market=merger_market,
            predicted_probability=0.05,  # 5% (sanity checked)
            confidence=0.35,
            recommended_position="YES"
        )
        print(f"\nDirect Kelly Analysis:")
        print(f"  Expected Value: {kelly_result.expected_value:.1%}")
        print(f"  Recommended Position: {kelly_result.recommended_fraction:.1%} of bankroll")
        print(f"  Recommendation: {kelly_result.recommendation}")
        if kelly_result.warnings:
            print(f"  Warnings:")
            for warning in kelly_result.warnings[:3]:
                print(f"    • {warning}")
        return  # Skip the rest for this market
    
    if merger_opportunity.kelly_analysis:
        kelly = merger_opportunity.kelly_analysis
        print(f"\nKelly Analysis:")
        print(f"  Expected Value: {kelly.expected_value:.1%}")
        print(f"  Kelly Fraction: {kelly.kelly_fraction:.1%}")
        print(f"  Recommended Position: {kelly.recommended_fraction:.1%} of bankroll")
        print(f"  Recommendation: {kelly.recommendation}")
        print(f"  Probability of Ruin: {kelly.probability_of_ruin:.1%}")
        
        if kelly.warnings:
            print(f"  Warnings:")
            for warning in kelly.warnings[:3]:
                print(f"    • {warning}")
    else:
        print("❌ Kelly analysis not available")
        
    print("\n" + "="*70)
    
    # Analyze reasonable market
    print("=== Fed Rate Decision Analysis ===")
    fed_opportunity = await analyzer._analyze_single_market(reasonable_market, fed_price, [])
    
    if fed_opportunity:
        print(f"Market Question: {fed_opportunity.question}")
        print(f"Recommended Position: {fed_opportunity.recommended_position}")
        print(f"Current Price: {fed_opportunity.current_yes_price:.1%}")
        print(f"Fair Price: {fed_opportunity.fair_yes_price:.1%}")
        print(f"Risk Level: {fed_opportunity.risk_level}")
    else:
        print("❌ Market was filtered out")
        return
    
    if fed_opportunity.kelly_analysis:
        kelly = fed_opportunity.kelly_analysis
        print(f"\nKelly Analysis:")
        print(f"  Expected Value: {kelly.expected_value:.1%}")
        print(f"  Kelly Fraction: {kelly.kelly_fraction:.1%}")
        print(f"  Recommended Position: {kelly.recommended_fraction:.1%} of bankroll")
        print(f"  Recommendation: {kelly.recommendation}")
        print(f"  Probability of Ruin: {kelly.probability_of_ruin:.1%}")
        
        if kelly.warnings:
            print(f"  Warnings:")
            for warning in kelly.warnings[:3]:
                print(f"    • {warning}")
    else:
        print("❌ Kelly analysis not available")


def test_backtesting_system():
    """Test backtesting system functionality."""
    
    print("\n" + "="*70)
    print("Testing Backtesting System\n")
    
    # Initialize backtesting engine
    backtesting = BacktestingEngine("data/test_backtests")
    
    # Test with some resolved outcomes
    print("=== Updating Outcomes ===")
    backtesting.update_outcome("x_truth_social_merger", "NO", datetime.now())
    backtesting.update_outcome("fed_rates_march", "YES", datetime.now())
    
    # Run backtest analysis
    print("\n=== Running Backtest ===")
    metrics = backtesting.run_backtest(model_version="v2024.1")
    
    print(f"Total Predictions: {metrics.total_predictions}")
    print(f"Accuracy: {metrics.accuracy:.1%}")
    print(f"Calibration Error: {metrics.calibration_error:.1%}")
    print(f"Mean Brier Score: {metrics.mean_brier_score:.3f}")
    
    # Generate full report
    report = backtesting.generate_report(metrics)
    print(f"\n{report}")


def demonstrate_kelly_examples():
    """Show Kelly Criterion examples with different scenarios."""
    
    print("\n" + "="*70)
    print("Kelly Criterion Examples\n")
    
    from src.analyzers.kelly_criterion import KellyCriterion
    
    kelly_calc = KellyCriterion()
    
    # Example 1: Good edge case
    good_market = Market(
        condition_id="good_edge",
        question="Test market with good edge",
        active=True,
        closed=False,
        minimum_order_size=1.0,
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.40),  # 40%
            Token(token_id="no", outcome="No", price=0.60)     # 60%
        ]
    )
    
    result1 = kelly_calc.calculate(
        market=good_market,
        predicted_probability=0.55,  # We think 55% but market says 40%
        confidence=0.8,
        recommended_position="YES"
    )
    
    print("=== Good Edge Example ===")
    print(f"Market Price: 40%, Our Estimate: 55%")
    print(f"Expected Value: {result1.expected_value:.1%}")
    print(f"Kelly Fraction: {result1.kelly_fraction:.1%}")
    print(f"Recommended: {result1.recommended_fraction:.1%}")
    print(f"Advice: {result1.recommendation}")
    
    # Example 2: Bad bet
    bad_market = Market(
        condition_id="bad_bet",
        question="Test market with bad edge",
        active=True,
        closed=False,
        minimum_order_size=1.0,
        tokens=[
            Token(token_id="yes", outcome="Yes", price=0.70),  # 70%
            Token(token_id="no", outcome="No", price=0.30)     # 30%
        ]
    )
    
    result2 = kelly_calc.calculate(
        market=bad_market,
        predicted_probability=0.60,  # We think 60% but market says 70%
        confidence=0.7,
        recommended_position="YES"
    )
    
    print("\n=== Bad Bet Example ===")
    print(f"Market Price: 70%, Our Estimate: 60%")
    print(f"Expected Value: {result2.expected_value:.1%}")
    print(f"Kelly Fraction: {result2.kelly_fraction:.1%}")
    print(f"Recommended: {result2.recommended_fraction:.1%}")
    print(f"Advice: {result2.recommendation}")
    
    # Show formatted analysis
    print(f"\n{kelly_calc.format_analysis(result1)}")


if __name__ == "__main__":
    # Run Kelly Criterion integration test
    asyncio.run(test_kelly_criterion_integration())
    
    # Test backtesting system
    test_backtesting_system()
    
    # Show Kelly examples
    demonstrate_kelly_examples()