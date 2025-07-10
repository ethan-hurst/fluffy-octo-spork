#!/usr/bin/env python3
"""
Check what response we're getting
"""

import httpx
import asyncio

async def check_response():
    """Check the actual response."""
    
    url = "https://polymarket.com/event/will-elon-register-the-america-party-by"
    
    async with httpx.AsyncClient() as client:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=20.0)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Save response to file for inspection
        with open('response.html', 'w') as f:
            f.write(response.text)
        
        print(f"\nSaved response to response.html")
        print(f"First 500 chars:\n{response.text[:500]}")
        
        # Check for common patterns
        if "cloudflare" in response.text.lower():
            print("\n⚠️ Cloudflare detected")
        if "please wait" in response.text.lower():
            print("\n⚠️ Loading/waiting page detected")
        if "javascript" in response.text.lower() and "enable" in response.text.lower():
            print("\n⚠️ JavaScript required message detected")


if __name__ == "__main__":
    asyncio.run(check_response())