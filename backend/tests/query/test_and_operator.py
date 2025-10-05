"""Test AND operator in Europeana query"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test(query, description):
    api_key = os.getenv('EUROPEANA_API_KEY')
    api_url = "https://api.europeana.eu/record/v2/search.json"
    
    params = {'wskey': api_key, 'query': query, 'rows': 5, 'media': 'true'}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=params)
        data = response.json()
    
    total = data.get('totalResults', 0)
    print(f"{description}")
    print(f"  Query: {query}")
    print(f"  Results: {total:,}\n")
    return total

async def main():
    # Test 1: Just keywords
    await test("surrealism digital art", "1. Just keywords")
    
    # Test 2: Keywords with AND TYPE:IMAGE
    await test("surrealism digital art AND TYPE:IMAGE", "2. With AND TYPE:IMAGE")
    
    # Test 3: Using qf parameter instead
    api_key = os.getenv('EUROPEANA_API_KEY')
    api_url = "https://api.europeana.eu/record/v2/search.json"
    params = {
        'wskey': api_key, 
        'query': 'surrealism digital art',
        'qf': ['TYPE:IMAGE'],
        'rows': 5,
        'media': 'true'
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=params)
        data = response.json()
    total = data.get('totalResults', 0)
    print(f"3. Using qf=['TYPE:IMAGE']")
    print(f"  Query: surrealism digital art")
    print(f"  qf: ['TYPE:IMAGE']")
    print(f"  Results: {total:,}\n")

asyncio.run(main())
