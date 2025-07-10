# Polymarket Research Tool Guide

## Overview
The Market Research Tool analyzes any Polymarket link and provides evidence-based trading recommendations.

## Features

### 1. **Automatic Market Analysis**
- Paste any Polymarket URL
- Automatically fetches market data
- Analyzes current pricing vs fair value
- Provides BUY YES/NO recommendations

### 2. **Pattern Recognition**
The tool identifies key patterns:
- **Extreme Events**: Records, all-time highs/lows (typically <5% probability)
- **Continuations**: Status quo, incumbents (typically 80-90% probability)
- **Dramatic Events**: Crashes, wars, resignations (typically <10% probability)
- **Bitcoin Targets**: Analyzes price targets based on % gain needed
- **Time Decay**: Short-term unlikely events

### 3. **Evidence-Based Scoring**
Each market gets scored on:
- Historical base rates
- Pattern matching
- Time until resolution
- Market volume/liquidity
- News sentiment (if API key configured)

## Usage

### Basic Usage
```bash
python enhanced_market_researcher.py
```

Then paste any Polymarket URL when prompted.

### Command Line Usage
```bash
python enhanced_market_researcher.py "https://polymarket.com/event/bitcoin-150k-2025"
```

### Example Output
```
📈 POLYMARKET RESEARCH REPORT
================================================================================

📌 Market: Will Bitcoin reach $150,000 by December 31, 2025?
💰 Volume: $2,579,223
📊 Current Prices: YES=34.0% | NO=66.0%

📋 Key Data Points:
  • Bitcoin current price: ~$95,000 (as of Jan 2025)
    → Compare to target price in question
  • Bitcoin needs ~58% increase to reach $150k
    → Significant rally required

💡 Market Insights:
  • High volume market - prices likely more efficient
    → Smaller edges, but more reliable

🎯 RECOMMENDATION
================================================================================

✅ Position: BUY NO
📊 Confidence: 70%
💹 Expected Edge: 9.0%

📝 Analysis:
  • BTC $150k requires 58% gain
  • Historical probability suggests ~25%
  • Market overpricing at 34%

💸 Trading Suggestion:
  Entry: NO at 66.0%
  Target: 75.0%
  Potential Return: 14%
```

## Pattern Examples

### 1. **Extreme Longshots**
- "Will X reach $1 million?" → Typically <1% probability
- "Perfect season" → Typically <1% probability
- "World record" → Typically 2-3% probability

### 2. **Continuation Bias**
- "Will X remain above Y?" → Typically 85-90% probability
- "Will incumbent win?" → Typically 65-85% probability
- "Will status quo continue?" → Typically 80-90% probability

### 3. **Bitcoin Price Targets**
- $100k (5% gain) → ~55% probability
- $120k (26% gain) → ~40% probability
- $150k (58% gain) → ~25% probability
- $200k (110% gain) → ~10% probability

### 4. **Political Drama**
- "Will X resign?" → Typically 5-10% probability
- "Will X be impeached?" → Typically <5% probability
- "Will there be war?" → Typically <5% probability

## Advanced Features

### News Integration
If you have a NEWS_API_KEY in your .env file:
- Searches recent news about the market topic
- Analyzes news sentiment
- Factors into confidence scoring

### Time Analysis
- Markets with <7 days: Status quo heavily favored
- Markets with <30 days: Moderate time pressure
- Markets with >90 days: More uncertainty

### Volume Analysis
- High volume (>$100k): More efficient pricing
- Medium volume ($10k-$100k): Good liquidity
- Low volume (<$10k): Wider spreads, less reliable

## Tips for Best Results

1. **Focus on Clear Patterns**: The tool works best with markets that fit known patterns
2. **Check Volume**: Higher volume markets tend to have more reliable analysis
3. **Consider Timeframe**: Short-term markets favor status quo
4. **Multiple Patterns**: Markets with multiple confirming patterns have higher confidence
5. **News Matters**: Major news can override historical patterns

## Files

- `market_researcher.py` - Basic version
- `enhanced_market_researcher.py` - Full version with web search
- `demo_market_research.py` - Demo showing example analysis