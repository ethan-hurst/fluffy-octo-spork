#!/usr/bin/env python3
"""
Save the actual response we're getting
"""

import httpx
import asyncio

async def save_response():
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
        
        with open('actual_response.html', 'w') as f:
            f.write(response.text)
        
        print(f"Saved response: {len(response.text)} bytes")
        
        # Check what we have
        if 'fc:frame' in response.text:
            print("✅ fc:frame found in response")
        else:
            print("❌ fc:frame NOT found in response")
            
        # Check for other patterns
        if 'condition' in response.text.lower():
            print("✅ 'condition' found in response")
        if '0x' in response.text:
            print("✅ Hex strings found in response")


if __name__ == "__main__":
    asyncio.run(save_response())