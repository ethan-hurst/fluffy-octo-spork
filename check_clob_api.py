#!/usr/bin/env python3
"""
Check CLOB API for the market
"""

import httpx
import asyncio
import json

async def check_clob():
    """Check CLOB API specifically."""
    
    print("=== CHECKING CLOB API ===\n")
    
    async with httpx.AsyncClient() as client:
        # CLOB API uses pagination
        next_cursor = "MA=="
        all_markets = []
        page = 1
        
        while next_cursor and page <= 5:  # Limit to 5 pages for testing
            print(f"Page {page}...")
            
            response = await client.get(
                "https://clob.polymarket.com/markets",
                params={"next_cursor": next_cursor},
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('data', [])
                all_markets.extend(markets)
                
                print(f"  Found {len(markets)} markets")
                
                # Check for our market
                for market in markets:
                    if 'elon' in str(market).lower() and 'america' in str(market).lower():
                        print(f"\n  🎯 Potential match found:")
                        print(f"  {json.dumps(market, indent=2)[:500]}...")
                
                # Get next cursor
                next_cursor = data.get('next_cursor')
                if not next_cursor:
                    print("  No more pages")
                    break
                    
                page += 1
            else:
                print(f"  Error: {response.status_code}")
                break
        
        print(f"\nTotal markets checked: {len(all_markets)}")
        
        # Also check the data structure
        if all_markets:
            print("\nSample market structure from CLOB:")
            sample = all_markets[0]
            print(f"Keys: {list(sample.keys())}")
            
            # Check if condition_id is present
            if 'condition_id' in sample:
                print(f"Condition ID format: {sample['condition_id']}")
            if 'question' in sample:
                print(f"Question: {sample['question'][:60]}...")
        
        # Try direct market lookup if we find a condition ID pattern
        print("\n\nTrying some direct lookups on CLOB:")
        
        # The URL might give us clues about the condition ID
        # Polymarket condition IDs are usually hex strings
        test_ids = [
            "0x" + "0" * 64,  # Placeholder
            "will-elon-register-the-america-party-by",  # Try slug as ID
        ]
        
        for test_id in test_ids:
            try:
                response = await client.get(
                    f"https://clob.polymarket.com/markets/{test_id}",
                    timeout=10.0
                )
                print(f"\nDirect lookup '{test_id[:20]}...': {response.status_code}")
            except Exception as e:
                print(f"\nDirect lookup '{test_id[:20]}...': Error - {e}")


if __name__ == "__main__":
    asyncio.run(check_clob())