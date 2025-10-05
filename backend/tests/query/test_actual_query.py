"""Test our actual generated query"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test(query, description):
    api_key = os.getenv('EUROPEANA_API_KEY')
    api_url = "https://api.europeana.eu/record/v2/search.json"
    
    params = {'wskey': api_key, 'query': query, 'rows': 5, 'media': 'true', 'thumbnail': 'true'}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=params)
        data = response.json()
    
    total = data.get('totalResults', 0)
    print(f"{description}")
    print(f"  Query: {query[:80]}...")
    print(f"  Results: {total:,}\n")
    return total

async def main():
    # Our actual generated query
    full_query = "exploring creation dreamlike landscapes digital art Surrealism Contemporary Art AND TYPE:IMAGE"
    
    await test(full_query, "1. Full query (all keywords)")
    
    # Simplified - core theme terms only
    await test("dreamlike surrealism digital AND TYPE:IMAGE", "2. Simplified (3 keywords)")
    
    # Even simpler
    await test("surrealism digital art AND TYPE:IMAGE", "3. Basic (3 keywords)")
    
    # With movement focus
    await test("Surrealism Contemporary art AND TYPE:IMAGE", "4. Movement focus")

asyncio.run(main())
