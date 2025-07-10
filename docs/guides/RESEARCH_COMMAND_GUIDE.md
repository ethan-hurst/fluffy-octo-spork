# Market Research Command Guide

## Overview
The market research command is now available both from the command line and within the interactive console.

## Usage

### Command Line
```bash
# Research a specific market directly
python main.py research https://polymarket.com/event/will-bitcoin-reach-150000-by-december-31-2025

# Show help
python main.py --help
```

### Interactive Console
```bash
# Start the console
python main.py

# Then use the research command
> research https://polymarket.com/event/will-bitcoin-reach-150000-by-december-31-2025
```

## URL Formats Supported

The research command supports various Polymarket URL formats:
- `https://polymarket.com/event/market-slug`
- `https://polymarket.com/event/full-question-slug`
- `https://polymarket.com/market/condition-id`

## Features

### Pattern Recognition
- **Extreme Events**: Records, all-time highs/lows (typically <5% probability)
- **Continuation Patterns**: Status quo, incumbents (typically 80-90% probability)
- **Dramatic Events**: Crashes, wars, resignations (typically <10% probability)
- **Bitcoin Targets**: Price targets with probability estimates
- **Time Decay**: Factors in days until resolution

### Analysis Output
- Market information (volume, current prices)
- Pattern analysis with historical probabilities
- Trading recommendation (BUY YES/NO)
- Confidence score and expected edge
- Entry/target prices with potential returns
- Score breakdown

## Example Output
```
📈 MARKET RESEARCH REPORT
================================================================================

📌 Market: Will Bitcoin reach $150,000 by December 31, 2025?
💰 Volume: $2,579,223
📊 Current Price: YES=34.0% | NO=66.0%
⏰ Time Left: 175 days

📋 Pattern Analysis:
  • BITCOIN_TARGET: $150k 
    Typical: 25% vs Current: 34%

🎯 RECOMMENDATION
============================================================

✅ Position: BUY NO
📊 Confidence: 54%
💹 Expected Edge: 7.2%

📝 Analysis:
  • BTC $150k ambitious (~25% likely)

💸 Trading Suggestion:
  Entry: NO at 66.0%
  Target: 73.2%
  Potential Return: 11%
```

## Troubleshooting

### Market Not Found Error
If you get a "Market not found" error:
1. Ensure the URL is correct and complete
2. Try using the full URL from Polymarket (not shortened versions)
3. Make sure the market is active (not closed)

### Common Issues
- **Shortened URLs**: Some shortened URLs may not match. Use the full URL from Polymarket
- **Old markets**: Closed or resolved markets won't be found
- **Special characters**: Ensure the URL is properly quoted if it contains special characters

## Exit Codes
- `0`: Success - analysis completed
- `1`: Error - market not found or other error

This allows for scripting:
```bash
if python main.py research "$URL"; then
    echo "Analysis successful"
else
    echo "Analysis failed"
fi
```