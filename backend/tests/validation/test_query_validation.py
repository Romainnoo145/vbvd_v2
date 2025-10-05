"""
Test Query Validation and Preview System

Tests the QueryValidator with real Europeana queries to ensure:
- Preview accurately predicts availability
- Warnings are generated for problematic queries
- Suggestions are helpful
"""

import sys
import asyncio
import os
from dotenv import load_dotenv

sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

load_dotenv()

from backend.models import CuratorBrief
from backend.query import EuropeanaQueryBuilder, QueryValidator


async def main():
    print("=" * 80)
    print("QUERY VALIDATION & PREVIEW SYSTEM TEST")
    print("=" * 80)
    print()

    # Test curator brief
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

    # Exhibition sections (mix of good, narrow, and broad queries)
    exhibition_sections = [
        {
            "title": "Dromen in Pixels",
            "focus": "Digital art exploring dreamlike landscapes and surreal atmospheres through contemporary photography and video.",
            "estimated_artwork_count": 10
        },
        {
            "title": "De Absurditeit van het Algoritme",
            "focus": "Examining how artificial intelligence and algorithms create unexpected and surreal outcomes in generative art.",
            "estimated_artwork_count": 8
        },
        {
            "title": "Klassieke Surrealisten",
            "focus": "Traditional surrealist works from the 1920s-1960s period, exploring the foundations of the movement.",
            "estimated_artwork_count": 10
        }
    ]

    # Step 1: Build queries
    print("STEP 1: BUILDING QUERIES")
    print("-" * 80)
    query_builder = EuropeanaQueryBuilder(curator_brief)
    queries = query_builder.build_section_queries(exhibition_sections)

    print(f"✓ Generated {len(queries)} queries")
    print()

    # Step 2: Validate queries with preview
    print("STEP 2: VALIDATING QUERIES WITH PREVIEW")
    print("=" * 80)
    print()

    validator = QueryValidator()
    previews = await validator.validate_queries(queries)

    # Display results
    for preview in previews:
        print(f"Section: {preview.section_title}")
        print(f"  Query: {preview.query}")
        if preview.filters:
            print(f"  Filters: {', '.join(preview.filters)}")
        print()

        # Status indicator
        if preview.status == "good":
            indicator = "✅"
        elif preview.status == "warning":
            indicator = "⚠️ "
        else:
            indicator = "❌"

        print(f"  {indicator} Status: {preview.status.upper()}")
        print(f"  {preview.message}")

        if preview.institution_count:
            print(f"  Institutions: {preview.institution_count}")

        if preview.suggestions:
            print()
            print("  Suggestions:")
            for suggestion in preview.suggestions:
                print(f"    • {suggestion}")

        print()
        print("-" * 80)
        print()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    good_count = sum(1 for p in previews if p.status == "good")
    warning_count = sum(1 for p in previews if p.status == "warning")
    error_count = sum(1 for p in previews if p.status == "error")

    total_artworks = sum(p.total_count for p in previews if p.is_valid)

    print(f"Total Queries: {len(previews)}")
    print(f"✅ Good: {good_count}")
    print(f"⚠️  Warnings: {warning_count}")
    print(f"❌ Errors: {error_count}")
    print()
    print(f"Total Artworks Available: {total_artworks:,}")
    print()

    # Validation checks
    all_valid = all(p.is_valid for p in previews)
    has_enough_artworks = total_artworks >= 300

    if all_valid and has_enough_artworks:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
        print(f"   ✓ All queries valid")
        print(f"   ✓ {total_artworks:,} artworks available (>= 300 minimum)")
    else:
        if not all_valid:
            print("⚠️  Some queries have errors")
        if not has_enough_artworks:
            print(f"⚠️  Only {total_artworks:,} artworks available (< 300 minimum)")

    print()


if __name__ == "__main__":
    asyncio.run(main())
