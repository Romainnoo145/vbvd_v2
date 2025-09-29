#!/usr/bin/env python3
"""
Test script to verify Essential Data Client functionality
Tests search capabilities across all 5 essential APIs
"""

import asyncio
import sys
import json
from pathlib import Path
from pprint import pprint

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.clients import EssentialDataClient
from backend.config import data_config


async def test_essential_client():
    """Test the Essential Data Client with sample queries"""

    print("=" * 60)
    print("AI CURATOR ASSISTANT - Data Client Test")
    print("=" * 60)

    # Test queries for different contexts
    test_cases = [
        {
            'query': 'Impressionism',
            'context': 'art movement',
            'sources': ['wikipedia', 'getty']
        },
        {
            'query': 'Claude Monet',
            'context': 'artist',
            'sources': ['wikidata', 'getty']
        },
        {
            'query': 'Water Lilies',
            'context': 'artwork',
            'sources': ['wikidata', 'yale_lux']
        }
    ]

    async with EssentialDataClient() as client:
        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test['query']} ({test['context']})")
            print("-" * 40)

            results = await client.search_essential(
                query=test['query'],
                sources=test['sources'],
                context=test['context']
            )

            for source, items in results.items():
                print(f"\n   {source.upper()}: {len(items)} results")
                if items:
                    # Show first result as sample
                    first = items[0]
                    print(f"   Sample: {first.get('title', first.get('label', 'N/A'))[:60]}...")
                    if 'description' in first:
                        print(f"           {first['description'][:60]}...")

    print("\n" + "=" * 60)
    print("CLIENT TEST COMPLETE")
    print("=" * 60)


async def test_parallel_search():
    """Test parallel search across all sources"""

    print("\n" + "=" * 60)
    print("PARALLEL SEARCH TEST")
    print("=" * 60)

    query = "Leonardo da Vinci"
    context = "artist Renaissance"

    # Test all available sources
    sources = ['wikipedia', 'wikidata', 'getty', 'yale_lux']
    if data_config.get_api_key('brave_search'):
        sources.append('brave_search')

    print(f"\nSearching for: '{query}' across {len(sources)} sources")
    print("Sources:", ', '.join(sources))

    start_time = asyncio.get_event_loop().time()

    async with EssentialDataClient() as client:
        results = await client.search_essential(query, sources, context)

    elapsed = asyncio.get_event_loop().time() - start_time

    print(f"\n✅ Parallel search completed in {elapsed:.2f} seconds")
    print("\nResults summary:")
    for source, items in results.items():
        print(f"  - {source}: {len(items)} results")

    # Save sample results to file for inspection
    output_file = Path("sample_results.json")
    with open(output_file, 'w') as f:
        # Convert to serializable format
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Sample results saved to: {output_file}")


async def test_specific_apis():
    """Test individual API methods"""

    print("\n" + "=" * 60)
    print("INDIVIDUAL API TESTS")
    print("=" * 60)

    async with EssentialDataClient() as client:

        # 1. Test Wikipedia summary
        print("\n1. Wikipedia Summary Test:")
        wiki_results = await client._search_wikipedia("Rembrandt", "Dutch artist")
        if wiki_results:
            print(f"   ✓ Found {len(wiki_results)} Wikipedia articles")
            if wiki_results[0].get('summary'):
                print(f"   Summary length: {len(wiki_results[0]['summary'])} chars")
        else:
            print("   ✗ No Wikipedia results")

        # 2. Test Wikidata SPARQL
        print("\n2. Wikidata SPARQL Test:")
        wd_results = await client._search_wikidata("Starry Night", "artwork")
        if wd_results:
            print(f"   ✓ Found {len(wd_results)} Wikidata entities")
            for item in wd_results[:2]:
                print(f"   - {item.get('title', 'N/A')} (ID: {item.get('wikidata_id', 'N/A')})")
        else:
            print("   ✗ No Wikidata results")

        # 3. Test Getty Vocabularies
        print("\n3. Getty Vocabularies Test:")
        getty_results = await client._search_getty("chiaroscuro", "technique")
        if getty_results:
            print(f"   ✓ Found {len(getty_results)} Getty terms")
            for item in getty_results[:2]:
                print(f"   - {item.get('label', 'N/A')} ({item.get('vocabulary', 'N/A')})")
        else:
            print("   ✗ No Getty results")

        # 4. Test Yale LUX
        print("\n4. Yale LUX Test:")
        yale_results = await client._search_yale_lux("portrait", "artwork")
        if yale_results:
            print(f"   ✓ Found {len(yale_results)} Yale LUX objects")
            for item in yale_results[:2]:
                print(f"   - {item.get('title', 'N/A')} (Type: {item.get('type', 'N/A')})")
        else:
            print("   ✗ No Yale LUX results")

        # 5. Test Brave Search (if configured)
        if data_config.get_api_key('brave_search'):
            print("\n5. Brave Search Test:")
            brave_results = await client._search_brave("Venice Biennale 2024", "contemporary art")
            if brave_results:
                print(f"   ✓ Found {len(brave_results)} web results")
                for item in brave_results[:2]:
                    print(f"   - {item.get('title', 'N/A')[:50]}...")
            else:
                print("   ✗ No Brave Search results")
        else:
            print("\n5. Brave Search Test: ⚠️  API key not configured")


async def main():
    """Run all tests"""
    try:
        await test_essential_client()
        await test_parallel_search()
        await test_specific_apis()
        print("\n✅ All tests completed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)