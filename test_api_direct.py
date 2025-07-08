#!/usr/bin/env python3
"""Test Polymarket API directly."""

import httpx
import json

# Test the Polymarket API directly
print("Testing Polymarket CLOB API...")
response = httpx.get('https://clob.polymarket.com/markets?closed=false&active=true&limit=10')
print(f'Status: {response.status_code}')

if response.status_code == 200:
    data = response.json()
    
    # Check if it's a list or has a data field
    if isinstance(data, dict):
        markets = data.get('data', [])
        print(f"\nResponse has 'data' field with {len(markets)} markets")
    else:
        markets = data
        print(f"\nResponse is a list with {len(markets)} markets")
    
    # Print first few markets
    for i, m in enumerate(markets[:5]):
        print(f'\n{i+1}. {m.get("question", "No question")[:80]}')
        print(f'   ID: {m.get("condition_id", "No ID")}')
        print(f'   Active: {m.get("active")}, Closed: {m.get("closed")}')
        print(f'   Volume: {m.get("volume", "N/A")}')
        
    # Print full structure of first market for debugging
    if markets:
        print("\n\nFull structure of first market:")
        print(json.dumps(markets[0], indent=2))
else:
    print(f"Error: {response.text}")