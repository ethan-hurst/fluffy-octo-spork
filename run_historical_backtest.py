"""
Run historical backtesting against closed Polymarket markets.

This script fetches closed markets and tests our prediction model
against them to validate performance on real historical data.
"""

import asyncio
import logging
from datetime import datetime

from src.analyzers.historical_backtesting import HistoricalBacktester
from src.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run historical backtesting."""
    
    print("🔄 Starting Historical Backtesting...")
    print("=" * 60)
    
    # Initialize backtester
    backtester = HistoricalBacktester()
    
    try:
        # Run backtest on last 30 days of closed markets
        print("📊 Running backtest on closed markets from last 30 days...")
        result = await backtester.run_historical_backtest(
            days_back=30,           # Look at markets closed in last 30 days
            max_markets=20,         # Test up to 20 markets
            prediction_window_days=3,  # Simulate predictions 3 days before close
            categories=None         # Test all categories
        )
        
        # Generate and display report
        report = backtester.generate_historical_report(result)
        print(report)
        
        # Additional analysis
        if result.metrics.total_predictions > 0:
            print("\n🎯 **Key Insights:**")
            
            # Model calibration
            if abs(result.metrics.calibration_error) < 0.1:
                print("✅ Model appears well-calibrated (calibration error < 10%)")
            else:
                print(f"⚠️ Model may need calibration (error: {result.metrics.calibration_error:.1%})")
                
            # Accuracy assessment
            if result.metrics.accuracy > 0.6:
                print(f"✅ Good accuracy: {result.metrics.accuracy:.1%}")
            elif result.metrics.accuracy > 0.5:
                print(f"⚡ Moderate accuracy: {result.metrics.accuracy:.1%}")
            else:
                print(f"❌ Poor accuracy: {result.metrics.accuracy:.1%} - Model needs improvement")
                
            # Confidence correlation
            if result.metrics.confidence_correlation > 0.3:
                print("✅ Model confidence correlates well with actual accuracy")
            else:
                print("⚠️ Model confidence doesn't correlate well with accuracy")
                
        else:
            print("❌ No predictions were successfully generated. Check market filters and data.")
            
    except Exception as e:
        logger.error(f"Historical backtesting failed: {e}")
        print(f"❌ Error: {e}")
        

async def run_category_specific_backtest():
    """Run backtests for specific categories."""
    
    print("\n" + "=" * 60)
    print("🎯 Category-Specific Backtesting")
    print("=" * 60)
    
    backtester = HistoricalBacktester()
    
    # Test different categories
    categories_to_test = [
        ["Politics", "Elections"],
        ["Crypto", "Bitcoin"], 
        ["Sports"],
        ["Technology"]
    ]
    
    for categories in categories_to_test:
        try:
            print(f"\n📂 Testing {', '.join(categories)} markets...")
            
            result = await backtester.run_historical_backtest(
                days_back=60,           # Look back further for category-specific
                max_markets=10,         # Fewer markets per category
                prediction_window_days=5,
                categories=categories
            )
            
            if result.markets_tested > 0:
                print(f"✅ {categories[0]}: {result.metrics.accuracy:.1%} accuracy "
                      f"({result.markets_tested} markets)")
            else:
                print(f"❌ {categories[0]}: No suitable markets found")
                
        except Exception as e:
            print(f"❌ {categories[0]}: Error - {e}")


async def validate_against_recent_markets():
    """Validate against very recent markets for faster feedback."""
    
    print("\n" + "=" * 60) 
    print("⚡ Quick Validation Against Recent Markets")
    print("=" * 60)
    
    backtester = HistoricalBacktester()
    
    try:
        # Quick test on very recent markets
        result = await backtester.run_historical_backtest(
            days_back=7,            # Last week only
            max_markets=5,          # Just a few markets
            prediction_window_days=1,  # 1 day before close
            categories=None
        )
        
        print(f"\n⚡ Quick Results:")
        print(f"• Markets Tested: {result.markets_tested}")
        if result.markets_tested > 0:
            print(f"• Accuracy: {result.metrics.accuracy:.1%}")
            print(f"• Calibration Error: {result.metrics.calibration_error:.1%}")
            
            # Simple recommendation
            if result.metrics.accuracy > 0.6 and abs(result.metrics.calibration_error) < 0.15:
                print("✅ Model looks ready for live predictions!")
            else:
                print("⚠️ Consider model adjustments before live use")
        else:
            print("❌ No recent closed markets found for testing")
            
    except Exception as e:
        print(f"❌ Quick validation failed: {e}")


if __name__ == "__main__":
    print("🚀 Historical Backtesting Suite")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run main backtest
    asyncio.run(main())
    
    # Run additional analysis
    asyncio.run(run_category_specific_backtest())
    asyncio.run(validate_against_recent_markets())
    
    print("\n✅ Historical backtesting complete!")
    print("💡 Use these results to tune model parameters and validate performance.")