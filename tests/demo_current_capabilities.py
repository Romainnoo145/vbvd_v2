#!/usr/bin/env python3
"""
Demonstration of Current Capabilities
Shows what the AI Curator Assistant can do with just the data client
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.clients import EssentialDataClient
from backend.config import data_config


class CurrentCapabilitiesDemo:
    """Demonstrates what we can do with the current implementation"""

    def __init__(self):
        self.client = None

    async def __aenter__(self):
        self.client = EssentialDataClient()
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def demo_1_art_movement_research(self):
        """
        CAPABILITY 1: Research Art Movements
        Aggregate information about art movements from multiple sources
        """
        print("\n" + "="*60)
        print("DEMO 1: Art Movement Research")
        print("="*60)
        print("\n📚 Researching 'Impressionism' across multiple sources...\n")

        sources = ['wikipedia', 'getty', 'wikidata']
        results = await self.client.search_essential(
            query="Impressionism",
            sources=sources,
            context="art movement 19th century"
        )

        # Aggregate findings
        findings = {
            'definitions': [],
            'key_concepts': [],
            'related_terms': [],
            'historical_context': []
        }

        # Process Wikipedia results
        if results.get('wikipedia'):
            for item in results['wikipedia'][:1]:
                findings['historical_context'].append({
                    'source': 'Wikipedia',
                    'summary': item.get('summary', '')[:200] + '...',
                    'url': item.get('url', '')
                })

        # Process Getty AAT results
        if results.get('getty'):
            for item in results['getty']:
                findings['key_concepts'].append({
                    'term': item.get('label', ''),
                    'getty_id': item.get('getty_id', ''),
                    'type': 'AAT Concept'
                })

        # Process Wikidata results
        if results.get('wikidata'):
            for item in results['wikidata']:
                findings['related_terms'].append({
                    'entity': item.get('title', ''),
                    'wikidata_id': item.get('wikidata_id', ''),
                    'description': item.get('description', '')
                })

        print("✅ Research Complete!")
        print(f"\nFindings:")
        print(f"  - Historical Context: {len(findings['historical_context'])} sources")
        print(f"  - Key Concepts (Getty): {len(findings['key_concepts'])} terms")
        print(f"  - Related Entities (Wikidata): {len(findings['related_terms'])} items")

        if findings['historical_context']:
            print(f"\n📖 Sample Context: {findings['historical_context'][0]['summary']}")

        return findings

    async def demo_2_artist_discovery(self):
        """
        CAPABILITY 2: Artist Information Aggregation
        Find and aggregate artist information from multiple sources
        """
        print("\n" + "="*60)
        print("DEMO 2: Artist Discovery & Information")
        print("="*60)
        print("\n🎨 Discovering information about 'Claude Monet'...\n")

        sources = ['wikipedia', 'wikidata', 'getty']
        results = await self.client.search_essential(
            query="Claude Monet",
            sources=sources,
            context="artist painter impressionist"
        )

        artist_profile = {
            'name': 'Claude Monet',
            'biographical_info': {},
            'authority_records': [],
            'descriptions': [],
            'related_works': []
        }

        # Process results
        for source, items in results.items():
            if items:
                if source == 'wikipedia':
                    artist_profile['biographical_info']['wikipedia'] = {
                        'summary': items[0].get('summary', '')[:300] + '...',
                        'url': items[0].get('url', '')
                    }
                elif source == 'wikidata':
                    for item in items:
                        if 'Monet' in item.get('title', ''):
                            artist_profile['authority_records'].append({
                                'source': 'Wikidata',
                                'id': item.get('wikidata_id', ''),
                                'label': item.get('title', '')
                            })
                elif source == 'getty':
                    for item in items:
                        if 'ULAN' in item.get('vocabulary', ''):
                            artist_profile['authority_records'].append({
                                'source': 'Getty ULAN',
                                'uri': item.get('uri', ''),
                                'label': item.get('label', '')
                            })

        print("✅ Artist Discovery Complete!")
        print(f"\nArtist Profile Summary:")
        print(f"  - Biographical Sources: {len(artist_profile['biographical_info'])} found")
        print(f"  - Authority Records: {len(artist_profile['authority_records'])} identifiers")

        if artist_profile['biographical_info'].get('wikipedia'):
            print(f"\n📝 Biography excerpt: {artist_profile['biographical_info']['wikipedia']['summary'][:150]}...")

        return artist_profile

    async def demo_3_artwork_search(self):
        """
        CAPABILITY 3: Artwork Discovery
        Search for specific artworks across collections
        """
        print("\n" + "="*60)
        print("DEMO 3: Artwork Discovery")
        print("="*60)
        print("\n🖼️ Searching for 'Water Lilies' artworks...\n")

        sources = ['wikidata', 'yale_lux']
        results = await self.client.search_essential(
            query="Water Lilies Monet",
            sources=sources,
            context="artwork painting impressionist"
        )

        artworks = []
        for source, items in results.items():
            for item in items:
                artwork = {
                    'title': item.get('title', item.get('label', 'Unknown')),
                    'source': source,
                    'id': item.get('wikidata_id', item.get('id', '')),
                    'type': item.get('type', 'artwork')
                }

                # Add additional metadata if available
                if 'artists' in item:
                    artwork['artists'] = item['artists']
                if 'location' in item:
                    artwork['location'] = item['location']

                artworks.append(artwork)

        print("✅ Artwork Search Complete!")
        print(f"\nFound {len(artworks)} related artworks")

        for i, artwork in enumerate(artworks[:3], 1):
            print(f"\n  {i}. {artwork['title']}")
            print(f"     Source: {artwork['source']}")
            if 'location' in artwork:
                print(f"     Location: {artwork['location']}")

        return artworks

    async def demo_4_vocabulary_validation(self):
        """
        CAPABILITY 4: Professional Vocabulary Validation
        Validate and enrich curatorial terms with Getty vocabularies
        """
        print("\n" + "="*60)
        print("DEMO 4: Professional Vocabulary Validation")
        print("="*60)
        print("\n📖 Validating curatorial terms with Getty AAT...\n")

        # Terms a curator might use
        curatorial_terms = [
            "chiaroscuro",
            "triptych",
            "sfumato",
            "impasto"
        ]

        validated_terms = []

        for term in curatorial_terms:
            print(f"  Validating '{term}'...")
            results = await self.client._search_getty(term, "technique concept")

            if results:
                validated = {
                    'original_term': term,
                    'getty_label': results[0].get('label', ''),
                    'getty_uri': results[0].get('uri', ''),
                    'getty_id': results[0].get('getty_id', ''),
                    'vocabulary': results[0].get('vocabulary', 'AAT'),
                    'valid': True
                }
            else:
                validated = {
                    'original_term': term,
                    'valid': False,
                    'note': 'Term not found in Getty vocabularies'
                }

            validated_terms.append(validated)

        print("\n✅ Vocabulary Validation Complete!")
        print(f"\nValidation Results:")
        valid_count = sum(1 for t in validated_terms if t['valid'])
        print(f"  - Valid Terms: {valid_count}/{len(curatorial_terms)}")

        for term in validated_terms:
            if term['valid']:
                print(f"  ✓ {term['original_term']} → Getty AAT ID: {term.get('getty_id', 'N/A')}")
            else:
                print(f"  ✗ {term['original_term']} → Not found")

        return validated_terms

    async def demo_5_parallel_comprehensive_search(self):
        """
        CAPABILITY 5: Parallel Comprehensive Search
        Show the power of parallel searching across all sources
        """
        print("\n" + "="*60)
        print("DEMO 5: Parallel Comprehensive Search")
        print("="*60)
        print("\n⚡ Demonstrating parallel search across all free sources...\n")

        query = "Rembrandt self-portrait"
        sources = ['wikipedia', 'wikidata', 'getty', 'yale_lux']

        print(f"Query: '{query}'")
        print(f"Searching {len(sources)} sources simultaneously...")

        start_time = asyncio.get_event_loop().time()

        results = await self.client.search_essential(
            query=query,
            sources=sources,
            context="artwork painting Dutch Golden Age"
        )

        elapsed = asyncio.get_event_loop().time() - start_time

        print(f"\n✅ Parallel search completed in {elapsed:.2f} seconds!")

        total_results = sum(len(items) for items in results.values())
        print(f"\nResults Summary:")
        print(f"  Total results: {total_results} items from {len(sources)} sources")

        for source, items in results.items():
            print(f"  - {source:15}: {len(items):3} results")

        return results

    async def demo_6_cross_reference_entities(self):
        """
        CAPABILITY 6: Cross-Reference Entities
        Show how we can cross-reference entities across different databases
        """
        print("\n" + "="*60)
        print("DEMO 6: Entity Cross-Referencing")
        print("="*60)
        print("\n🔗 Cross-referencing 'Van Gogh' across databases...\n")

        entity = "Vincent van Gogh"

        # Search across all authority databases
        sources = ['wikidata', 'getty', 'yale_lux']
        results = await self.client.search_essential(
            query=entity,
            sources=sources,
            context="artist painter post-impressionist"
        )

        # Build cross-reference map
        cross_references = {
            'entity': entity,
            'identifiers': [],
            'found_in': []
        }

        for source, items in results.items():
            if items:
                cross_references['found_in'].append(source)

                if source == 'wikidata':
                    for item in items:
                        if 'Gogh' in item.get('title', ''):
                            cross_references['identifiers'].append({
                                'system': 'Wikidata',
                                'id': item.get('wikidata_id', ''),
                                'uri': f"https://www.wikidata.org/wiki/{item.get('wikidata_id', '')}"
                            })
                            break

                elif source == 'getty':
                    for item in items:
                        if 'ULAN' in item.get('vocabulary', ''):
                            cross_references['identifiers'].append({
                                'system': 'Getty ULAN',
                                'id': item.get('getty_id', ''),
                                'uri': item.get('uri', '')
                            })
                            break

        print("✅ Cross-Reference Complete!")
        print(f"\nEntity: {entity}")
        print(f"Found in {len(cross_references['found_in'])} databases:")

        for identifier in cross_references['identifiers']:
            print(f"  - {identifier['system']}: {identifier['id']}")

        return cross_references


async def run_all_demos():
    """Run all capability demonstrations"""
    print("\n" + "="*70)
    print(" AI CURATOR ASSISTANT - CURRENT CAPABILITIES DEMONSTRATION")
    print("="*70)
    print("\nThis demo shows what's possible with just the data client layer.")
    print("No AI agents yet - just intelligent data aggregation!\n")

    async with CurrentCapabilitiesDemo() as demo:

        # Run all demos
        results = {}

        # 1. Art Movement Research
        results['movement'] = await demo.demo_1_art_movement_research()
        await asyncio.sleep(1)  # Be nice to APIs

        # 2. Artist Discovery
        results['artist'] = await demo.demo_2_artist_discovery()
        await asyncio.sleep(1)

        # 3. Artwork Search
        results['artworks'] = await demo.demo_3_artwork_search()
        await asyncio.sleep(1)

        # 4. Vocabulary Validation
        results['vocabulary'] = await demo.demo_4_vocabulary_validation()
        await asyncio.sleep(1)

        # 5. Parallel Search
        results['parallel'] = await demo.demo_5_parallel_comprehensive_search()
        await asyncio.sleep(1)

        # 6. Cross-References
        results['cross_ref'] = await demo.demo_6_cross_reference_entities()

    # Save results
    output_file = Path("demo_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "="*70)
    print(" DEMONSTRATION COMPLETE")
    print("="*70)
    print(f"\n💾 Full results saved to: {output_file}")
    print("\n🚀 What's Next?")
    print("   With the addition of AI agents, this system will be able to:")
    print("   1. Transform rough curator ideas into professional themes")
    print("   2. Discover relevant artists based on themes")
    print("   3. Find specific artworks for exhibitions")
    print("   4. Generate complete exhibition proposals")
    print("   5. Provide curatorial narratives and visitor journeys")

    return results


async def quick_capability_test():
    """Quick test to show immediate capabilities"""
    print("\n" + "="*60)
    print("QUICK CAPABILITY TEST")
    print("="*60)

    async with EssentialDataClient() as client:
        # Quick multi-source search
        print("\n🔍 Quick Search: 'Impressionism' across 3 sources...")

        results = await client.search_essential(
            query="Impressionism",
            sources=['wikipedia', 'getty', 'wikidata'],
            context="art movement"
        )

        print("\n✅ Results Summary:")
        for source, items in results.items():
            if items:
                print(f"\n{source.upper()}:")
                for item in items[:2]:  # Show first 2 items
                    title = item.get('title', item.get('label', 'Unknown'))
                    print(f"  - {title[:60]}...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='AI Curator Assistant Capability Demo')
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    parser.add_argument('--full', action='store_true', help='Run full demonstration')

    args = parser.parse_args()

    if args.quick:
        asyncio.run(quick_capability_test())
    else:
        # Default to full demo
        asyncio.run(run_all_demos())