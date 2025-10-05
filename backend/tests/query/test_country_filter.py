"""
Test if COUNTRY filter works with current query structure
"""

import sys
import asyncio
import os
import httpx
from dotenv import load_dotenv

sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

load_dotenv()  # Load .env file
API_KEY = os.getenv('EUROPEANA_API_KEY')
API_URL = "https://api.europeana.eu/record/v2/search.json"

async def test_query(description, query, qf=None):
    """Test a single query configuration"""
    print(f"\nTest: {description}")
    print(f"Query: {query}")
    if qf:
        print(f"QF: {qf}")
    print("-" * 80)

    params = {
        'wskey': API_KEY,
        'query': query,
        'rows': 100,
        'profile': 'rich',
        'media': 'true',
        'thumbnail': 'true'
    }

    if qf:
        params['qf'] = qf

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()

        total_results = data.get('totalResults', 0)
        items = data.get('items', [])

        print(f"Total Available: {total_results:,}")
        print(f"Fetched: {len(items)}")

        if items:
            # Country distribution
            from collections import Counter
            countries = Counter()
            for item in items:
                country = item.get('country', [])
                if isinstance(country, list):
                    countries.update(country)
                elif country:
                    countries[country] += 1

            print("\nCountry Distribution:")
            for country, count in countries.most_common(5):
                print(f"  {country}: {count} ({count/len(items)*100:.1f}%)")

        return total_results, len(items)

    except Exception as e:
        print(f"❌ Error: {e}")
        return 0, 0

async def main():
    print("=" * 80)
    print("TESTING COUNTRY FILTERS")
    print("=" * 80)

    # Test 1: Original query (no filter)
    await test_query(
        "Original (no COUNTRY filter)",
        "(Surrealism OR \"Contemporary Art\" OR creation OR dreamlike) AND TYPE:IMAGE"
    )

    # Test 2: Add COUNTRY as qf parameter
    await test_query(
        "With qf COUNTRY filter",
        "(Surrealism OR \"Contemporary Art\" OR creation OR dreamlike) AND TYPE:IMAGE",
        qf="COUNTRY:(Netherlands OR Belgium OR Germany OR France)"
    )

    # Test 3: Add COUNTRY in main query
    await test_query(
        "COUNTRY in main query",
        "(Surrealism OR \"Contemporary Art\" OR creation OR dreamlike) AND TYPE:IMAGE AND COUNTRY:(Netherlands OR Belgium OR Germany OR France)"
    )

    # Test 4: Simpler query with COUNTRY
    await test_query(
        "Simple query with COUNTRY filter",
        "Surrealism AND TYPE:IMAGE",
        qf="COUNTRY:(Netherlands OR Belgium OR Germany OR France)"
    )

    # Test 5: Multiple qf parameters
    await test_query(
        "Multiple qf as list",
        "(Surrealism OR \"Contemporary Art\") AND TYPE:IMAGE",
        qf=["COUNTRY:Netherlands", "COUNTRY:Belgium", "COUNTRY:Germany", "COUNTRY:France"]
    )

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
