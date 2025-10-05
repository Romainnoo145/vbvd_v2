"""
Test EuropeanaQueryExecutor with live API
Validates parallel execution, deduplication, and result aggregation
"""

import sys
import asyncio
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.query import EuropeanaQueryBuilder, EuropeanaQueryExecutor
from backend.models import CuratorBrief

# Test data from demo
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
    print("TESTING EUROPEANA QUERY EXECUTOR")
    print("=" * 80)
    print()

    # Step 1: Build queries
    print("Step 1: Building queries...")
    print("-" * 80)
    query_builder = EuropeanaQueryBuilder(curator_brief)
    queries = query_builder.build_section_queries(exhibition_sections)

    print(f"✓ Generated {len(queries)} queries:")
    for query in queries:
        print(f"  - {query.section_title}: {query.query[:60]}...")
    print()

    # Step 2: Execute queries
    print("Step 2: Executing queries in parallel...")
    print("-" * 80)
    executor = EuropeanaQueryExecutor()

    # Fetch 50 artworks per section for testing (faster)
    results = await executor.execute_queries(queries, rows_per_section=50)
    print()

    # Step 3: Analyze results
    print("=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    print()

    print(f"Total Artworks Fetched: {results.total_artworks}")
    print(f"Unique Artworks (deduplicated): {results.unique_artworks}")
    print(f"Deduplication Rate: {((results.total_artworks - results.unique_artworks) / results.total_artworks * 100) if results.total_artworks > 0 else 0:.1f}%")
    print(f"Success Rate: {results.success_rate}%")
    print()

    print("Artworks by Section:")
    for section, count in results.artworks_by_section.items():
        print(f"  {section}: {count} artworks")
    print()

    if results.failed_sections:
        print(f"⚠️  Failed Sections: {', '.join(results.failed_sections)}")
        print()

    # Step 4: Sample artworks validation
    print("=" * 80)
    print("SAMPLE ARTWORKS (First 5)")
    print("=" * 80)
    print()

    for i, artwork in enumerate(results.artworks[:5], 1):
        print(f"Artwork {i}:")

        # Title
        title = artwork.get('title', ['Untitled'])
        if isinstance(title, list):
            title = title[0] if title else 'Untitled'
        print(f"  Title: {title}")

        # Artist
        creator = artwork.get('dcCreator', ['Unknown'])
        if isinstance(creator, list):
            creator = creator[0] if creator else 'Unknown'
        print(f"  Artist: {creator}")

        # Year
        year = artwork.get('year', ['Unknown'])
        if isinstance(year, list):
            year = year[0] if year else 'Unknown'
        print(f"  Year: {year}")

        # Type
        artwork_type = artwork.get('type', 'Unknown')
        print(f"  Type: {artwork_type}")

        # Section tagging
        section_id = artwork.get('_section_id', 'NO TAG')
        section_title = artwork.get('_section_title', 'NO TAG')
        print(f"  Section: {section_title} ({section_id})")

        # Europeana ID
        europeana_id = artwork.get('id', 'NO ID')
        print(f"  ID: {europeana_id}")

        print()

    # Step 5: Validation checks
    print("=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)
    print()

    validation_passed = True

    # Check 1: Minimum artworks fetched
    if results.unique_artworks < 100:
        print(f"⚠️  Low artwork count: {results.unique_artworks} (expected >100)")
        validation_passed = False
    else:
        print(f"✓ Good artwork count: {results.unique_artworks}")

    # Check 2: All sections succeeded
    if len(results.failed_sections) > 0:
        print(f"⚠️  {len(results.failed_sections)} sections failed")
        validation_passed = False
    else:
        print("✓ All sections succeeded")

    # Check 3: Deduplication occurred
    if results.total_artworks == results.unique_artworks:
        print("⚠️  No duplicates found (unexpected)")
    else:
        duplicates = results.total_artworks - results.unique_artworks
        print(f"✓ Deduplication working: {duplicates} duplicates removed")

    # Check 4: Section tagging present
    tagged_count = sum(1 for a in results.artworks if '_section_id' in a)
    if tagged_count == len(results.artworks):
        print(f"✓ All artworks tagged with section_id")
    else:
        print(f"⚠️  Only {tagged_count}/{len(results.artworks)} artworks tagged")
        validation_passed = False

    # Check 5: All artworks have IDs
    with_ids = sum(1 for a in results.artworks if 'id' in a and a['id'])
    if with_ids == len(results.artworks):
        print(f"✓ All artworks have Europeana IDs")
    else:
        print(f"⚠️  Only {with_ids}/{len(results.artworks)} artworks have IDs")
        validation_passed = False

    print()
    if validation_passed:
        print("=" * 80)
        print("✅ ALL VALIDATION CHECKS PASSED!")
        print("=" * 80)
    else:
        print("=" * 80)
        print("⚠️  SOME VALIDATION CHECKS FAILED")
        print("=" * 80)

    print()
    print(f"Summary: Fetched {results.unique_artworks} unique artworks from {len(queries)} sections")
    print("Ready for artist extraction!")
    print()

if __name__ == "__main__":
    asyncio.run(main())
