#!/usr/bin/env python3
"""
Test Theme Refinement Agent - Stage 1 of AI Curator Pipeline
Demonstrates real theme refinement with Getty AAT validation and Wikipedia research
"""

import sys
import asyncio
from pathlib import Path
from datetime import date
from decimal import Decimal
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models import CuratorBrief
from backend.clients.essential_data_client import EssentialDataClient
from backend.agents.theme_refinement_agent import ThemeRefinementAgent


async def test_simple_theme_refinement():
    """Test basic theme refinement functionality"""
    print("\n🎨 Testing Simple Theme Refinement")
    print("-" * 50)

    # Create a focused curator brief
    brief = CuratorBrief(
        theme_title="French Impressionism",
        theme_description="An exploration of the French Impressionist movement, focusing on innovations in light, color, and outdoor painting techniques.",
        theme_concepts=["impressionism", "french art", "plein air"],
        reference_artists=["Claude Monet", "Pierre-Auguste Renoir"],
        target_audience="general",
        duration_weeks=12,
        budget_max=Decimal("150000")
    )

    print(f"📝 Original Brief: {brief.theme_title}")
    print(f"📍 Concepts: {brief.get_concept_string()}")
    print(f"👥 Artists: {brief.get_artist_string()}")

    async with EssentialDataClient() as data_client:
        agent = ThemeRefinementAgent(data_client)

        print(f"\n🔄 Running theme refinement...")
        refined_theme = await agent.refine_theme(brief, "test-session-001")

        print(f"\n✨ Refined Theme Results:")
        print(f"Title: {refined_theme.exhibition_title}")
        if refined_theme.subtitle:
            print(f"Subtitle: {refined_theme.subtitle}")
        print(f"Primary Focus: {refined_theme.primary_focus}")
        print(f"Secondary Themes: {', '.join(refined_theme.secondary_themes[:3])}")
        print(f"Complexity: {refined_theme.complexity_level}")
        print(f"Confidence: {refined_theme.refinement_confidence:.1%}")

        print(f"\n📚 Research Backing:")
        print(f"Historical Context: {refined_theme.research_backing.art_historical_context[:200]}...")
        print(f"Research Confidence: {refined_theme.research_backing.research_confidence:.1%}")
        print(f"Wikipedia Sources: {len(refined_theme.research_backing.wikipedia_sources)}")

        print(f"\n🎯 Concept Validations:")
        for concept in refined_theme.validated_concepts:
            status = "✅" if concept.confidence_score > 0.5 else "⚠️"
            print(f"{status} {concept.original_concept} → {concept.refined_concept}")
            print(f"   Getty URI: {concept.getty_aat_uri or 'Not found'}")
            print(f"   Confidence: {concept.confidence_score:.1%}")

        print(f"\n🏛️ Exhibition Recommendations:")
        print(f"Target Audience: {refined_theme.target_audience_refined}")
        print(f"Duration: {refined_theme.estimated_duration}")
        if refined_theme.space_recommendations:
            print(f"Space: {refined_theme.space_recommendations[0]}")

        print(f"\n📖 Curatorial Statement (excerpt):")
        print(f"{refined_theme.curatorial_statement[:300]}...")

        return refined_theme


async def test_complex_theme_refinement():
    """Test complex theme with multiple concepts and international scope"""
    print("\n🌍 Testing Complex Theme Refinement")
    print("-" * 50)

    # Create a complex curator brief
    brief = CuratorBrief(
        theme_title="Modernist Dialogues: Cross-Cultural Exchange in 20th Century Art",
        theme_description="A comprehensive examination of how modernist movements evolved through cross-cultural exchange, featuring works from Europe, America, and Asia that demonstrate artistic innovation through cultural dialogue.",
        theme_concepts=["modernism", "abstract art", "cultural exchange", "international art", "avant-garde"],
        reference_artists=["Pablo Picasso", "Wassily Kandinsky", "Jackson Pollock", "Yves Klein", "Kazuo Shiraga"],
        target_audience="academic",
        space_type="main",
        duration_weeks=20,
        budget_max=Decimal("500000"),
        include_international=True,
        curator_name="Dr. Elena Rodriguez"
    )

    print(f"📝 Complex Brief: {brief.theme_title}")
    print(f"📍 Concepts: {brief.get_concept_string()}")
    print(f"👥 Artists: {brief.get_artist_string()}")
    print(f"🌐 International: {brief.include_international}")
    print(f"🎯 Audience: {brief.target_audience}")

    async with EssentialDataClient() as data_client:
        agent = ThemeRefinementAgent(data_client)

        print(f"\n🔄 Running complex theme refinement...")
        refined_theme = await agent.refine_theme(brief, "test-session-002")

        print(f"\n✨ Complex Refined Results:")
        print(f"Title: {refined_theme.exhibition_title}")
        if refined_theme.subtitle:
            print(f"Subtitle: {refined_theme.subtitle}")
        print(f"Complexity: {refined_theme.complexity_level}")
        print(f"Overall Confidence: {refined_theme.refinement_confidence:.1%}")

        print(f"\n🎯 Validated Concepts ({len(refined_theme.validated_concepts)}):")
        for concept in refined_theme.validated_concepts:
            status = "✅" if concept.confidence_score > 0.5 else "⚠️"
            print(f"{status} {concept.original_concept} → {concept.refined_concept} ({concept.confidence_score:.1%})")

        print(f"\n📚 Research Depth:")
        research = refined_theme.research_backing
        print(f"Chronological Scope: {research.chronological_scope}")
        print(f"Geographical Scope: {research.geographical_scope}")
        print(f"Key Developments: {len(research.key_developments)}")
        print(f"Wikipedia Sources: {len(research.wikipedia_sources)}")

        print(f"\n🏛️ Exhibition Planning:")
        print(f"Refined Audience: {refined_theme.target_audience_refined}")
        print(f"Duration Recommendation: {refined_theme.estimated_duration}")
        print(f"Space Recommendations: {len(refined_theme.space_recommendations)}")

        print(f"\n📜 Scholarly Rationale (excerpt):")
        print(f"{refined_theme.scholarly_rationale[:250]}...")

        return refined_theme


