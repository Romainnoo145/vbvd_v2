#!/usr/bin/env python3
"""
Test Curator Input Validation
Demonstrates real validation with Getty AAT/ULAN resolution
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


async def test_concept_validation():
    """Test concept validation against Getty AAT"""
    print("\n🎯 Testing Concept Validation")
    print("-" * 50)

    async with EssentialDataClient() as data_client:
        validator = CuratorInputValidator(data_client)

        # Test concepts with mix of valid and invalid terms
        test_concepts = [
            "impressionism",      # Should be valid in Getty AAT
            "landscape painting", # Should be valid
            "chiaroscuro",       # Should be valid
            "xyz123invalid"      # Should be invalid
        ]

        concept_results = await validator._validate_concepts(test_concepts)

        for result in concept_results:
            status = "✅" if result.is_valid else "❌"
            print(f"{status} {result.concept}")
            print(f"   Getty AAT URI: {result.getty_aat_uri or 'Not found'}")
            print(f"   Confidence: {result.confidence_score:.2f}")
            print(f"   Message: {result.validation_message}")
            if result.suggested_alternatives:
                print(f"   Alternatives: {', '.join(result.suggested_alternatives)}")
            print()

        return concept_results


async def test_artist_validation():
    """Test artist validation against Getty ULAN and Wikidata"""
    print("\n👨‍🎨 Testing Artist Validation")
    print("-" * 50)

    async with EssentialDataClient() as data_client:
        validator = CuratorInputValidator(data_client)

        # Test artists with mix of well-known and unknown names
        test_artists = [
            "Claude Monet",         # Should be valid
            "Pablo Picasso",        # Should be valid
            "John Doe Artist"       # Should be invalid
        ]

        artist_results = await validator._validate_artists(test_artists)

        for result in artist_results:
            status = "✅" if result.is_valid else "❌"
            print(f"{status} {result.artist_name}")
            print(f"   Getty ULAN URI: {result.getty_ulan_uri or 'Not found'}")
            print(f"   Wikidata URI: {result.wikidata_uri or 'Not found'}")
            print(f"   Confidence: {result.confidence_score:.2f}")
            if result.birth_year:
                lifespan = f"{result.birth_year}"
                if result.death_year:
                    lifespan += f"-{result.death_year}"
                print(f"   Lifespan: {lifespan}")
            if result.nationality:
                print(f"   Nationality: {result.nationality}")
            print(f"   Message: {result.validation_message}")
            print()

        return artist_results


async def test_complete_validation():
    """Test complete curator brief validation"""
    print("\n📋 Testing Complete Brief Validation")
    print("-" * 50)

    # Create a realistic curator brief
    brief = CuratorBrief(
        theme_title="Impressionist Landscapes: Light and Color",
        theme_description="An exploration of how Impressionist painters revolutionized landscape painting through their innovative use of light, color, and plein air techniques, fundamentally changing our perception of the natural world.",
        theme_concepts=["impressionism", "landscape painting", "plein air", "color theory"],
        reference_artists=["Claude Monet", "Camille Pissarro", "Alfred Sisley"],
        target_audience="general",
        space_type="main",
        duration_weeks=16,
        budget_max=Decimal("250000"),
        include_international=True,
        curator_name="Dr. Sarah Johnson",
        exhibition_dates={
            "start": date(2024, 6, 15),
            "end": date(2024, 10, 15)
        }
    )

    print(f"📝 Brief: {brief.theme_title}")
    print(f"📍 Concepts: {brief.get_concept_string()}")
    print(f"👥 Artists: {brief.get_artist_string()}")
    print(f"💰 Budget: €{brief.budget_max:,}")
    print(f"⏱️  Duration: {brief.duration_weeks} weeks")

    async with EssentialDataClient() as data_client:
        validator = CuratorInputValidator(data_client)

        # Run complete validation
        validation_result = await validator.validate_curator_brief(brief)

    print(f"\n🎯 Validation Results")
    print("-" * 30)
    print(f"Status: {validation_result.validation_status.value.upper()}")
    print(f"Overall Confidence: {validation_result.overall_confidence:.1%}")
    print(f"Processing Time: {validation_result.processing_time_seconds:.2f}s")

    print(f"\n📊 Feasibility Assessment")
    print("-" * 30)
    feasibility = validation_result.feasibility_assessment
    print(f"Overall Score: {feasibility.overall_score:.1%}")
    print(f"Concept Coverage: {feasibility.concept_coverage:.1%}")
    print(f"Artist Availability: {feasibility.artist_availability:.1%}")
    print(f"Expected Artworks: ~{feasibility.expected_artworks}")
    print(f"Complexity: {feasibility.complexity_rating}")
    print(f"Success Probability: {feasibility.success_probability:.1%}")

    if feasibility.recommendations:
        print(f"\n💡 Recommendations")
        print("-" * 20)
        for i, rec in enumerate(feasibility.recommendations, 1):
            print(f"{i}. {rec}")

    if feasibility.risk_factors:
        print(f"\n⚠️  Risk Factors")
        print("-" * 15)
        for i, risk in enumerate(feasibility.risk_factors, 1):
            print(f"{i}. {risk}")

    print(f"\n📝 Validation Messages")
    print("-" * 25)
    for msg in validation_result.validation_messages:
        print(f"• {msg}")

    if validation_result.recommendations:
        print(f"\n🎯 Action Items")
        print("-" * 15)
        for i, rec in enumerate(validation_result.recommendations, 1):
            print(f"{i}. {rec}")

    return validation_result


async def test_invalid_brief():
    """Test validation with an invalid brief"""
    print("\n❌ Testing Invalid Brief Validation")
    print("-" * 50)

    # Create a brief with problematic elements
    brief = CuratorBrief(
        theme_title="Unknown Art Movement XYZ",
        theme_description="An exhibition about completely made-up art concepts that don't exist in any art historical context.",
        theme_concepts=["fakemovement123", "nonexistentconcept", "invalidterm"],
        reference_artists=["Fake Artist One", "Made Up Person", "Non Existent Painter"],
        target_audience="general",
        budget_max=Decimal("10000"),  # Very low budget
        duration_weeks=2,             # Very short duration
        include_international=True
    )

    print(f"📝 Brief: {brief.theme_title}")
    print(f"📍 Concepts: {brief.get_concept_string()}")
    print(f"👥 Artists: {brief.get_artist_string()}")

    data_client = EssentialDataClient()
    validator = CuratorInputValidator(data_client)

    validation_result = await validator.validate_curator_brief(brief)

    print(f"\n🎯 Validation Results")
    print("-" * 30)
    print(f"Status: {validation_result.validation_status.value.upper()}")
    print(f"Overall Confidence: {validation_result.overall_confidence:.1%}")

    print(f"\n📊 Issues Detected")
    print("-" * 20)
    feasibility = validation_result.feasibility_assessment
    print(f"Concept Coverage: {feasibility.concept_coverage:.1%}")
    print(f"Artist Availability: {feasibility.artist_availability:.1%}")
    print(f"Expected Artworks: ~{feasibility.expected_artworks}")

    if validation_result.recommendations:
        print(f"\n💡 Suggested Improvements")
        print("-" * 25)
        for i, rec in enumerate(validation_result.recommendations, 1):
            print(f"{i}. {rec}")

    return validation_result


async def main():
    """Run all validation tests"""
    print("=" * 60)
    print("🧪 AI CURATOR ASSISTANT - Input Validation Testing")
    print("=" * 60)

    try:
        # Test individual components
        await test_concept_validation()
        await test_artist_validation()

        # Test complete workflow
        valid_result = await test_complete_validation()
        invalid_result = await test_invalid_brief()

        print("\n" + "=" * 60)
        print("✅ ALL VALIDATION TESTS COMPLETED!")
        print("=" * 60)
        print("\nInput validation system is ready for:")
        print("• Pre-flight checking of curator briefs")
        print("• Getty AAT/ULAN resolution validation")
        print("• Feasibility assessment and recommendations")
        print("• Early feedback to prevent failed queries")

        # Summary
        print(f"\n📈 Test Summary")
        print("-" * 15)
        print(f"Valid brief confidence: {valid_result.overall_confidence:.1%}")
        print(f"Invalid brief confidence: {invalid_result.overall_confidence:.1%}")
        print(f"Validation working correctly: {'✅' if valid_result.overall_confidence > invalid_result.overall_confidence else '❌'}")

        return True

    except Exception as e:
        print(f"\n❌ VALIDATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)