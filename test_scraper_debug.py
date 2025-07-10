#!/usr/bin/env python3
"""
Debug the web scraper
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
import json

async def debug_scraper():
    """Debug web scraping."""
    
    url = "https://polymarket.com/event/will-elon-register-the-america-party-by"
    
    print(f"Testing scraper on: {url}\n")
    
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
        
        try:
            print("1. Fetching page...")
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=20.0)
            
            print(f"   Status: {response.status_code}")
            print(f"   Final URL: {response.url}")
            print(f"   Content length: {len(response.text)}")
            
            # Check for 404
            if "<title>404" in response.text:
                print("   ❌ 404 page detected")
            elif "Page not found" in response.text:
                print("   ❌ Page not found detected")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check title
            title = soup.find('title')
            if title:
                print(f"\n2. Title: {title.text}")
            
            # Look for __NEXT_DATA__
            next_data_script = soup.find('script', id='__NEXT_DATA__')
            if next_data_script:
                print("\n3. Found __NEXT_DATA__ script")
                
                try:
                    next_data = json.loads(next_data_script.string)
                    print("   ✓ Successfully parsed JSON")
                    
                    # Explore the structure
                    print("\n4. Exploring data structure:")
                    
                    def explore_dict(d, path="", max_depth=3, current_depth=0):
                        if current_depth >= max_depth:
                            return
                        
                        for key, value in d.items():
                            current_path = f"{path}.{key}" if path else key
                            
                            if key in ['market', 'event', 'data', 'question', 'price', 'volume']:
                                print(f"   Found: {current_path}")
                                if isinstance(value, dict):
                                    print(f"     Keys: {list(value.keys())[:10]}")
                                elif isinstance(value, (str, int, float)):
                                    print(f"     Value: {str(value)[:100]}")
                            
                            if isinstance(value, dict) and key in ['props', 'pageProps', 'data', 'market', 'event']:
                                explore_dict(value, current_path, max_depth, current_depth + 1)
                    
                    explore_dict(next_data)
                    
                    # Try to extract market data
                    props = next_data.get('props', {})
                    page_props = props.get('pageProps', {})
                    
                    print("\n5. pageProps keys:", list(page_props.keys())[:20])
                    
                    # Save a sample for analysis
                    with open('next_data_sample.json', 'w') as f:
                        json.dump(page_props, f, indent=2)
                    print("\n   Saved pageProps to next_data_sample.json for analysis")
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse JSON: {e}")
            else:
                print("\n3. ❌ No __NEXT_DATA__ script found")
                
                # Look for other data sources
                scripts = soup.find_all('script')
                print(f"\n   Found {len(scripts)} script tags")
                
                for i, script in enumerate(scripts[:5]):
                    if script.string and len(script.string) > 100:
                        preview = script.string[:200].replace('\n', ' ')
                        print(f"\n   Script {i}: {preview}...")
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_scraper())