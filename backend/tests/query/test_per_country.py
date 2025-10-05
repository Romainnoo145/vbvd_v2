"""
Test per-country queries for balanced geographic distribution
"""

import sys
import asyncio
import os
import httpx
from dotenv import load_dotenv

sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

load_dotenv()
API_KEY = os.getenv('EUROPEANA_API_KEY')
API_URL = "https://api.europeana.eu/record/v2/search.json"

async def test_country(country, query, rows=50):
    """Test single-country filter"""
    print(f"\n{'='*80}")
    print(f"Testing: {country}")
    print(f"{'='*80}")

    params = {
        'wskey': API_KEY,
        'query': query,
        'rows': rows,
        'qf': f'COUNTRY:{country}',
        'profile': 'rich',
        'media': 'true',
        'thumbnail': 'true'
    }

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
            # Sample artworks
            print("\nSample Artworks (first 3):")
            for i, item in enumerate(items[:3], 1):
                title = item.get('title', ['Untitled'])
                if isinstance(title, list):
                    title = title[0] if title else 'Untitled'

                creator = item.get('dcCreator', ['Unknown'])
                if isinstance(creator, list):
                    creator = creator[0] if creator else 'Unknown'

                print(f"  {i}. {title}")
                print(f"     Creator: {creator}")

        return total_results, len(items), items

    except Exception as e:
        print(f"❌ Error: {e}")
        return 0, 0, []

async def main():
    print("="*80)
    print("PER-COUNTRY QUERY TEST")
    print("Testing balanced geographic distribution approach")
    print("="*80)

    query = "(Surrealism OR \"Contemporary Art\" OR creation OR dreamlike) AND TYPE:IMAGE"
    countries = ["Netherlands", "Belgium", "Germany", "France"]
    rows_per_country = 50

    results = {}
    all_items = []

    # Test each country separately
    for country in countries:
        total, fetched, items = await test_country(country, query, rows_per_country)
        results[country] = {
            'total_available': total,
            'fetched': fetched,
            'items': items
        }
        all_items.extend(items)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY: Balanced Geographic Distribution")
    print("="*80)

    total_fetched = sum(r['fetched'] for r in results.values())
    print(f"\nTotal Artworks Fetched: {total_fetched}")
    print("\nPer-Country Breakdown:")

    for country, data in results.items():
        percentage = (data['fetched'] / total_fetched * 100) if total_fetched > 0 else 0
        print(f"  {country:15} {data['fetched']:3} artworks ({percentage:5.1f}%) - {data['total_available']:,} available")

    # Check balance
    print("\n" + "="*80)
    print("BALANCE CHECK")
    print("="*80)

    target_percentage = 100 / len(countries)
    print(f"Target: {target_percentage:.1f}% per country")

    balanced = True
    for country, data in results.items():
        percentage = (data['fetched'] / total_fetched * 100) if total_fetched > 0 else 0
        deviation = abs(percentage - target_percentage)

        if deviation < 5:
            status = "✅ BALANCED"
        else:
            status = "⚠️  UNBALANCED"
            balanced = False

        print(f"  {country:15} {percentage:5.1f}% {status}")

    print()
    if balanced:
        print("✅ Geographic distribution is BALANCED!")
    else:
        print("⚠️  Geographic distribution needs adjustment")

    print(f"\n🎯 Result: {total_fetched} artworks from {len(countries)} countries")

if __name__ == "__main__":
    asyncio.run(main())
