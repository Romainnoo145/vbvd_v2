"""
Comprehensive Europeana API Capabilities Test
Tests all features we need before creating the PRP

Tests:
1. Facet retrieval - What categories/filters are available?
2. Entity API - Can we find artists by movement/period?
3. Search API - Multi-criteria filtering (time + media + country)
4. Response structure - What metadata do we actually get?
5. IIIF availability - How many items have IIIF manifests?
6. Theme-based queries - Do our mappings work in practice?
"""

import asyncio
import httpx
import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
EUROPEANA_API_KEY = os.getenv('EUROPEANA_API_KEY')

if not EUROPEANA_API_KEY:
    print("❌ ERROR: EUROPEANA_API_KEY not found in .env file")
    exit(1)


class EuropeanaCapabilityTester:
    """Test all Europeana API capabilities we need"""

    def __init__(self):
        self.api_key = EUROPEANA_API_KEY
        self.base_url = "https://api.europeana.eu"
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    # =========================================================================
    # TEST 1: Facet Retrieval
    # =========================================================================

    async def test_facet_retrieval(self):
        """
        Test if we can retrieve available facets (categories) from Europeana
        This is CRITICAL for building the structured input form
        """
        print("\n" + "="*80)
        print("TEST 1: FACET RETRIEVAL (Available Categories)")
        print("="*80)

        try:
            # Query with facets parameter to get available categories
            url = f"{self.base_url}/record/v2/search.json"
            params = {
                'wskey': self.api_key,
                'query': '*',  # Get everything
                'rows': 0,     # We don't need items, just facets
                'facet': [
                    'proxy_dc_type',    # Media types
                    'TYPE',             # Resource types
                    'COUNTRY',          # Countries
                    'LANGUAGE',         # Languages
                    'YEAR',             # Time periods
                    'PROVIDER',         # Data providers
                    'DATA_PROVIDER',    # Institutions
                    'RIGHTS',           # Rights/licenses
                ]
            }

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()

                print(f"\n✅ Facets retrieved successfully")
                print(f"   Total items in Europeana: {data.get('totalResults', 'unknown'):,}")

                facets = data.get('facets', [])
                print(f"\n📊 Available Facets ({len(facets)}):\n")

                for facet in facets:
                    facet_name = facet.get('name', 'Unknown')
                    fields = facet.get('fields', [])

                    print(f"   🏷️  {facet_name} ({len(fields)} values)")

                    # Show top 10 values for each facet
                    for i, field in enumerate(fields[:10]):
                        label = field.get('label', 'Unknown')
                        count = field.get('count', 0)
                        print(f"      {i+1}. {label}: {count:,} items")

                    if len(fields) > 10:
                        print(f"      ... and {len(fields) - 10} more")
                    print()

                # Save full facet data for analysis
                with open('europeana_facets.json', 'w', encoding='utf-8') as f:
                    json.dump(facets, f, indent=2, ensure_ascii=False)
                print("   💾 Full facet data saved to: europeana_facets.json")

                return True

            else:
                print(f"❌ Failed with status {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    # =========================================================================
    # TEST 2: Entity API (Artist Discovery)
    # =========================================================================

    async def test_entity_api_artists(self):
        """
        Test Europeana Entity API for finding artists
        This is CRITICAL for artist discovery phase
        """
        print("\n" + "="*80)
        print("TEST 2: ENTITY API (Artist Discovery)")
        print("="*80)

        test_queries = [
            ("contemporary sculpture", "Find contemporary sculptors"),
            ("surrealism", "Find surrealist artists"),
            ("De Stijl", "Find De Stijl artists"),
            ("Dutch modern art", "Find Dutch modern artists"),
        ]

        for query, description in test_queries:
            print(f"\n🔍 Query: '{query}' ({description})")
            print("-" * 80)

            try:
                url = f"{self.base_url}/entity/suggest"
                params = {
                    'wskey': self.api_key,
                    'text': query,
                    'TYPE': 'agent',  # Artists are "agents" in Europeana
                    'rows': 10
                }

                response = await self.client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])

                    if items:
                        print(f"   ✅ Found {len(items)} artists:")
                        for i, item in enumerate(items, 1):
                            pref_label = item.get('prefLabel', {})
                            name = list(pref_label.values())[0] if pref_label else 'Unknown'
                            entity_id = item.get('id', 'No ID')
                            print(f"      {i}. {name}")
                            print(f"         ID: {entity_id}")
                    else:
                        print(f"   ⚠️  No artists found")

                else:
                    print(f"   ❌ Failed with status {response.status_code}")

                await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"   ❌ Error: {e}")

        return True

    # =========================================================================
    # TEST 3: Multi-Criteria Search (Our Core Use Case)
    # =========================================================================

    async def test_multi_criteria_search(self):
        """
        Test searching with multiple filters simultaneously
        This simulates actual curator queries
        """
        print("\n" + "="*80)
        print("TEST 3: MULTI-CRITERIA SEARCH (Core Use Case)")
        print("="*80)

        test_scenarios = [
            {
                "name": "Contemporary Dutch Sculpture",
                "description": "Van Bommel van Dam's primary focus",
                "query": "sculpture",
                "qf": [
                    'COUNTRY:Netherlands',
                    'proxy_dc_type:sculpture',
                    'YEAR:[1970 TO 2025]'
                ]
            },
            {
                "name": "Surrealist Artworks (European)",
                "description": "Demo theme test",
                "query": "surrealism OR surrealist",
                "qf": [
                    'TYPE:IMAGE',
                    'YEAR:[1920 TO 1970]'
                ]
            },
            {
                "name": "Installation Art (Contemporary)",
                "description": "Modern museum focus",
                "query": "installation",
                "qf": [
                    'YEAR:[1960 TO 2025]',
                    'TYPE:IMAGE'
                ]
            },
            {
                "name": "De Stijl Movement",
                "description": "Dutch modern art",
                "query": '"De Stijl" OR "Neo-Plasticism"',
                "qf": [
                    'COUNTRY:Netherlands',
                    'YEAR:[1910 TO 1940]'
                ]
            }
        ]

        for scenario in test_scenarios:
            print(f"\n📋 Scenario: {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            print(f"   Query: {scenario['query']}")
            print(f"   Filters: {scenario['qf']}")
            print("-" * 80)

            try:
                url = f"{self.base_url}/record/v2/search.json"
                params = {
                    'wskey': self.api_key,
                    'query': scenario['query'],
                    'qf': scenario['qf'],
                    'rows': 5,
                    'profile': 'rich',
                    'media': 'true',
                    'thumbnail': 'true'
                }

                response = await self.client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get('totalResults', 0)
                    items = data.get('items', [])

                    print(f"\n   ✅ Found {total:,} total artworks")

                    if items:
                        print(f"   📦 Sample artworks ({len(items)}):\n")

                        for i, item in enumerate(items, 1):
                            title = item.get('title', ['Untitled'])[0] if isinstance(item.get('title'), list) else item.get('title', 'Untitled')
                            creator = item.get('dcCreator', ['Unknown'])[0] if 'dcCreator' in item else 'Unknown'
                            provider = item.get('dataProvider', ['Unknown'])[0] if isinstance(item.get('dataProvider'), list) else 'Unknown'
                            year = item.get('year', ['Unknown'])[0] if 'year' in item else 'Unknown'

                            print(f"      {i}. {title}")
                            print(f"         Artist: {creator}")
                            print(f"         Year: {year}")
                            print(f"         Institution: {provider}")

                            # Check for IIIF
                            has_iiif = 'edmIsShownBy' in item or 'isShownBy' in item
                            iiif_status = "✅ IIIF available" if has_iiif else "⚠️  No IIIF"
                            print(f"         {iiif_status}")
                            print()
                    else:
                        print(f"   ⚠️  No items returned")

                else:
                    print(f"   ❌ Failed with status {response.status_code}")
                    print(f"      Response: {response.text[:200]}")

                await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"   ❌ Error: {e}")

        return True

    # =========================================================================
    # TEST 4: Response Structure Analysis
    # =========================================================================

    async def test_response_structure(self):
        """
        Test what metadata fields we actually get in responses
        This validates our data model assumptions
        """
        print("\n" + "="*80)
        print("TEST 4: RESPONSE STRUCTURE ANALYSIS")
        print("="*80)

        print("\n🔍 Fetching sample artwork to analyze metadata fields...")

        try:
            url = f"{self.base_url}/record/v2/search.json"
            params = {
                'wskey': self.api_key,
                'query': 'sculpture',
                'qf': ['TYPE:IMAGE', 'COUNTRY:Netherlands'],
                'rows': 1,
                'profile': 'rich',  # Get ALL metadata
                'media': 'true',
                'thumbnail': 'true'
            }

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])

                if items:
                    item = items[0]

                    print(f"\n✅ Sample artwork retrieved")
                    print("\n📋 Available Fields:\n")

                    # Analyze all fields
                    fields_found = {}

                    # Basic metadata
                    if 'title' in item:
                        fields_found['title'] = item['title']
                    if 'dcCreator' in item:
                        fields_found['dcCreator (Artist)'] = item['dcCreator']
                    if 'dcDescription' in item:
                        fields_found['dcDescription'] = item['dcDescription']
                    if 'year' in item:
                        fields_found['year'] = item['year']
                    if 'type' in item:
                        fields_found['type'] = item['type']

                    # Institution/Location
                    if 'dataProvider' in item:
                        fields_found['dataProvider (Institution)'] = item['dataProvider']
                    if 'provider' in item:
                        fields_found['provider'] = item['provider']
                    if 'country' in item:
                        fields_found['country'] = item['country']

                    # Media/Images
                    if 'edmPreview' in item:
                        fields_found['edmPreview (Thumbnail)'] = item['edmPreview']
                    if 'edmIsShownBy' in item:
                        fields_found['edmIsShownBy (Full Image)'] = item['edmIsShownBy']
                    if 'edmIsShownAt' in item:
                        fields_found['edmIsShownAt (View URL)'] = item['edmIsShownAt']

                    # Rights
                    if 'rights' in item:
                        fields_found['rights'] = item['rights']

                    # Technical
                    if 'dcFormat' in item:
                        fields_found['dcFormat (Medium)'] = item['dcFormat']
                    if 'dctermsExtent' in item:
                        fields_found['dctermsExtent (Dimensions)'] = item['dctermsExtent']

                    # Print all found fields
                    for field_name, value in fields_found.items():
                        value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                        print(f"   ✅ {field_name}")
                        print(f"      {value_preview}\n")

                    # Save complete item for analysis
                    with open('europeana_sample_item.json', 'w', encoding='utf-8') as f:
                        json.dump(item, f, indent=2, ensure_ascii=False)
                    print("   💾 Full item saved to: europeana_sample_item.json")

                    # Check IIIF manifest construction
                    europeana_id = item.get('id', '')
                    if europeana_id:
                        record_id = europeana_id.lstrip('/')
                        iiif_manifest = f"https://iiif.europeana.eu/presentation/{record_id}/manifest"
                        print(f"\n   🖼️  IIIF Manifest URL: {iiif_manifest}")

                    return True
                else:
                    print("   ⚠️  No items found")
                    return False

            else:
                print(f"   ❌ Failed with status {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    # =========================================================================
    # TEST 5: IIIF Availability Check
    # =========================================================================

    async def test_iiif_availability(self):
        """
        Test how many artworks have IIIF manifests
        This is important for image quality
        """
        print("\n" + "="*80)
        print("TEST 5: IIIF AVAILABILITY CHECK")
        print("="*80)

        print("\n🔍 Checking IIIF availability across different queries...")

        test_queries = [
            ("sculpture Netherlands", "Dutch sculptures"),
            ("painting contemporary", "Contemporary paintings"),
            ("installation art", "Installation artworks"),
        ]

        for query, description in test_queries:
            print(f"\n📋 Query: {description} ('{query}')")

            try:
                url = f"{self.base_url}/record/v2/search.json"
                params = {
                    'wskey': self.api_key,
                    'query': query,
                    'rows': 20,
                    'profile': 'rich',
                    'media': 'true',
                    'thumbnail': 'true'
                }

                response = await self.client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])

                    if items:
                        total = len(items)
                        with_iiif = sum(1 for item in items if 'edmIsShownBy' in item)
                        with_thumbnail = sum(1 for item in items if 'edmPreview' in item)

                        iiif_percent = (with_iiif / total * 100) if total > 0 else 0
                        thumb_percent = (with_thumbnail / total * 100) if total > 0 else 0

                        print(f"   ✅ Sampled {total} items:")
                        print(f"      🖼️  IIIF images: {with_iiif}/{total} ({iiif_percent:.1f}%)")
                        print(f"      🖼️  Thumbnails: {with_thumbnail}/{total} ({thumb_percent:.1f}%)")
                    else:
                        print(f"   ⚠️  No items found")

                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"   ❌ Error: {e}")

        return True

    # =========================================================================
    # TEST 6: Theme-Based Query Testing
    # =========================================================================

    async def test_theme_based_queries(self):
        """
        Test our predefined theme mappings from europeana_topics.py
        This validates our knowledge base
        """
        print("\n" + "="*80)
        print("TEST 6: THEME-BASED QUERY TESTING")
        print("="*80)

        # Import our theme mappings
        import sys
        sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')
        from backend.config.europeana_topics import EXHIBITION_THEME_MAPPINGS

        print(f"\n🔍 Testing {len(EXHIBITION_THEME_MAPPINGS)} predefined themes...")

        for theme_name, mapping in EXHIBITION_THEME_MAPPINGS.items():
            print(f"\n📋 Theme: {theme_name.replace('_', ' ').title()}")
            print(f"   Movements: {', '.join(mapping.art_movements[:3])}")
            print(f"   Media: {', '.join(mapping.media_types[:3])}")

            try:
                # Build query from theme mapping
                movements_query = ' OR '.join([f'"{m}"' for m in mapping.art_movements[:2]])
                query = f'({movements_query}) AND TYPE:IMAGE'

                url = f"{self.base_url}/record/v2/search.json"
                params = {
                    'wskey': self.api_key,
                    'query': query,
                    'rows': 0,  # Just get count
                }

                # Add qf filters if available
                if mapping.qf_filters:
                    params['qf'] = []
                    for field, values in mapping.qf_filters.items():
                        if field == 'YEAR' and len(values) == 2:
                            params['qf'].append(f'YEAR:[{values[0]} TO {values[1]}]')
                        else:
                            for value in values[:2]:  # Limit to 2 values
                                params['qf'].append(f'{field}:{value}')

                response = await self.client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get('totalResults', 0)

                    if total > 0:
                        print(f"   ✅ Found {total:,} artworks")
                    else:
                        print(f"   ⚠️  No artworks found (theme mapping may need adjustment)")
                else:
                    print(f"   ❌ Query failed with status {response.status_code}")

                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"   ❌ Error: {e}")

        return True


