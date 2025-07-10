#!/usr/bin/env python3
"""
Test web scraping for Polymarket
"""

import httpx
import asyncio

async def test_scrape():
    """Test scraping the Polymarket page."""
    
    url = "https://polymarket.com/event/will-elon-register-the-america-party-by"
    
    async with httpx.AsyncClient() as client:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"Fetching: {url}")
        
        try:
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
            
            print(f"Status: {response.status_code}")
            print(f"Final URL: {response.url}")
            print(f"Content length: {len(response.text)}")
            
            # Check for key indicators
            if "404" in response.text or "not found" in response.text.lower():
                print("\n❌ Page appears to be 404")
            
            # Look for title
            import re
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_match:
                print(f"\nTitle: {title_match.group(1)}")
            
            # Look for JSON data
            if '__NEXT_DATA__' in response.text:
                print("\n✓ Found __NEXT_DATA__ (Next.js app)")
            
            if '"question"' in response.text:
                print("✓ Found question field")
                
            if '"lastTradePrice"' in response.text:
                print("✓ Found lastTradePrice field")
            
            # Try to extract question
            question_match = re.search(r'"question":\s*"([^"]+)"', response.text)
            if question_match:
                print(f"\nQuestion: {question_match.group(1)}")
                
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_scrape())