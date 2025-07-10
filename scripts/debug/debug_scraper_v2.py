#!/usr/bin/env python3
"""
Debug scraper in detail
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def debug_scraper():
    """Debug the scraping process step by step."""
    
    url = "https://polymarket.com/event/will-elon-register-the-america-party-by"
    
    async with httpx.AsyncClient() as client:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print(f"1. Fetching: {url}")
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=20.0)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check title
        title = soup.find('title')
        if title:
            print(f"\n2. Title: {title.text}")
        
        # Look for fc:frame meta tag
        fc_frame_meta = soup.find('meta', {'property': 'fc:frame:image'})
        if fc_frame_meta:
            content = fc_frame_meta.get('content', '')
            print(f"\n3. Found fc:frame:image meta tag:")
            print(f"   Content: {content}")
            
            # Extract condition ID
            match = re.search(r'/market/(0x[0-9a-f]+)', content)
            if match:
                condition_id = match.group(1)
                print(f"   ✅ Extracted condition ID: {condition_id}")
                
                # Try CLOB API
                print(f"\n4. Trying CLOB API with condition ID...")
                clob_url = f"https://clob.polymarket.com/markets/{condition_id}"
                clob_response = await client.get(clob_url, timeout=10.0)
                
                print(f"   Status: {clob_response.status_code}")
                if clob_response.status_code == 200:
                    data = clob_response.json()
                    print(f"   ✅ Got market data!")
                    print(f"   Question: {data.get('question', 'N/A')}")
                    print(f"   Active: {data.get('active', 'N/A')}")
                    print(f"   Volume: {data.get('volume', 'N/A')}")
                    print(f"   Price: {data.get('price', 'N/A')}")
                else:
                    print(f"   ❌ Failed to get market data")
                    print(f"   Response: {clob_response.text[:200]}")
            else:
                print("   ❌ Could not extract condition ID")
        else:
            print("\n3. ❌ No fc:frame:image meta tag found")
            
            # List all meta tags
            print("\n   All meta tags:")
            for meta in soup.find_all('meta')[:10]:
                prop = meta.get('property', meta.get('name', ''))
                content = meta.get('content', '')[:100]
                if prop:
                    print(f"   - {prop}: {content}")


if __name__ == "__main__":
    asyncio.run(debug_scraper())