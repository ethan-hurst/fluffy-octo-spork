#!/usr/bin/env python3
"""
Debug CLOB response format
"""

import httpx
import asyncio
import json

async def debug_clob():
    condition_id = "0xd1cb040420a6877ec2b3e5e0901ed2029d85b42d5c1b939cecc27071c8536b0e"
    
    async with httpx.AsyncClient() as client:
        url = f"https://clob.polymarket.com/markets/{condition_id}"
        response = await client.get(url, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            
            # Pretty print the response
            print(json.dumps(data, indent=2))
            
            print("\n\nKey fields:")
            for key in ['question', 'description', 'volume', 'liquidity', 'price', 'last_trade_price', 'outcomes', 'tokens']:
                if key in data:
                    value = data[key]
                    if isinstance(value, (list, dict)):
                        print(f"{key}: {type(value).__name__} with {len(value)} items")
                    else:
                        print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(debug_clob())