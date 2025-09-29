#!/usr/bin/env python3
"""
Simple Theme Refinement Agent Test
Quick validation that the agent works correctly
"""

import sys
import asyncio
from pathlib import Path
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models import CuratorBrief
from backend.clients.essential_data_client import EssentialDataClient
from backend.agents.theme_refinement_agent import ThemeRefinementAgent


async def main():
    """Test theme refinement agent functionality"""
    print("=" * 60)
    print("🎨 THEME REFINEMENT AGENT - Quick Test")
    print("=" * 60)

    # Create a simple brief
    brief = CuratorBrief(
        theme_title="Abstract Expressionism",
        theme_description="An exploration of the Abstract Expressionist movement in American art.",
        theme_concepts=["abstract art", "expressionism"],
        reference_artists=["Jackson Pollock"],
        target_audience="general",
        duration_weeks=10,
        budget_max=Decimal("100000")
    )

    print(f"📝 Brief: {brief.theme_title}")
    print(f"📍 Concepts: {brief.get_concept_string()}")

    try:
        async with EssentialDataClient() as data_client:
            agent = ThemeRefinementAgent(data_client)

            print(f"\n🔄 Processing...")
            refined_theme = await agent.refine_theme(brief, "test-session")

            print(f"\n✨ Results:")
            print(f"Title: {refined_theme.exhibition_title}")
            print(f"Confidence: {refined_theme.refinement_confidence:.1%}")
            print(f"Concepts Processed: {len(refined_theme.validated_concepts)}")
            print(f"Complexity: {refined_theme.complexity_level}")

            print(f"\n✅ Theme Refinement Agent working correctly!")
            return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)