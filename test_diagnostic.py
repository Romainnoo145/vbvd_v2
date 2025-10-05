"""
Diagnostic Test - Investigate Poland bias and low artwork counts
"""

import sys
import asyncio
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.query import EuropeanaQueryBuilder, EuropeanaQueryExecutor
from backend.models import CuratorBrief

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
    },
    {
        "title": "De Absurditeit van het Algoritme",
        "focus": "Investigating how algorithms can produce surreal and unexpected outcomes.",
        "estimated_artwork_count": 10
    },
    {
        "title": "Het Onbewuste en de Virtuele Ruimte",
        "focus": "Examining the intersection of the unconscious mind and virtual realities.",
        "estimated_artwork_count": 8
    }
]

async def main():
    print("=" * 80)
    print("DIAGNOSTIC: Query Generation and Execution")
    print("=" * 80)
    print()

    # Step 1: Inspect generated queries
    print("STEP 1: Query Generation")
    print("-" * 80)
    query_builder = EuropeanaQueryBuilder(curator_brief)
    queries = query_builder.build_section_queries(exhibition_sections)

    for query in queries:
        print(f"\nSection: {query.section_title}")
        print(f"  Query: {query.query}")
        print(f"  QF Filters: {query.qf if query.qf else 'None'}")
        print(f"  Section ID: {query.section_id}")

    print()
    print("=" * 80)

    # Step 2: Execute ONE query and inspect results
    print("\nSTEP 2: Execute First Query (Section 1 only)")
    print("-" * 80)
    executor = EuropeanaQueryExecutor()

    # Execute just the first query to inspect
    result = await executor._execute_single_query(queries[0], rows=200)

    if result:
        items = result['items']
        print(f"\nTotal Available: {result['total_available']:,}")
        print(f"Fetched: {len(items)} items")
        print()

        # Analyze country distribution
        print("Country Distribution:")
        from collections import Counter
        countries = Counter()
        for item in items:
            country = item.get('country', [])
            if isinstance(country, list):
                countries.update(country)
            elif country:
                countries[country] += 1

        for country, count in countries.most_common(10):
            print(f"  {country}: {count} ({count/len(items)*100:.1f}%)")

        print()

        # Sample artworks
        print("Sample Artworks (first 5):")
        for i, item in enumerate(items[:5], 1):
            title = item.get('title', ['Untitled'])
            if isinstance(title, list):
                title = title[0] if title else 'Untitled'

            creator = item.get('dcCreator', ['Unknown'])
            if isinstance(creator, list):
                creator = creator[0] if creator else 'Unknown'

            country = item.get('country', ['Unknown'])
            if isinstance(country, list):
                country = country[0] if country else 'Unknown'

            print(f"  {i}. {title}")
            print(f"     Creator: {creator}")
            print(f"     Country: {country}")
            print()

    # Step 3: Execute all queries and check deduplication
    print("=" * 80)
    print("\nSTEP 3: Execute All Queries")
    print("-" * 80)
    results = await executor.execute_queries(queries, rows_per_section=200)

    print(f"\nTotal Fetched (before dedup): {results.total_artworks}")
    print(f"Unique (after dedup): {results.unique_artworks}")
    print(f"Deduplication Rate: {(results.total_artworks - results.unique_artworks) / results.total_artworks * 100:.1f}%")
    print()

    print("Artworks by Section:")
    for section, count in results.artworks_by_section.items():
        print(f"  {section}: {count}")
    print()

    # Check country distribution in final results
    print("Final Country Distribution (all sections):")
    countries_final = Counter()
    for item in results.artworks:
        country = item.get('country', [])
        if isinstance(country, list):
            countries_final.update(country)
        elif country:
            countries_final[country] += 1

    for country, count in countries_final.most_common(10):
        print(f"  {country}: {count} ({count/len(results.artworks)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())
