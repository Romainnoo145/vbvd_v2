"""
Test Artist Extraction with real Europeana data
End-to-end test: Query → Execute → Extract Artists
"""

import sys
import asyncio
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.query import EuropeanaQueryBuilder, EuropeanaQueryExecutor
from backend.extraction import ArtistExtractor
from backend.models import CuratorBrief

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
    print("END-TO-END TEST: Query → Execute → Extract Artists")
    print("=" * 80)
    print()

    # Step 1: Build queries
    print("Step 1: Building queries...")
    print("-" * 80)
    query_builder = EuropeanaQueryBuilder(curator_brief)
    queries = query_builder.build_section_queries(exhibition_sections)
    print(f"✓ Generated {len(queries)} queries")
    print()

    # Step 2: Execute queries
    print("Step 2: Executing queries...")
    print("-" * 80)
    executor = EuropeanaQueryExecutor()
    results = await executor.execute_queries(queries)  # Using default 200 rows per section
    print(f"✓ Fetched {results.unique_artworks} unique artworks")
    print()

    # Step 3: Extract artists
    print("Step 3: Extracting artists...")
    print("-" * 80)
    extractor = ArtistExtractor(min_works=1)  # Include all artists with ≥1 work
    extraction_results = extractor.extract_artists(results.artworks)
    print()

    # Step 4: Analyze results
    print("=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)
    print()

    print(f"Artworks Processed: {extraction_results.total_artworks_processed}")
    print(f"Artists Found: {extraction_results.artists_found}")
    print(f"Artists Filtered: {extraction_results.artists_filtered}")
    print()

    print("Filtering Statistics:")
    print(f"  Unknown/Missing: {extraction_results.unknown_count}")
    print(f"  URI-only: {extraction_results.uri_count}")
    print(f"  Various/Multiple: {extraction_results.various_count}")
    print()

    # Step 5: Top artists
    print("=" * 80)
    print("TOP 10 ARTISTS (by works count)")
    print("=" * 80)
    print()

    for i, artist in enumerate(extraction_results.artists[:10], 1):
        print(f"{i}. {artist.name}")
        print(f"   Works: {artist.works_count}")
        print(f"   Institutions: {len(artist.institutions)}")
        print(f"   Countries: {list(artist.countries.keys())}")
        if artist.year_range:
            print(f"   Year Range: {artist.year_range[0]}-{artist.year_range[1]}")
        print(f"   Sections: {', '.join(artist.sections[:3])}")
        print()

    # Step 6: Sample artist details
    if extraction_results.artists:
        print("=" * 80)
        print("DETAILED VIEW: Top Artist")
        print("=" * 80)
        print()

        top_artist = extraction_results.artists[0]
        print(f"Name: {top_artist.name}")
        print(f"Original Name Variants: {top_artist.original_names}")
        print(f"Total Works: {top_artist.works_count}")
        print()

        print("Institutions:")
        for inst in top_artist.institutions[:5]:
            print(f"  - {inst}")
        print()

        print("Countries (with counts):")
        for country, count in top_artist.countries.items():
            print(f"  - {country}: {count} works")
        print()

        print("Media Types (with counts):")
        for media, count in top_artist.media_types.items():
            print(f"  - {media}: {count} works")
        print()

        print("Years:")
        if top_artist.years:
            print(f"  {', '.join(str(y) for y in sorted(top_artist.years)[:10])}")
            if len(top_artist.years) > 10:
                print(f"  ... and {len(top_artist.years) - 10} more")
        print()

        print("Sample Artworks:")
        for artwork in top_artist.artworks[:3]:
            title = artwork.get('title', ['Untitled'])
            if isinstance(title, list):
                title = title[0] if title else 'Untitled'
            print(f"  - {title}")
        print()

    # Step 7: Validation
    print("=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)
    print()

    validation_passed = True

    # Check 1: Artists extracted
    if extraction_results.artists_found == 0:
        print("❌ No artists extracted!")
        validation_passed = False
    else:
        print(f"✓ Extracted {extraction_results.artists_found} artists")

    # Check 2: Reasonable extraction rate
    extraction_rate = (extraction_results.artists_found / extraction_results.total_artworks_processed) * 100
    if extraction_rate < 5:  # At least 5% of artworks should have valid artists
        print(f"⚠️  Low extraction rate: {extraction_rate:.1f}%")
    else:
        print(f"✓ Good extraction rate: {extraction_rate:.1f}%")

    # Check 3: All artists have artworks
    artists_without_works = [a for a in extraction_results.artists if not a.artworks]
    if artists_without_works:
        print(f"❌ {len(artists_without_works)} artists have no artworks!")
        validation_passed = False
    else:
        print("✓ All artists have associated artworks")

    # Check 4: All artists have metadata
    artists_without_metadata = [a for a in extraction_results.artists if not a.institutions and not a.countries]
    if artists_without_metadata:
        print(f"⚠️  {len(artists_without_metadata)} artists missing metadata")
    else:
        print("✓ All artists have aggregated metadata")

    # Check 5: Top artists have multiple works
    if extraction_results.artists:
        top_artist = extraction_results.artists[0]
        if top_artist.works_count == 1:
            print("⚠️  Top artist has only 1 work")
        else:
            print(f"✓ Top artist has {top_artist.works_count} works")

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
    print(f"Summary: {extraction_results.artists_found} artists ready for scoring!")
    print()

if __name__ == "__main__":
    asyncio.run(main())
