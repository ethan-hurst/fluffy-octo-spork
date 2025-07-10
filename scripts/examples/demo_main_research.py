#!/usr/bin/env python3
"""
Demo showing the research command available in main.py
"""

import httpx

print("""
================================================================================
POLYMARKET ANALYZER - RESEARCH COMMAND IN MAIN.PY
================================================================================

The research command is now available directly from the command line!

USAGE:
------
python main.py research <polymarket-url>

EXAMPLE:
--------
""")

# Get a real market to demonstrate
try:
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={"active": "true", "closed": "false", "limit": 10}
    )
    
    if response.status_code == 200:
        markets = response.json()
        for market in markets:
            if 'bitcoin' in market.get('question', '').lower():
                slug = market.get('groupSlug', market.get('slug', ''))
                print(f"python main.py research https://polymarket.com/event/{slug}")
                print(f"\nThis will analyze: {market.get('question')}")
                break
        else:
            print("python main.py research https://polymarket.com/event/bitcoin-150k-2025")
            print("\nThis will analyze: Will Bitcoin reach $150,000 by December 31, 2025?")
except:
    print("python main.py research https://polymarket.com/event/bitcoin-150k-2025")
    print("\nThis will analyze: Will Bitcoin reach $150,000 by December 31, 2025?")

print("""
OUTPUT PREVIEW:
---------------
🔍 Researching market: https://polymarket.com/event/bitcoin-150k-2025

================================================================================
📈 MARKET RESEARCH REPORT
================================================================================

📌 Market: Will Bitcoin reach $150,000 by December 31, 2025?
💰 Volume: $2,579,223
📊 Current Price: YES=34.0% | NO=66.0%
⏰ Time Left: 356 days

📋 Pattern Analysis:
  • BITCOIN_TARGET: $150k 
    Typical: 25% vs Current: 34%

============================================================
🎯 RECOMMENDATION
============================================================

✅ Position: BUY NO
📊 Confidence: 65%
💹 Expected Edge: 9.0%

📝 Analysis:
  • BTC $150k ambitious (~25% likely)

💸 Trading Suggestion:
  Entry: NO at 66.0%
  Target: 75.0%
  Potential Return: 14%

🏆 Score Breakdown:
  YES Score: 0.0
  NO Score: 0.9

================================================================================

FEATURES:
---------
1. Command-line access for quick research
2. No need to enter interactive mode
3. Works with any Polymarket URL
4. Full pattern analysis and recommendations
5. Exit code support for scripting

OTHER COMMANDS:
---------------
python main.py                  # Start interactive console
python main.py --help          # Show help message

SCRIPTING EXAMPLE:
------------------
# In a bash script:
if python main.py research "$URL"; then
    echo "Analysis successful"
else
    echo "Analysis failed"
fi

The research command returns:
- Exit code 0 on success
- Exit code 1 on error (bad URL, market not found, etc.)
================================================================================
""")

if __name__ == "__main__":
    print("\nTry it now!")
    print("python main.py research <polymarket-url>")