#!/usr/bin/env python3
"""Test Polymarket gamma API for active markets."""

import httpx
import json
from datetime import datetime

# Test the gamma API for recent active markets
print('Testing Polymarket gamma API for active markets...')
response = httpx.get('https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100')
print(f'Status: {response.status_code}')

if response.status_code == 200:
    markets = response.json()
    
    # Filter for markets that are actually active and have reasonable volume
    active_markets = []
    for m in markets:
        if m.get('active') and not m.get('closed') and not m.get('archived'):
            # Check different volume fields
            volume = (m.get('volume', 0) or 
                     m.get('volume24hrClob', 0) or 
                     m.get('volumeClob', 0) or 
                     m.get('volume1wk', 0) or 0)
            
            # Check if market has a future end date
            end_date_str = m.get('endDate')
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                    if end_date > datetime.now(end_date.tzinfo):
                        m['_volume'] = volume
                        active_markets.append(m)
                except:
                    pass
    
    # Sort by volume
    active_markets.sort(key=lambda x: x.get('_volume', 0), reverse=True)
    
    print(f'\nFound {len(active_markets)} active markets with future end dates')
    
    # Show top 10
    for i, m in enumerate(active_markets[:10]):
        print(f'\n{i+1}. {m.get("question", "No question")[:80]}')
        print(f'   Slug: {m.get("slug")}')
        print(f'   Volume: ${float(m.get("_volume", 0)):,.0f}')
        print(f'   End Date: {m.get("endDate")}')
        print(f'   Active: {m.get("active")}, Closed: {m.get("closed")}')