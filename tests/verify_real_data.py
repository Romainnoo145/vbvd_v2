#!/usr/bin/env python3
"""
Verify Real Data Test
Shows actual API calls and responses to prove we're using real data, not mocks
"""

import asyncio
import sys
import json
from pathlib import Path
import httpx

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.clients import EssentialDataClient
from backend.config import data_config


async def show_actual_api_calls():
    """
    Demonstrate actual API calls with raw responses
    This proves we're using real data, not mock-ups
    """
    print("\n" + "="*70)
    print("🔍 REAL API VERIFICATION TEST")
    print("="*70)
    print("\nThis test shows actual API calls and raw responses")
    print("to prove we're using real live data, not mock-ups.\n")

    async with EssentialDataClient() as client:

        # Test 1: Direct Wikipedia API call
        print("1️⃣ DIRECT WIKIPEDIA API TEST")
        print("-" * 50)

        query = "Impressionism"
        api_url = data_config.get_endpoint_url('wikipedia', 'api')
        headers = data_config.get_headers('wikipedia')

        print(f"🌐 Making real API call to:")
        print(f"   URL: {api_url}")
        print(f"   Query: {query}")
        print(f"   Headers: {headers}")

        # Show actual HTTP request
        search_params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': f"{query} art movement",
            'srlimit': 2,
            'srprop': 'snippet|size'
        }

        response = await client.client.get(api_url, params=search_params, headers=headers)

        print(f"\n📡 Response Status: {response.status_code}")
        print(f"📦 Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n📄 Raw JSON Response (first 500 chars):")
            print(json.dumps(data, indent=2)[:500] + "...")

            # Show actual search results
            search_results = data.get('query', {}).get('search', [])
            print(f"\n✅ Found {len(search_results)} real Wikipedia articles:")

            for i, result in enumerate(search_results, 1):
                print(f"\n   {i}. {result['title']}")
                print(f"      Page ID: {result['pageid']}")
                print(f"      Size: {result['size']} bytes")
                print(f"      Snippet: {result['snippet'][:100]}...")

        # Test 2: Get full article summary
        print("\n\n2️⃣ WIKIPEDIA ARTICLE SUMMARY TEST")
        print("-" * 50)

        article_title = "Impressionism"
        summary_url = data_config.get_endpoint_url('wikipedia', 'summary', title=article_title)

        print(f"🌐 Fetching real article summary:")
        print(f"   URL: {summary_url}")

        summary_response = await client.client.get(summary_url, headers=headers)

        print(f"\n📡 Response Status: {summary_response.status_code}")

        if summary_response.status_code == 200:
            summary_data = summary_response.json()

            print(f"\n📄 Article Details:")
            print(f"   Title: {summary_data.get('title', 'N/A')}")
            print(f"   Page ID: {summary_data.get('pageid', 'N/A')}")
            print(f"   Last Modified: {summary_data.get('timestamp', 'N/A')}")
            print(f"   Extract Length: {len(summary_data.get('extract', ''))} characters")

            print(f"\n📖 First 200 characters of real article:")
            print(f"   \"{summary_data.get('extract', '')[:200]}...\"")

        # Test 3: Show Getty API configuration (even though it might not work)
        print("\n\n3️⃣ GETTY API CONFIGURATION TEST")
        print("-" * 50)

        getty_url = data_config.get_endpoint_url('getty_vocabularies', 'sparql')
        getty_headers = data_config.get_headers('getty_vocabularies')

        print(f"🌐 Getty SPARQL Endpoint:")
        print(f"   URL: {getty_url}")
        print(f"   Headers: {getty_headers}")

        # Show the actual SPARQL query we would send
        sparql_query = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX aat: <http://vocab.getty.edu/aat/>

        SELECT ?subject ?label WHERE {
            ?subject a skos:Concept ;
                    skos:prefLabel ?label ;
                    skos:inScheme aat: .
            FILTER(CONTAINS(LCASE(?label), "impressionism"))
        }
        LIMIT 5
        """

        print(f"\n📝 Real SPARQL Query we send:")
        print(sparql_query)

        try:
            getty_response = await client.client.post(
                getty_url,
                data={'query': sparql_query},
                headers={'Accept': 'application/sparql-results+json'}
            )
            print(f"\n📡 Getty Response Status: {getty_response.status_code}")
            if getty_response.status_code == 200:
                print("✅ Getty API is working!")
                getty_data = getty_response.json()
                print(f"📄 Getty response preview: {str(getty_data)[:200]}...")
            else:
                print(f"⚠️  Getty API returned status {getty_response.status_code}")
                print(f"   Response: {getty_response.text[:200]}...")
        except Exception as e:
            print(f"⚠️  Getty API error: {e}")

        # Test 4: Show actual vs potential Brave Search
        print("\n\n4️⃣ BRAVE SEARCH API TEST")
        print("-" * 50)

        brave_key = data_config.get_api_key('brave_search')
        brave_url = data_config.get_endpoint_url('brave_search', 'web')

        if brave_key:
            print(f"🔑 Brave API Key: {'*' * (len(brave_key) - 8) + brave_key[-8:]}")
            print(f"🌐 Brave API URL: {brave_url}")
            print("✅ Would make real API calls to Brave Search")
        else:
            print("⚠️  No Brave API key configured")
            print(f"🌐 Would use URL: {brave_url}")
            print("📝 Would send real web search queries for current art information")

        # Test 5: Our search method with real data
        print("\n\n5️⃣ OUR SEARCH METHOD WITH REAL DATA")
        print("-" * 50)

        print("🔍 Running our search method with real APIs...")
        results = await client._search_wikipedia("Claude Monet", "French impressionist painter")

        print(f"\n✅ Our method returned {len(results)} real results:")
        for i, result in enumerate(results, 1):
            print(f"\n   {i}. {result['title']}")
            print(f"      Source: {result['source']}")
            print(f"      URL: {result['url']}")
            print(f"      Word Count: {result.get('word_count', 'N/A')}")
            print(f"      Summary: {result['summary'][:100]}...")


async def test_api_endpoints_status():
    """Test which APIs are actually working"""

    print("\n" + "="*70)
    print("🏥 API HEALTH CHECK")
    print("="*70)

    endpoints_to_test = [
        {
            'name': 'Wikipedia API',
            'url': 'https://en.wikipedia.org/w/api.php',
            'test_params': {'action': 'query', 'format': 'json', 'meta': 'siteinfo'}
        },
        {
            'name': 'Wikipedia REST API',
            'url': 'https://en.wikipedia.org/api/rest_v1/page/summary/Test',
            'test_params': {}
        },
        {
            'name': 'Wikidata SPARQL',
            'url': 'https://query.wikidata.org/sparql',
            'test_params': {}
        },
        {
            'name': 'Getty SPARQL',
            'url': 'http://vocab.getty.edu/sparql.json',
            'test_params': {}
        },
        {
            'name': 'Yale LUX Search',
            'url': 'https://lux.collections.yale.edu/api/search',
            'test_params': {'q': 'test', 'type': 'HumanMadeObject', 'page': 1, 'pageSize': 1}
        }
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints_to_test:
            try:
                print(f"\n🔍 Testing {endpoint['name']}...")
                print(f"   URL: {endpoint['url']}")

                if endpoint['test_params']:
                    response = await client.get(endpoint['url'], params=endpoint['test_params'])
                else:
                    response = await client.get(endpoint['url'])

                print(f"   Status: {response.status_code}")

                if response.status_code == 200:
                    print(f"   ✅ Working! Response size: {len(response.content)} bytes")
                elif response.status_code in [301, 302, 403]:
                    print(f"   ⚠️  Redirect/Access issue (status {response.status_code})")
                else:
                    print(f"   ❌ Error (status {response.status_code})")

            except Exception as e:
                print(f"   ❌ Connection failed: {e}")


if __name__ == "__main__":
    print("What would you like to test?")
    print("1. Show actual API calls and responses")
    print("2. Test API endpoint availability")
    print("3. Both tests")

    choice = input("\nEnter choice (1, 2, or 3): ").strip()

    if choice == "1":
        asyncio.run(show_actual_api_calls())
    elif choice == "2":
        asyncio.run(test_api_endpoints_status())
    else:
        print("Running both tests...")
        asyncio.run(test_api_endpoints_status())
        asyncio.run(show_actual_api_calls())