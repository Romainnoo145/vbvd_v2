"""Test media type filter with .en suffix"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def main():
    api_key = os.getenv('EUROPEANA_API_KEY')
    api_url = "https://api.europeana.eu/record/v2/search.json"
    
    query = "surrealism art AND TYPE:IMAGE"
    
    # Test without media filter
    print("1. Without media filter:")
    params = {'wskey': api_key, 'query': query, 'rows': 5}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=params)
        data = response.json()
    print(f"   Results: {data.get('totalResults', 0):,}\n")
    
    # Test with single media filter
    print("2. With single media filter (proxy_dc_type.en:\"photography\"):")
    params = {
        'wskey': api_key, 
        'query': query, 
        'qf': ['proxy_dc_type.en:"photography"'],
        'rows': 5
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=params)
        data = response.json()
    print(f"   Results: {data.get('totalResults', 0):,}\n")
    
    # Test with media parameter instead
    print("3. With media=true parameter:")
    params = {
        'wskey': api_key, 
        'query': query,
        'media': 'true',
        'rows': 5
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=params)
        data = response.json()
    print(f"   Results: {data.get('totalResults', 0):,}\n")

asyncio.run(main())
