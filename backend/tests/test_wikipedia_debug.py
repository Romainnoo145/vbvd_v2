"""
Debug Wikipedia API - step by step
"""
import asyncio
import httpx
from backend.config import data_config

async def test_wikipedia_raw():
    """Test Wikipedia API with raw HTTP call"""
    print("=" * 80)
    print("TESTING WIKIPEDIA API - RAW HTTP")
    print("=" * 80)

    # Get config
    api_url = data_config.get_endpoint_url('wikipedia', 'api')
    headers = data_config.get_headers('wikipedia')

    print(f"\n📍 API URL: {api_url}")
    print(f"📋 Headers: {headers}")

    # Build search params
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'search',
        'srsearch': 'geometric abstraction art',
        'srlimit': 5,
        'srprop': 'snippet|size|wordcount'
    }

    print(f"\n🔍 Search params: {params}")

    # Make request
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n📡 Making request...")
        response = await client.get(api_url, params=params, headers=headers)

        print(f"✅ Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n📦 Response keys: {list(data.keys())}")

            if 'query' in data:
                query_data = data['query']
                print(f"📦 Query keys: {list(query_data.keys())}")

                if 'search' in query_data:
                    results = query_data['search']
                    print(f"\n✅ Found {len(results)} results")

                    if results:
                        first = results[0]
                        print(f"\n🎯 First result:")
                        print(f"   Title: {first.get('title')}")
                        print(f"   Snippet: {first.get('snippet', 'NO SNIPPET')[:100]}...")
                else:
                    print("❌ No 'search' in query data")
            else:
                print("❌ No 'query' in response data")
                print(f"   Data: {data}")
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_wikipedia_raw())
