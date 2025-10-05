"""
Simple Europeana API test - remove filters one by one
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_query(query, qf_filters, description):
    api_key = os.getenv('EUROPEANA_API_KEY')
    api_url = "https://api.europeana.eu/record/v2/search.json"
    
    api_params = {
        'wskey': api_key,
        'query': query,
        'rows': 10,
        'profile': 'rich',
        'media': 'true',
        'thumbnail': 'true'
    }
    
    if qf_filters:
        api_params['qf'] = qf_filters
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=api_params)
        response.raise_for_status()
        data = response.json()
    
    total = data.get('totalResults', 0)
    print(f"{description}: {total:,} results")
    if qf_filters:
        print(f"  Filters: {qf_filters}")
    print()
    return total

async def main():
    query = "surrealism digital art"
    
    # Test 1: No filters
    await test_query(query, [], "1. No filters")
    
    # Test 2: Just TYPE
    await test_query(query, ['TYPE:IMAGE'], "2. TYPE:IMAGE only")
    
    # Test 3: TYPE + YEAR
    await test_query(query, ['TYPE:IMAGE', 'YEAR:[1970 TO 2025]'], "3. TYPE + YEAR")
    
    # Test 4: TYPE + YEAR + media
    await test_query(query, [
        'TYPE:IMAGE', 
        'YEAR:[1970 TO 2025]',
        'proxy_dc_type:(photography OR "video art" OR installation)'
    ], "4. TYPE + YEAR + media")
    
    # Test 5: TYPE + YEAR + COUNTRY
    await test_query(query, [
        'TYPE:IMAGE', 
        'YEAR:[1970 TO 2025]',
        'COUNTRY:(Netherlands OR Belgium OR Germany OR France)'
    ], "5. TYPE + YEAR + COUNTRY")
    
    # Test 6: All filters
    await test_query(query, [
        'TYPE:IMAGE', 
        'YEAR:[1970 TO 2025]',
        'proxy_dc_type:(photography OR "video art" OR installation)',
        'COUNTRY:(Netherlands OR Belgium OR Germany OR France)'
    ], "6. All filters (original)")

if __name__ == "__main__":
    asyncio.run(main())
