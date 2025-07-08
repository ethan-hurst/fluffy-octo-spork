#!/usr/bin/env python3
"""Test script to check what markets are being fetched."""

import asyncio
from src.clients.polymarket.client import PolymarketClient

async def test_markets():
    async with PolymarketClient() as client:
        # Get raw markets directly
        response = await client.get_markets(limit=10)
        print(f'Found {len(response.data)} markets from API')
        print('\nFirst 10 markets:')
        for i, m in enumerate(response.data[:10]):
            print(f'\n{i+1}. {m.question[:80]}...')
            print(f'   ID: {m.condition_id}')
            print(f'   Slug: {m.market_slug}')
            print(f'   Active: {m.active}, Closed: {m.closed}')
            if m.volume:
                print(f'   Volume: ${m.volume:,.2f}')
            else:
                print('   Volume: N/A')
            print(f'   URL: https://polymarket.com/event/{m.market_slug}')

if __name__ == "__main__":
    asyncio.run(test_markets())