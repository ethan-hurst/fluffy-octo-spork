#!/usr/bin/env python3
"""
Test if we can access the market page directly and extract info
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
import json
import re

async def test_live_url():
    """Try to access the market page directly."""
    
    url = "https://polymarket.com/event/israel-x-hamas-ceasefire-by-july-15"
    
    async with httpx.AsyncClient() as client:
        print(f"Accessing: {url}\n")
        
        # Try to get the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = await client.get(url, headers=headers, follow_redirects=True)
            print(f"Status: {response.status_code}")
            print(f"Final URL: {response.url}")
            
            if response.status_code == 200:
                # Check if it's a 404 page
                if "404" in response.text or "not found" in response.text.lower():
                    print("\n❌ This appears to be a 404 page")
                else:
                    print("\n✅ Page loaded successfully")
                    
                    # Try to extract condition ID from the page
                    # Look for patterns like conditionId or condition_id in JavaScript
                    condition_pattern = r'["\']condition[_]?[iI]d["\']\s*:\s*["\']([^"\']+)["\']'
                    matches = re.findall(condition_pattern, response.text)
                    
                    if matches:
                        print(f"\nFound condition IDs in page:")
                        for match in set(matches):
                            print(f"  - {match}")
                    
                    # Look for market data in script tags
                    soup = BeautifulSoup(response.text, 'html.parser')
                    scripts = soup.find_all('script')
                    
                    for script in scripts:
                        if script.string and ('market' in script.string or 'condition' in script.string):
                            # Look for JSON data
                            json_pattern = r'\{[^{}]*"(market|condition|slug)"[^{}]*\}'
                            json_matches = re.findall(json_pattern, script.string)
                            if json_matches:
                                print(f"\nFound potential market data in script tag")
                                break
                    
                    # Check __NEXT_DATA__ for Next.js apps
                    next_data = soup.find('script', id='__NEXT_DATA__')
                    if next_data and next_data.string:
                        try:
                            data = json.loads(next_data.string)
                            print("\nFound __NEXT_DATA__")
                            
                            # Navigate through the data structure
                            if 'props' in data and 'pageProps' in data['props']:
                                page_props = data['props']['pageProps']
                                print(f"Page props keys: {list(page_props.keys())[:10]}")
                                
                                # Look for market data
                                for key in ['market', 'event', 'condition', 'data']:
                                    if key in page_props:
                                        print(f"\nFound '{key}' in pageProps")
                                        if isinstance(page_props[key], dict):
                                            for k, v in page_props[key].items():
                                                if 'id' in k.lower() or 'slug' in k.lower():
                                                    print(f"  {k}: {v}")
                        except json.JSONDecodeError:
                            print("Could not parse __NEXT_DATA__")
            
            else:
                print(f"\n❌ Failed to load page: {response.status_code}")
                
        except Exception as e:
            print(f"\n❌ Error accessing page: {e}")
        
        # Also try the API with the exact slug from the URL
        print("\n\nTrying API with exact slug...")
        try:
            # Try gamma API with the slug
            response = await client.get(
                "https://gamma-api.polymarket.com/markets",
                params={"slug": "israel-x-hamas-ceasefire-by-july-15"},
                timeout=10.0
            )
            print(f"API response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Found {len(data)} markets")
                if data:
                    print(f"First market: {data[0].get('question', 'No question')}")
        except Exception as e:
            print(f"API error: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_url())