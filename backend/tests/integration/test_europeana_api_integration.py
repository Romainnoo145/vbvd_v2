"""
Test generated queries against LIVE Europeana API
Validates that our queries actually work and return good data
"""

import sys
import asyncio
import os
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.query.europeana_query_builder import EuropeanaQueryBuilder
from backend.models import CuratorBrief
from backend.clients.essential_data_client import EssentialDataClient

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Test data
curator_brief = CuratorBrief(
    theme_title="Surrealisme in het Digitale Tijdperk",
    theme_description="Een tentoonstelling die de invloed van surrealistische principes op hedendaagse digitale kunst onderzoekt.",
    art_movements=["surrealism", "contemporary"],
    media_types=["photography", "video_art", "installation"],
    time_period="contemporary",
    geographic_focus=["Netherlands", "Belgium", "Germany", "France"],
    target_audience="general",
    duration_weeks=16
)

exhibition_sections = [
    {
        "title": "Dromen in Pixels",
        "focus": "Exploring the creation of dreamlike landscapes in digital art.",
        "estimated_artwork_count": 8
    }
]

async def test_europeana_api():
    print("=" * 80)
    print("TESTING EUROPEANA API INTEGRATION")
    print("=" * 80)
    print()

    # Check API key
    api_key = os.getenv('EUROPEANA_API_KEY')
    if not api_key:
        print("❌ EUROPEANA_API_KEY not found in environment!")
        print("   Please set it in .env file")
        return

    print(f"✓ Europeana API Key found: {api_key[:10]}...")
    print()

    # Initialize components
    query_builder = EuropeanaQueryBuilder(curator_brief)
    data_client = EssentialDataClient()

    # Build query
    queries = query_builder.build_section_queries(exhibition_sections)
    test_query = queries[0]

    print(f"Testing Query for: {test_query.section_title}")
    print(f"Main Query: {test_query.query}")
    print(f"Filters: {', '.join(test_query.qf[:3])}... ({len(test_query.qf)} total)")
    print()
    print("-" * 80)
    print()

    # Build Europeana API parameters
    params = {
        'query': test_query.query,
        'qf': test_query.qf,
        'rows': 10,  # Just 10 for testing
        'profile': 'rich'
    }

    print("Calling Europeana API...")
    print(f"URL: https://api.europeana.eu/record/v2/search.json")
    print(f"Params: {params}")
    print()

    try:
        # Make direct API call to Europeana
        import httpx

        api_url = "https://api.europeana.eu/record/v2/search.json"
        api_params = {
            'wskey': api_key,
            'query': test_query.query,
            'rows': 10,
            'profile': 'rich',
            'media': 'true',
            'thumbnail': 'true'
        }

        # Add qf filters
        if test_query.qf:
            api_params['qf'] = test_query.qf

        async with httpx.AsyncClient(timeout=30.0) as client:
            api_response = await client.get(api_url, params=api_params)
            api_response.raise_for_status()
            response = api_response.json()

        print("=" * 80)
        print("API RESPONSE ANALYSIS")
        print("=" * 80)
        print()

        if 'totalResults' in response:
            total = response['totalResults']
            print(f"✅ Total Results Available: {total:,}")

            if total == 0:
                print("❌ PROBLEM: Query returned 0 results!")
                print("   Filters may be too restrictive")
                return False
            elif total < 20:
                print(f"⚠️  WARNING: Only {total} results - query might be too narrow")
            elif total > 5000:
                print(f"⚠️  WARNING: {total} results - query very broad")
            else:
                print(f"✓ Good result count ({total} artworks)")

        print()

        if 'items' in response and response['items']:
            items = response['items']
            print(f"✅ Returned {len(items)} sample artworks")
            print()
            print("-" * 80)
            print("SAMPLE ARTWORKS:")
            print("-" * 80)
            print()

            for i, item in enumerate(items[:3], 1):
                print(f"Artwork {i}:")
                print(f"  Title: {item.get('title', ['Unknown'])[0]}")

                # Creator
                creator = item.get('dcCreator', ['Unknown'])
                if isinstance(creator, list):
                    creator = creator[0] if creator else 'Unknown'
                print(f"  Artist: {creator}")

                # Year
                year = item.get('year', ['Unknown'])
                if isinstance(year, list):
                    year = year[0] if year else 'Unknown'
                print(f"  Year: {year}")

                # Type
                dc_type = item.get('type', 'Unknown')
                print(f"  Type: {dc_type}")

                # Country
                country = item.get('country', ['Unknown'])
                if isinstance(country, list):
                    country = ', '.join(country)
                print(f"  Country: {country}")

                # Provider
                provider = item.get('dataProvider', ['Unknown'])
                if isinstance(provider, list):
                    provider = provider[0] if provider else 'Unknown'
                print(f"  Institution: {provider}")

                print()

            # Analyze filter effectiveness
            print("-" * 80)
            print("FILTER EFFECTIVENESS:")
            print("-" * 80)
            print()

            # Check TYPE filter
            image_count = sum(1 for item in items if item.get('type') == 'IMAGE')
            print(f"TYPE:IMAGE filter: {image_count}/{len(items)} items are IMAGE type")
            if image_count == len(items):
                print("  ✓ TYPE filter working perfectly")
            else:
                print(f"  ⚠️  {len(items) - image_count} non-IMAGE items found")

            # Check YEAR filter
            years = []
            for item in items:
                year = item.get('year')
                if year and isinstance(year, list) and year[0]:
                    try:
                        years.append(int(year[0]))
                    except:
                        pass

            if years:
                in_range = sum(1 for y in years if 1970 <= y <= 2025)
                print(f"YEAR:[1970 TO 2025] filter: {in_range}/{len(years)} items in range")
                if in_range == len(years):
                    print("  ✓ YEAR filter working perfectly")
                else:
                    print(f"  ⚠️  {len(years) - in_range} items outside range")
                print(f"  Year range: {min(years)} - {max(years)}")

            # Check COUNTRY filter
            countries = {}
            for item in items:
                country = item.get('country', [])
                if isinstance(country, list):
                    for c in country:
                        countries[c] = countries.get(c, 0) + 1

            print(f"COUNTRY filters: Found countries: {', '.join(countries.keys())}")
            expected = ["Netherlands", "Belgium", "Germany", "France"]
            unexpected = [c for c in countries.keys() if c not in expected]
            if unexpected:
                print(f"  ⚠️  Unexpected countries: {', '.join(unexpected)}")
            else:
                print("  ✓ All countries match filter")

            print()
            print("=" * 80)
            print("✅ API INTEGRATION TEST SUCCESSFUL!")
            print("=" * 80)
            print()
            print(f"Summary: {total:,} artworks available matching theme criteria")
            print("Next step: Extract artists from these artworks")

            return True

        else:
            print("❌ No items in response")
            print(f"Response keys: {response.keys()}")
            return False

    except Exception as e:
        print("=" * 80)
        print("❌ API CALL FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_europeana_api())
    sys.exit(0 if success else 1)