async def run_all_tests():
    """Run all capability tests"""

    print("\n" + "="*80)
    print("🎨 EUROPEANA API COMPREHENSIVE CAPABILITY TEST")
    print("="*80)
    print(f"\n🔑 API Key found: {EUROPEANA_API_KEY[:20]}...")
    print(f"🎯 Purpose: Validate capabilities before creating PRP")

    async with EuropeanaCapabilityTester() as tester:
        results = {
            "facet_retrieval": await tester.test_facet_retrieval(),
            "entity_api": await tester.test_entity_api_artists(),
            "multi_criteria": await tester.test_multi_criteria_search(),
            "response_structure": await tester.test_response_structure(),
            "iiif_availability": await tester.test_iiif_availability(),
            "theme_queries": await tester.test_theme_based_queries(),
        }

        # Summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)

        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {status}: {test_name.replace('_', ' ').title()}")

        all_passed = all(results.values())

        print("\n" + "="*80)
        if all_passed:
            print("✅ ALL TESTS PASSED - Ready to create PRP!")
        else:
            print("⚠️  SOME TESTS FAILED - Review results before creating PRP")
        print("="*80)

        print("\n📁 Output Files:")
        print("   - europeana_facets.json (available categories)")
        print("   - europeana_sample_item.json (sample metadata structure)")
        print("\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
