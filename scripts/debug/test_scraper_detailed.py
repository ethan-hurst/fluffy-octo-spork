#!/usr/bin/env python3
"""
Detailed test of the scraping process
"""

import httpx
import asyncio
import re
from bs4 import BeautifulSoup

async def test_scraping():
    """Test each step of scraping."""
    
    url = "https://polymarket.com/event/will-elon-register-the-america-party-by"
    
    async with httpx.AsyncClient() as client:
        # Step 1: Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print("1. Fetching page...")
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=20.0)
        print(f"   Status: {response.status_code}")
        
        # Step 2: Try regex extraction
        print("\n2. Trying regex extraction...")
        match = re.search(r'property="fc:frame:image"\s+content="[^"]*?/market/(0x[0-9a-f]+)', response.text)
        if match:
            condition_id = match.group(1)
            print(f"   ✅ Found condition ID: {condition_id}")
            
            # Step 3: Try CLOB API
            print("\n3. Fetching from CLOB API...")
            clob_url = f"https://clob.polymarket.com/markets/{condition_id}"
            print(f"   URL: {clob_url}")
            
            clob_response = await client.get(clob_url, timeout=10.0)
            print(f"   Status: {clob_response.status_code}")
            
            if clob_response.status_code == 200:
                data = clob_response.json()
                print("   ✅ Got market data!")
                print(f"   Keys: {list(data.keys())[:10]}")
                
                # Check for important fields
                for field in ['question', 'description', 'volume', 'liquidity', 'last_trade_price', 'price', 'outcomes']:
                    if field in data:
                        value = data[field]
                        if isinstance(value, (str, int, float)):
                            print(f"   {field}: {str(value)[:100]}")
                        elif isinstance(value, list):
                            print(f"   {field}: List with {len(value)} items")
                        elif isinstance(value, dict):
                            print(f"   {field}: Dict with keys {list(value.keys())[:5]}")
            else:
                print(f"   ❌ Failed to get data: {clob_response.text[:200]}")
        else:
            print("   ❌ Could not find condition ID in HTML")
            
            # Debug: Show where we're looking
            print("\n   Searching for pattern in HTML...")
            if 'fc:frame:image' in response.text:
                print("   Found 'fc:frame:image' in HTML")
                # Find the context
                idx = response.text.find('fc:frame:image')
                context = response.text[max(0, idx-50):idx+200]
                print(f"   Context: {context}")
            else:
                print("   'fc:frame:image' not found in HTML")


if __name__ == "__main__":
    asyncio.run(test_scraping())