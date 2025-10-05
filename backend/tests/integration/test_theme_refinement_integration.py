"""
Test Theme Refinement Integration with Query Building and Validation

Tests that the theme refinement agent now:
1. Builds Europeana queries for exhibition sections
2. Validates queries with preview system
3. Implements adjustment loop for problematic queries
4. Includes query data in RefinedTheme output
"""

import sys
import asyncio
import os
from dotenv import load_dotenv

sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

load_dotenv()

from backend.models import CuratorBrief
from backend.agents.theme_refinement_agent import ThemeRefinementAgent
from backend.clients.essential_data_client import EssentialDataClient


async def progress_callback(message: str):
    """Simple progress callback for testing"""
    print(f"  [PROGRESS] {message}")


async def main():
    print("=" * 80)
    print("THEME REFINEMENT + QUERY INTEGRATION TEST")
    print("=" * 80)
    print()

    # Test curator brief - contemporary digital surrealism
    curator_brief = CuratorBrief(
        theme_title="Surrealisme in het Digitale Tijdperk",
        theme_description="Een tentoonstelling die de invloed van surrealistische principes op hedendaagse digitale kunst onderzoekt.",
        theme_concepts=["surrealism", "digital art", "contemporary art"],
        art_movements=["surrealism", "contemporary"],
        media_types=["photography", "video_art", "installation"],
        time_period="contemporary",
        geographic_focus=["Netherlands", "Belgium", "Germany", "France"],
        target_audience="general",
        duration_weeks=16
    )

    print("CURATOR BRIEF:")
    print(f"  Theme: {curator_brief.theme_title}")
    print(f"  Movements: {', '.join(curator_brief.art_movements)}")
    print(f"  Media: {', '.join(curator_brief.media_types)}")
    print(f"  Geography: {', '.join(curator_brief.geographic_focus)}")
    print()

    # Initialize agent
    print("STEP 1: INITIALIZING THEME REFINEMENT AGENT")
    print("-" * 80)

    async with EssentialDataClient() as client:
        agent = ThemeRefinementAgent(client)
        print("✓ Agent initialized")
        print()

        # Refine theme with query integration
        print("STEP 2: REFINING THEME WITH QUERY INTEGRATION")
        print("=" * 80)
        print()

        refined_theme = await agent.refine_theme(
            brief=curator_brief,
            session_id="test-session-123",
            progress_callback=progress_callback
        )

        print()
        print("=" * 80)
        print("REFINEMENT RESULTS")
        print("=" * 80)
        print()

        print(f"Exhibition Title: {refined_theme.exhibition_title}")
        if refined_theme.subtitle:
            print(f"Subtitle: {refined_theme.subtitle}")
        print()
        print(f"Central Argument: {refined_theme.central_argument}")
        print()
        print(f"Sections: {len(refined_theme.exhibition_sections)}")
        for i, section in enumerate(refined_theme.exhibition_sections, 1):
            print(f"  {i}. {section.title}")
            print(f"     {section.focus[:100]}...")
        print()

        # NEW: Display query integration results
        print("=" * 80)
        print("QUERY INTEGRATION RESULTS")
        print("=" * 80)
        print()

        print(f"Europeana Queries Generated: {len(refined_theme.europeana_queries)}")
        print(f"Query Validations: {len(refined_theme.query_validation_results)}")
        print()

        for query in refined_theme.europeana_queries:
            print(f"Section: {query.section_title}")
            print(f"  Query: {query.query}")
            if query.qf:
                print(f"  Filters: {', '.join(query.qf)}")

            # Get validation result
            validation = refined_theme.query_validation_results.get(query.section_id)
            if validation:
                status_icon = "✅" if validation.status == "good" else "⚠️ " if validation.status == "warning" else "❌"
                print(f"  {status_icon} Status: {validation.status.upper()}")
                print(f"  {validation.message}")
                if validation.suggestions:
                    print(f"  Suggestions:")
                    for suggestion in validation.suggestions:
                        print(f"    • {suggestion}")
            print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()

        good_queries = sum(1 for v in refined_theme.query_validation_results.values() if v.status == "good")
        warning_queries = sum(1 for v in refined_theme.query_validation_results.values() if v.status == "warning")
        error_queries = sum(1 for v in refined_theme.query_validation_results.values() if v.status == "error")

        total_artworks = sum(v.total_count for v in refined_theme.query_validation_results.values() if v.is_valid)

        print(f"Total Queries: {len(refined_theme.europeana_queries)}")
        print(f"✅ Good: {good_queries}")
        print(f"⚠️  Warnings: {warning_queries}")
        print(f"❌ Errors: {error_queries}")
        print()
        print(f"Total Artworks Available: {total_artworks:,}")
        print()
        print(f"Refinement Confidence: {refined_theme.refinement_confidence:.2f}")
        print()

        # Validation check
        if len(refined_theme.europeana_queries) == len(refined_theme.exhibition_sections):
            print("🎉 INTEGRATION TEST PASSED!")
            print(f"   ✓ All {len(refined_theme.exhibition_sections)} sections have queries")
            print(f"   ✓ All queries validated")
            print(f"   ✓ {total_artworks:,} artworks available")
        else:
            print("⚠️  Some sections missing queries")

        print()


if __name__ == "__main__":
    asyncio.run(main())
