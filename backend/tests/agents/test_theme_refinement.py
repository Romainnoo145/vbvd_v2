"""
Test script for Theme Refinement Agent
Runs the actual agent with real curator input
"""
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

from backend.clients.essential_data_client import EssentialDataClient
from backend.agents.theme_refinement_agent import ThemeRefinementAgent
from backend.models import CuratorBrief


async def test_theme_refinement():
    """Test theme refinement with real curator input"""

    # Create a realistic curator brief about Geometric Abstraction
    curator_brief = CuratorBrief(
        theme_title="Geometry and Order",
        theme_description="An exhibition exploring geometric abstraction in modern art, focusing on how artists use geometric forms, mathematical precision, and primary colors to create pure visual experiences. Looking at the transition from figurative to abstract art through geometric reduction.",
        theme_concepts=[
            "geometric abstraction",
            "minimalism",
            "constructivism",
            "De Stijl",
            "color theory"
        ],
        reference_artists=[
            "Piet Mondrian",
            "Kazimir Malevich",
            "Theo van Doesburg",
            "El Lissitzky"
        ],
        target_audience="general",
        duration_weeks=16,
        space_type="main",
        include_international=True
    )

    print("=" * 80)
    print("TESTING THEME REFINEMENT AGENT")
    print("=" * 80)
    print("\n📝 INPUT - Curator Brief:")
    print(f"   Title: {curator_brief.theme_title}")
    print(f"   Description: {curator_brief.theme_description[:100]}...")
    print(f"   Concepts: {', '.join(curator_brief.theme_concepts)}")
    print(f"   Reference Artists: {', '.join(curator_brief.reference_artists)}")
    print(f"   Target Audience: {curator_brief.target_audience}")
    print(f"   Duration: {curator_brief.duration_weeks} weeks")
    print("\n" + "=" * 80)
    print("🤖 RUNNING THEME REFINEMENT AGENT...")
    print("=" * 80)

    # Initialize the agent
    data_client = EssentialDataClient()
    theme_agent = ThemeRefinementAgent(data_client)

    # Run theme refinement
    session_id = "test-session-001"
    refined_theme = await theme_agent.refine_theme(curator_brief, session_id)

    # Display results
    print("\n" + "=" * 80)
    print("✅ OUTPUT - Refined Exhibition Theme")
    print("=" * 80)

    print(f"\n🎨 EXHIBITION TITLE:")
    print(f"   {refined_theme.exhibition_title}")
    if refined_theme.subtitle:
        print(f"   Subtitle: {refined_theme.subtitle}")

    print(f"\n💡 CENTRAL ARGUMENT:")
    print(f"   {refined_theme.central_argument}")

    print(f"\n📜 CURATORIAL STATEMENT:")
    print(f"   {refined_theme.curatorial_statement}")

    print(f"\n📚 SCHOLARLY RATIONALE:")
    print(f"   {refined_theme.scholarly_rationale}")

    print(f"\n🏛️ EXHIBITION SECTIONS ({len(refined_theme.exhibition_sections)}):")
    for i, section in enumerate(refined_theme.exhibition_sections, 1):
        print(f"   {i}. {section.title}")
        print(f"      Focus: {section.focus}")
        print(f"      Artworks: ~{section.estimated_artwork_count}")
        if section.artist_emphasis:
            print(f"      Artists: {', '.join(section.artist_emphasis[:3])}")

    print(f"\n🚪 OPENING WALL TEXT:")
    print(f"   {refined_theme.opening_wall_text}")

    print(f"\n❓ KEY QUESTIONS:")
    for i, question in enumerate(refined_theme.key_questions, 1):
        print(f"   {i}. {question}")

    print(f"\n🌍 CONTEMPORARY RELEVANCE:")
    print(f"   {refined_theme.contemporary_relevance}")

    print(f"\n💭 VISITOR TAKEAWAY:")
    print(f"   {refined_theme.visitor_takeaway}")

    print(f"\n✍️ WALL TEXT STRATEGY:")
    print(f"   {refined_theme.wall_text_strategy}")

    print(f"\n🎓 EDUCATIONAL ANGLES:")
    for i, angle in enumerate(refined_theme.educational_angles, 1):
        print(f"   {i}. {angle}")

    print(f"\n📊 VALIDATED CONCEPTS ({len(refined_theme.validated_concepts)}):")
    for concept in refined_theme.validated_concepts[:5]:
        print(f"   • {concept.refined_concept} (confidence: {concept.confidence_score:.2f})")
        if concept.getty_aat_uri:
            print(f"     Getty AAT: {concept.getty_aat_uri}")

    print(f"\n🎯 METADATA:")
    print(f"   Target Audience: {refined_theme.target_audience_refined}")
    print(f"   Complexity: {refined_theme.complexity_level}")
    print(f"   Duration: {refined_theme.estimated_duration}")
    print(f"   Refinement Confidence: {refined_theme.refinement_confidence:.2f}")
    print(f"   Iteration Count: {refined_theme.iteration_count}")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

    # Test re-refinement
    print("\n" + "=" * 80)
    print("🔄 TESTING ITERATIVE REFINEMENT")
    print("=" * 80)

    feedback = "Make the title shorter and more punchy. Focus more on Dutch artists."
    print(f"\n📝 FEEDBACK: {feedback}")
    print("\n🤖 Re-refining theme...")

    updated_theme = await theme_agent.re_refine_theme(
        previous_theme=refined_theme,
        feedback=feedback,
        original_brief=curator_brief
    )

    print(f"\n✅ UPDATED THEME:")
    print(f"   New Title: {updated_theme.exhibition_title}")
    print(f"   Iteration Count: {updated_theme.iteration_count}")
    print(f"   Central Argument: {updated_theme.central_argument}")

    print("\n" + "=" * 80)
    print("✅ ITERATIVE REFINEMENT TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_theme_refinement())
