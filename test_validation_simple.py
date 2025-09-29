#!/usr/bin/env python3
"""
Simple Curator Input Validation Test
Quick test to verify validation system works with real data
"""

import sys
import asyncio
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models import CuratorBrief
from backend.clients.essential_data_client import EssentialDataClient
from backend.validators.curator_input_validator import CuratorInputValidator


async def main():
    """Test the validation system with a simple example"""
    print("=" * 60)
    print("🧪 CURATOR INPUT VALIDATION - Simple Test")
    print("=" * 60)

    # Create a realistic curator brief
    brief = CuratorBrief(
        theme_title="French Impressionism",
        theme_description="An exploration of French Impressionist painters and their revolutionary techniques in capturing light and color.",
        theme_concepts=["impressionism", "french art"],
        reference_artists=["Claude Monet", "Pierre-Auguste Renoir"],
        target_audience="general",
        duration_weeks=12,
        budget_max=Decimal("150000")
    )

    print(f"📝 Testing Brief: {brief.theme_title}")
    print(f"📍 Concepts: {brief.get_concept_string()}")
    print(f"👥 Artists: {brief.get_artist_string()}")

    try:
        async with EssentialDataClient() as data_client:
            validator = CuratorInputValidator(data_client)

            print("\n🔍 Running validation...")
            validation_result = await validator.validate_curator_brief(brief)

            print(f"\n🎯 Results:")
            print(f"Status: {validation_result.validation_status.value.upper()}")
            print(f"Confidence: {validation_result.overall_confidence:.1%}")
            print(f"Processing Time: {validation_result.processing_time_seconds:.2f}s")

            print(f"\n📊 Feasibility:")
            feasibility = validation_result.feasibility_assessment
            print(f"Expected Artworks: ~{feasibility.expected_artworks}")
            print(f"Success Probability: {feasibility.success_probability:.1%}")

            print(f"\n📋 Summary:")
            for msg in validation_result.validation_messages:
                print(f"• {msg}")

            if validation_result.recommendations:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(validation_result.recommendations[:3], 1):
                    print(f"{i}. {rec}")

            print(f"\n✅ Validation system working correctly!")
            return True

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)