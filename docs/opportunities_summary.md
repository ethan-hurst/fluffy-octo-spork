# Polymarket Opportunity Finder - Enhanced

## Improvements Made

1. **Lowered Thresholds**
   - Minimum volume: $500 (was $1,000)
   - Minimum edge: 3% (was 5%)
   - Analyze more markets: 500 (was 100)

2. **Expanded Pattern Detection**
   - **Extreme Longshots**: Events priced 5-20% that should be <5%
   - **Overpriced Moderate Events**: 10-30% events likely overpriced
   - **Underpriced Continuations**: 70-90% events that should be higher
   - **Binary Mispricings**: True 50/50 events mispriced
   - **Near Impossibilities**: Events that almost never happen
   - **Time-Sensitive**: Short-term unlikely events
   - **Bitcoin/Crypto Specific**: Price target analysis
   - **Political Events**: Drama and unlikely scenarios

3. **Pattern Examples Found**
   - Bitcoin $120k by 2025: 72% → Should be ~50% (BUY NO)
   - Argentina incumbent party: 71% → Should be ~88% (BUY YES)
   - US confirms aliens: 5.2% → Should be ~0.1% (BUY NO)
   - Trump abolishes IRS: 7% → Should be ~0.5% (BUY NO)
   - Hottest year record: 7% → Should be ~2% (BUY NO)

## Current Opportunities (5 found)

### High Confidence Plays
1. **Will UP hold most seats in Argentina?**
   - Current: 71%, Fair: 88%
   - Edge: 17%, Volume: $1M+
   - Action: BUY YES

2. **Will Bitcoin reach $120,000 by 2025?**
   - Current: 72%, Fair: 50%
   - Edge: 22%, Volume: $1.5M
   - Action: BUY NO

### Lower Edge but High Volume
3. **Will US confirm aliens exist?**
   - Current: 5.2%, Fair: 0.1%
   - Edge: 5.1%, Volume: $1.7M
   - Action: BUY NO

## How to Find More Opportunities

1. Run the direct finder: `python direct_opportunity_finder.py`
2. Adjust thresholds in the script for more results
3. Add new patterns based on market observations
4. Check different times of day (new markets added regularly)

## Key Success Factors
- Focus on extreme mispricings (very high or very low probabilities)
- Look for continuation bias (things tend to stay the same)
- Identify impossible/nearly impossible events overpriced
- Time decay opportunities (short-term unlikely events)
- Category-specific knowledge (Bitcoin targets, political drama)