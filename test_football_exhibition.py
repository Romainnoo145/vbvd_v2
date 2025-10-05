"""
End-to-End Test: Football Exhibition
Real curator workflow from form input → artist extraction
"""

import sys
import asyncio
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.query import EuropeanaQueryBuilder, EuropeanaQueryExecutor
from backend.extraction import ArtistExtractor
from backend.models import CuratorBrief
from collections import Counter

# Simulated form input: Football exhibition for Netherlands
curator_brief = CuratorBrief(
    theme_title="Voetbal & Kunst: Een Culturele Reis",
    theme_description="Een tentoonstelling die de relatie tussen voetbal en beeldende kunst onderzoekt, van historische affiches tot hedendaagse fotografie en installaties.",
    art_movements=["modern", "contemporary"],
    media_types=["photography", "prints", "posters"],
    time_period="contemporary",
    geographic_focus=["Netherlands", "Belgium", "Germany", "France"],
    target_audience="general",
    duration_weeks=12
)

# Exhibition sections (would come from theme refinement)
exhibition_sections = [
    {
        "title": "De Gouden Jaren: Voetbaliconen",
        "focus": "Historical football photography capturing legendary players and iconic moments in Dutch football history.",
        "estimated_artwork_count": 10
    },
    {
        "title": "Stadion als Canvas",
        "focus": "Exploring the architecture and design of football stadiums as cultural landmarks and artistic spaces.",
        "estimated_artwork_count": 8
    },
    {
        "title": "Fans & Gemeenschap",
        "focus": "Examining football fan culture, community identity, and social movements through visual art and photography.",
        "estimated_artwork_count": 10
    }
]

async def main():
    print("=" * 80)
    print("FOOTBALL EXHIBITION: END-TO-END TEST")
    print("=" * 80)
    print()
    print("FORM INPUT:")
    print("-" * 80)
    print(f"Theme: {curator_brief.theme_title}")
    print(f"Description: {curator_brief.theme_description}")
    print(f"Art Movements: {', '.join(curator_brief.art_movements)}")
    print(f"Media Types: {', '.join(curator_brief.media_types)}")
    print(f"Time Period: {curator_brief.time_period}")
    print(f"Geographic Focus: {', '.join(curator_brief.geographic_focus)}")
    print(f"Duration: {curator_brief.duration_weeks} weeks")
    print()

    # Step 1: Build queries
    print("=" * 80)
    print("STEP 1: QUERY GENERATION")
    print("=" * 80)
    query_builder = EuropeanaQueryBuilder(curator_brief)
    queries = query_builder.build_section_queries(exhibition_sections)

    print(f"\n✓ Generated {len(queries)} queries")
    print(f"  ({len(exhibition_sections)} sections × {len(curator_brief.geographic_focus)} countries)")
    print()

    print("Sample Queries:")
    for i, query in enumerate(queries[:4], 1):
        print(f"{i}. Section: {query.section_title}")
        print(f"   Query: {query.query}")
        print(f"   Filter: {query.qf}")
        print()

    # Step 2: Execute queries
    print("=" * 80)
    print("STEP 2: QUERY EXECUTION")
    print("=" * 80)
    executor = EuropeanaQueryExecutor()
    results = await executor.execute_queries(queries)

    print(f"\n✓ Fetched {results.unique_artworks} unique artworks")
    print(f"  Total fetched: {results.total_artworks}")
    print(f"  Deduplication: {((results.total_artworks - results.unique_artworks) / results.total_artworks * 100) if results.total_artworks > 0 else 0:.1f}%")
    print()

    # Geographic distribution
    print("Geographic Distribution:")
    countries = Counter()
    for artwork in results.artworks:
        country = artwork.get('country', [])
        if isinstance(country, list):
            countries.update(country)
        elif country:
            countries[country] += 1

    for country, count in countries.most_common():
        percentage = (count / len(results.artworks) * 100) if results.artworks else 0
        print(f"  {country:15} {count:4} artworks ({percentage:5.1f}%)")

    print()

    # Step 3: Extract artists
    print("=" * 80)
    print("STEP 3: ARTIST EXTRACTION")
    print("=" * 80)
    extractor = ArtistExtractor(min_works=2)  # At least 2 works
    extraction_results = extractor.extract_artists(results.artworks)

    print(f"\n✓ Extracted {extraction_results.artists_found} artists (min 2 works)")
    print(f"  Artworks processed: {extraction_results.total_artworks_processed}")
    print(f"  Filtered: {extraction_results.unknown_count} unknown, {extraction_results.uri_count} URIs")
    print()

    # Top artists
    print("=" * 80)
    print("TOP 20 ARTISTS FOR FOOTBALL EXHIBITION")
    print("=" * 80)
    print()

    for i, artist in enumerate(extraction_results.artists[:20], 1):
        print(f"{i}. {artist.name}")
        print(f"   Works: {artist.works_count}")
        print(f"   Countries: {', '.join(artist.countries.keys())}")
        if artist.year_range:
            print(f"   Years: {artist.year_range[0]}-{artist.year_range[1]}")
        print(f"   Sections: {', '.join(artist.sections)}")
        print()

    # Sample artworks from top artist
    if extraction_results.artists:
        print("=" * 80)
        print("SAMPLE ARTWORKS: Top Artist")
        print("=" * 80)
        print()

        top_artist = extraction_results.artists[0]
        print(f"Artist: {top_artist.name}")
        print(f"Total Works: {top_artist.works_count}")
        print()

        print("Sample Artworks:")
        for artwork in top_artist.artworks[:5]:
            title = artwork.get('title', ['Untitled'])
            if isinstance(title, list):
                title = title[0] if title else 'Untitled'

            year = artwork.get('year', ['Unknown'])
            if isinstance(year, list):
                year = year[0] if year else 'Unknown'

            print(f"  • {title}")
            print(f"    Year: {year}")

    # Validation
    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    print()

    checks = []

    # Check 1: Minimum artworks
    if results.unique_artworks >= 300:
        print(f"✅ Artwork count: {results.unique_artworks} (>= 300)")
        checks.append(True)
    else:
        print(f"⚠️  Artwork count: {results.unique_artworks} (< 300)")
        checks.append(False)

    # Check 2: Geographic balance
    if countries:
        max_percentage = (countries.most_common(1)[0][1] / len(results.artworks) * 100)
        if max_percentage < 50:
            print(f"✅ Geographic balance: Max {max_percentage:.1f}% (< 50%)")
            checks.append(True)
        else:
            print(f"⚠️  Geographic bias: {max_percentage:.1f}% from one country")
            checks.append(False)

    # Check 3: Netherlands representation
    netherlands_count = countries.get('Netherlands', 0)
    netherlands_pct = (netherlands_count / len(results.artworks) * 100) if results.artworks else 0
    if netherlands_count > 0:
        print(f"✅ Netherlands represented: {netherlands_count} artworks ({netherlands_pct:.1f}%)")
        checks.append(True)
    else:
        print(f"⚠️  No Netherlands artworks found")
        checks.append(False)

    # Check 4: Artist extraction
    if extraction_results.artists_found >= 50:
        print(f"✅ Artists found: {extraction_results.artists_found} (>= 50)")
        checks.append(True)
    else:
        print(f"⚠️  Artists found: {extraction_results.artists_found} (< 50)")
        checks.append(False)

    print()
    if all(checks):
        print("🎉 ALL VALIDATION CHECKS PASSED!")
    else:
        print(f"⚠️  {sum(checks)}/{len(checks)} checks passed")

    print()
    print("=" * 80)
    print(f"READY FOR SCORING: {extraction_results.artists_found} artists")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