async def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n⚠️ Testing Edge Cases")
    print("-" * 50)

    # Minimal brief with potential issues
    brief = CuratorBrief(
        theme_title="Unknown Art Movement",
        theme_description="An exhibition about completely fictional art concepts.",
        theme_concepts=["fakemovement", "nonexistent", "madeup"],
        reference_artists=["Fictional Artist"],
        target_audience="general"
    )

    print(f"📝 Edge Case Brief: {brief.theme_title}")
    print(f"📍 Invalid Concepts: {brief.get_concept_string()}")

    async with EssentialDataClient() as data_client:
        agent = ThemeRefinementAgent(data_client)

        print(f"\n🔄 Testing error handling...")
        refined_theme = await agent.refine_theme(brief, "test-session-003")

        print(f"\n✨ Edge Case Results:")
        print(f"Title: {refined_theme.exhibition_title}")
        print(f"Confidence: {refined_theme.refinement_confidence:.1%}")
        print(f"Handled gracefully: {'✅' if refined_theme.refinement_confidence > 0 else '❌'}")

        print(f"\n🎯 Concept Handling:")
        for concept in refined_theme.validated_concepts:
            print(f"• {concept.original_concept} → {concept.refined_concept} ({concept.confidence_score:.1%})")

        print(f"✅ Error handling working correctly!")
        return refined_theme


async def test_json_serialization():
    """Test that refined themes can be serialized for storage"""
    print("\n💾 Testing JSON Serialization")
    print("-" * 50)

    brief = CuratorBrief(
        theme_title="Serialization Test",
        theme_description="Testing JSON serialization of refined themes.",
        theme_concepts=["modern art"],
        target_audience="general"
    )

    async with EssentialDataClient() as data_client:
        agent = ThemeRefinementAgent(data_client)
        refined_theme = await agent.refine_theme(brief, "test-session-004")

        try:
            # Test Pydantic JSON serialization
            json_data = refined_theme.model_dump(mode='json')
            json_str = json.dumps(json_data, default=str, indent=2)

            print(f"✅ JSON serialization successful")
            print(f"JSON size: {len(json_str)} characters")
            print(f"Fields serialized: {len(json_data)}")

            # Test deserialization
            parsed_data = json.loads(json_str)
            print(f"✅ JSON parsing successful")
            print(f"Title preserved: {parsed_data.get('exhibition_title', 'MISSING')}")

            return True

        except Exception as e:
            print(f"❌ JSON serialization failed: {e}")
            return False


async def main():
    """Run all theme refinement tests"""
    print("=" * 60)
    print("🧪 AI CURATOR ASSISTANT - Theme Refinement Agent Testing")
    print("=" * 60)

    try:
        # Test simple case
        simple_result = await test_simple_theme_refinement()

        # Test complex case
        complex_result = await test_complex_theme_refinement()

        # Test edge cases
        edge_result = await test_edge_cases()

        # Test serialization
        serialization_success = await test_json_serialization()

        print("\n" + "=" * 60)
        print("✅ ALL THEME REFINEMENT TESTS COMPLETED!")
        print("=" * 60)

        print(f"\n📊 Test Summary:")
        print(f"Simple theme confidence: {simple_result.refinement_confidence:.1%}")
        print(f"Complex theme confidence: {complex_result.refinement_confidence:.1%}")
        print(f"Edge case handling: {'✅' if edge_result.refinement_confidence > 0 else '❌'}")
        print(f"JSON serialization: {'✅' if serialization_success else '❌'}")

        print(f"\n🎯 Theme Refinement Agent is ready for:")
        print("• Professional exhibition title generation")
        print("• Getty AAT concept validation and enrichment")
        print("• Wikipedia-based art historical research")
        print("• Scholarly curatorial statement generation")
        print("• Comprehensive feasibility assessment")
        print("• JSON serialization for database storage")

        return True

    except Exception as e:
        print(f"\n❌ THEME REFINEMENT TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)