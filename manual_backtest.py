"""
Manual backtesting for specific markets.

This script allows you to manually test the prediction model against
specific closed markets that you're interested in.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from src.clients.polymarket.client import PolymarketClient
from src.analyzers.market_analyzer import MarketAnalyzer
from src.analyzers.kelly_criterion import KellyCriterion
from src.clients.polymarket.models import MarketPrice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def backtest_specific_market(condition_id: str, prediction_days_before: int = 3):
    """
    Backtest a specific market by condition ID.
    
    Args:
        condition_id: The market condition ID to test
        prediction_days_before: How many days before close to simulate prediction
    """
    
    print(f"🔍 Backtesting Market: {condition_id}")
    print("=" * 60)
    
    try:
        # Initialize clients
        analyzer = MarketAnalyzer()
        kelly_calc = KellyCriterion()
        
        # Fetch the specific market
        async with PolymarketClient() as polymarket_client:
            markets_response = await polymarket_client.get_markets()
            markets = markets_response.data
        target_market = None
        
        for market in markets:
            if market.condition_id == condition_id:
                target_market = market
                break
                
        if not target_market:
            print(f"❌ Market {condition_id} not found")
            return
            
        print(f"📋 Market: {target_market.question}")
        print(f"📅 End Date: {target_market.end_date_iso}")
        print(f"🏷️ Category: {target_market.category}")
        print(f"💰 Volume: ${target_market.volume:,.0f}" if target_market.volume else "Volume: Unknown")
        print(f"🔒 Closed: {target_market.closed}")
        print()
        
        # Check if market is closed
        if not target_market.closed:
            print("⚠️ Warning: This market is still open, not truly historical")
            
        # Simulate historical prediction
        if target_market.end_date_iso:
            end_date = target_market.end_date_iso
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            simulated_prediction_time = end_date - timedelta(days=prediction_days_before)
            print(f"🕐 Simulating prediction made on: {simulated_prediction_time.strftime('%Y-%m-%d')}")
            print(f"   ({prediction_days_before} days before market close)")
        else:
            print("❌ No end date available for simulation")
            return
            
        # Create price object (using current prices as proxy for historical)
        if len(target_market.tokens) >= 2:
            yes_price = target_market.tokens[0].price or 0.5
            no_price = target_market.tokens[1].price or (1.0 - yes_price)
            
            price = MarketPrice(
                condition_id=target_market.condition_id,
                yes_price=yes_price,
                no_price=no_price,
                spread=abs(yes_price - no_price)
            )
            
            print(f"💹 Market Prices at Time:")
            print(f"   YES: {yes_price:.1%}")
            print(f"   NO: {no_price:.1%}")
            print()
        else:
            print("❌ Invalid token structure")
            return
            
        # Run our prediction model
        print("🤖 Running Prediction Model...")
        opportunity = await analyzer._analyze_single_market(
            market=target_market,
            price=price,
            news_articles=[]  # Could fetch historical news here
        )
        
        if opportunity:
            print("✅ Model Generated Prediction:")
            print(f"   Recommended Position: {opportunity.recommended_position}")
            print(f"   Fair Value: {opportunity.fair_yes_price:.1%} YES / {opportunity.fair_no_price:.1%} NO")
            print(f"   Expected Return: {opportunity.expected_return:.1%}")
            print(f"   Confidence: {opportunity.score.confidence_score:.1%}")
            print(f"   Risk Level: {opportunity.risk_level}")
            print()
            
            # Kelly Criterion analysis
            if opportunity.kelly_analysis:
                kelly = opportunity.kelly_analysis
                print("💰 Kelly Criterion Analysis:")
                print(f"   Expected Value: {kelly.expected_value:.1%}")
                print(f"   Recommended Position: {kelly.recommended_fraction:.1%} of bankroll")
                print(f"   Recommendation: {kelly.recommendation}")
                print()
                
            # Determine actual outcome
            actual_outcome = determine_market_outcome(target_market)
            if actual_outcome:
                print(f"🎯 Actual Outcome: {actual_outcome}")
                
                # Check if our prediction was correct
                prediction_correct = (
                    (opportunity.recommended_position == "YES" and actual_outcome == "YES") or
                    (opportunity.recommended_position == "NO" and actual_outcome == "NO")
                )
                
                if prediction_correct:
                    print("✅ PREDICTION CORRECT!")
                else:
                    print("❌ PREDICTION INCORRECT")
                    
                print()
                
                # Calculate what would have happened with Kelly sizing
                if opportunity.kelly_analysis and kelly.recommended_fraction > 0:
                    position_size = kelly.recommended_fraction
                    if prediction_correct:
                        if opportunity.recommended_position == "YES":
                            payout_odds = (1.0 - yes_price) / yes_price
                        else:
                            payout_odds = (1.0 - no_price) / no_price
                        actual_return = position_size * payout_odds
                        print(f"💵 Kelly Outcome: +{actual_return:.1%} of bankroll")
                    else:
                        print(f"💔 Kelly Outcome: -{position_size:.1%} of bankroll (total loss)")
                        
            else:
                print("❓ Could not determine actual outcome")
                
        else:
            print("❌ Model did not generate a prediction (filtered out)")
            print("   Possible reasons: too low volume, insufficient spread, or model error")
            
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        print(f"❌ Error: {e}")


def determine_market_outcome(market) -> str:
    """Determine the actual outcome of a market."""
    try:
        if len(market.tokens) != 2:
            return "INVALID"
            
        yes_token = market.tokens[0]
        no_token = market.tokens[1]
        
        # In closed markets, winning token should be near $1.00
        if yes_token.price and no_token.price:
            if yes_token.price > 0.9:
                return "YES"
            elif no_token.price > 0.9:
                return "NO"
            else:
                return "UNCLEAR"
        else:
            return "UNKNOWN"
            
    except Exception:
        return "ERROR"


async def find_recent_closed_markets():
    """Find some recent closed markets for testing."""
    
    print("🔍 Finding Recent Closed Markets...")
    print("=" * 60)
    
    try:
        async with PolymarketClient() as polymarket_client:
            markets_response = await polymarket_client.get_markets()
            markets = markets_response.data
        
        # Find closed markets and some open ones for examples
        closed_markets = []
        open_markets = []
        
        for market in markets:
            if market.end_date_iso:
                now = datetime.now(timezone.utc)
                end_date = market.end_date_iso
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                days_since_close = (now - end_date).days
                
                if market.closed and 0 <= days_since_close <= 60:
                    closed_markets.append((market, days_since_close))
                elif not market.closed and market.volume and market.volume > 1000:
                    # Show some open markets as examples
                    days_until_close = -days_since_close
                    open_markets.append((market, days_until_close))
                    
        # Sort by most recently closed/soonest to close
        closed_markets.sort(key=lambda x: x[1])
        open_markets.sort(key=lambda x: x[1])
        
        if closed_markets:
            print(f"🔒 Found {len(closed_markets)} recently closed markets:")
            print()
            
            for i, (market, days_ago) in enumerate(closed_markets[:5], 1):
                outcome = determine_market_outcome(market)
                volume_str = f"${market.volume:,.0f}" if market.volume else "Unknown"
                
                print(f"{i:2d}. {market.condition_id}")
                print(f"    Question: {market.question[:80]}...")
                print(f"    Closed: {days_ago} days ago | Volume: {volume_str} | Outcome: {outcome}")
                print(f"    Category: {market.category or 'Unknown'}")
                print()
        else:
            print("❌ No recently closed markets found")
            
        if open_markets:
            print(f"\n🟢 Found {len(open_markets)} open markets (for testing):")
            print()
            
            for i, (market, days_until) in enumerate(open_markets[:5], 1):
                volume_str = f"${market.volume:,.0f}" if market.volume else "Unknown"
                yes_price = market.tokens[0].price if market.tokens else 0.5
                
                print(f"{i:2d}. {market.condition_id}")
                print(f"    Question: {market.question[:80]}...")
                print(f"    Closes in: {days_until} days | Volume: {volume_str} | YES: {yes_price:.1%}")
                print(f"    Category: {market.category or 'Unknown'}")
                print()
                
        print("💡 Copy a condition_id to test it with backtest_specific_market()")
            
    except Exception as e:
        print(f"❌ Error finding markets: {e}")


async def main():
    """Main function for manual backtesting."""
    
    print("🔬 Manual Backtesting Tool")
    print("=" * 60)
    
    # First, show available markets
    await find_recent_closed_markets()
    
    # Example: Test a specific market (you would replace this with an actual condition_id)
    print("\n" + "=" * 60)
    print("📊 Example Backtest")
    print("=" * 60)
    print("💡 To test a specific market, replace 'example_condition_id' below with a real condition_id")
    print("   from the list above, then run: python manual_backtest.py")
    
    # Uncomment and modify this line to test a specific market:
    # await backtest_specific_market("0x1234...", prediction_days_before=3)


if __name__ == "__main__":
    asyncio.run(main())