#!/usr/bin/env python3
"""
Check response headers
"""

import httpx
import asyncio

async def check_headers():
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
        
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=20.0)
        
        print(f"Status: {response.status_code}")
        print(f"\nHeaders:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
        
        print(f"\nContent length: {len(response.content)} bytes")
        print(f"Text length: {len(response.text)} characters")
        
        # Check encoding
        print(f"\nEncoding: {response.encoding}")
        
        # Save properly decoded content
        with open('decoded_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print("\nSaved decoded response to decoded_response.html")

if __name__ == "__main__":
    asyncio.run(check_headers())