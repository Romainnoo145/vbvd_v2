"""
Test quality scoring integration with artist extraction

Uses real Europeana data from query executor test
"""

import sys
import os
import asyncio

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, backend_path)

# Also add project root to path for backend imports
project_root = os.path.abspath(os.path.join(backend_path, '..'))
sys.path.insert(0, project_root)

from backend.extraction.artist_extractor import ArtistExtractor
from backend.query.europeana_query_executor import EuropeanaQueryExecutor
from backend.query.europeana_query_builder import EuropeanaQuery


async def test_quality_scoring_integration():
    """Test that quality scoring works with real artist extraction"""

    print("\n" + "="*80)
    print("QUALITY SCORING INTEGRATION TEST")
    print("="*80 + "\n")

    # Create sample query (surrealism theme)
    query = EuropeanaQuery(
        section_id="test-section",
        section_title="Digital Surrealism Test",
        query="(Surrealism OR \"Contemporary Art\") AND TYPE:IMAGE",
        qf=["TYPE:IMAGE"],
        rows=50  # Small sample for testing
    )

    # Execute query to get real artworks
    print("1. Fetching artworks from Europeana...")
    executor = EuropeanaQueryExecutor()
    results = await executor.execute_queries([query])

    print(f"   ✓ Fetched {results.total_artworks} artworks")
    print(f"   ✓ Unique: {results.unique_artworks}\n")

    if results.unique_artworks == 0:
        print("   ✗ No artworks found - skipping test")
        return

    # Extract artists with quality scoring
    print("2. Extracting artists with quality scoring...")

    # Define theme period for scoring (contemporary surrealism: 1970-2025)
    theme_period = (1970, 2025)

    extractor = ArtistExtractor(min_works=1, theme_period=theme_period)
    extraction_results = extractor.extract_artists(results.artworks)

    print(f"   ✓ Extracted {extraction_results.artists_found} artists")
    print(f"   ✓ Theme period: {theme_period[0]}-{theme_period[1]}\n")

    if not extraction_results.artists:
        print("   ✗ No artists extracted - skipping test")
        return

    # Display top 5 artists with quality scores
    print("3. Top Artists by Quality Score:")
    print("-" * 80)

    for i, artist in enumerate(extraction_results.artists[:5], 1):
        print(f"\n{i}. {artist.name}")
        print(f"   Quality Score: {artist.quality_score:.1f}/100")

        if artist.quality_breakdown:
            breakdown = artist.quality_breakdown
            print(f"   - Availability: {breakdown['availability']:.1f}/40 ({artist.works_count} works)")
            print(f"   - IIIF: {breakdown['iiif']:.1f}/30 ({artist.iiif_percentage:.0f}%)")
            print(f"   - Institutions: {breakdown['institution_diversity']:.1f}/20 ({len(artist.institutions)} inst)")
            print(f"   - Period Match: {breakdown['time_period_match']:.1f}/10")

        # Display derived fields
        if artist.nationality:
            print(f"   Nationality: {artist.nationality}")

        if artist.estimated_birth_year:
            birth_death = f"{artist.estimated_birth_year}"
            if artist.estimated_death_year:
                birth_death += f"-{artist.estimated_death_year}"
            else:
                birth_death += "-present"
            print(f"   Estimated years: {birth_death}")

        if artist.movement:
            print(f"   Movement: {artist.movement}")

        if artist.relevance_reasoning:
            print(f"   Relevance: {artist.relevance_reasoning}")

    # Quality score statistics
    print("\n" + "="*80)
    print("QUALITY SCORE STATISTICS")
    print("="*80 + "\n")

    scores = [a.quality_score for a in extraction_results.artists if a.quality_score]

    if scores:
        print(f"  Highest score: {max(scores):.1f}/100")
        print(f"  Lowest score: {min(scores):.1f}/100")
        print(f"  Average score: {sum(scores)/len(scores):.1f}/100")
        print(f"  Score range: {max(scores) - min(scores):.1f} points")

        # Count by tier
        excellent = sum(1 for s in scores if s >= 70)
        good = sum(1 for s in scores if 50 <= s < 70)
        moderate = sum(1 for s in scores if 30 <= s < 50)
        low = sum(1 for s in scores if s < 30)

        print(f"\n  Score distribution:")
        print(f"    Excellent (70+): {excellent} artists")
        print(f"    Good (50-70): {good} artists")
        print(f"    Moderate (30-50): {moderate} artists")
        print(f"    Low (<30): {low} artists")

    # IIIF statistics
    print("\n" + "="*80)
    print("IIIF AVAILABILITY STATISTICS")
    print("="*80 + "\n")

    iiif_percentages = [a.iiif_percentage for a in extraction_results.artists]
    if iiif_percentages:
        print(f"  Highest IIIF: {max(iiif_percentages):.1f}%")
        print(f"  Lowest IIIF: {min(iiif_percentages):.1f}%")
        print(f"  Average IIIF: {sum(iiif_percentages)/len(iiif_percentages):.1f}%")

        high_iiif = sum(1 for p in iiif_percentages if p >= 80)
        print(f"\n  Artists with high IIIF (80%+): {high_iiif}/{len(extraction_results.artists)}")

    print("\n" + "="*80)
    print("✅ QUALITY SCORING TEST COMPLETE")
    print("="*80 + "\n")

    # Test filtering logic
    print("\n" + "="*80)
    print("FILTERING LOGIC TEST (Task 23)")
    print("="*80 + "\n")

    # Test with top 10 limit
    print("Testing with max_artists=10...")
    extractor_limited = ArtistExtractor(min_works=2, theme_period=theme_period, max_artists=10)
    results_limited = extractor_limited.extract_artists(results.artworks)

    print(f"  Total artists found: {results_limited.artists_found}")
    print(f"  Filtered by min works (<2): {results_limited.filtered_by_min_works}")
    print(f"  Filtered by Unknown works (>80%): {results_limited.filtered_by_unknown_works}")
    print(f"  Filtered by top limit (>10): {results_limited.filtered_by_top_limit}")
    print(f"  Total filtered: {results_limited.artists_filtered}")

    if results_limited.artists_found == 10:
        print(f"\n  ✅ Top {extractor_limited.max_artists} limit working correctly!")

    # Show filtering statistics
    print(f"\n  Filtering breakdown:")
    print(f"    - Started with: {len(results.artworks)} artworks")
    print(f"    - Unique artist names: (tracked internally)")
    print(f"    - After min works filter: {results_limited.artists_found + results_limited.filtered_by_top_limit}")
    print(f"    - After Unknown filter: {results_limited.artists_found + results_limited.filtered_by_top_limit}")
    print(f"    - After top {extractor_limited.max_artists} limit: {results_limited.artists_found}")

    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_quality_scoring_integration())
