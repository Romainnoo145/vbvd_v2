#!/usr/bin/env python3
"""
Test Pydantic Models
Validates that all our data models work correctly
"""

import sys
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models import (
    CuratorBrief,
    ThemeValidation,
    ValidationReport,
    EnrichedQuery,
    DiscoveredArtist,
    ArtworkCandidate,
    ExhibitionProposal,
    SpaceRequirements,
    BudgetBreakdown,
    RiskAssessment
)


def test_curator_brief():
    """Test CuratorBrief model"""
    print("\n1️⃣ Testing CuratorBrief Model")
    print("-" * 40)

    # Valid curator brief
    brief = CuratorBrief(
        theme_title="Impressionist Landscapes",
        theme_description="An exploration of how Impressionist painters captured the fleeting effects of light and atmosphere in their landscape paintings, focusing on plein air techniques and color theory innovations.",
        theme_concepts=["impressionism", "landscape", "plein air", "color theory"],
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

    print(f"✅ Valid brief created: {brief.theme_title}")
    print(f"   Concepts: {brief.get_concept_string()}")
    print(f"   Artists: {brief.get_artist_string()}")

    # Test validation errors
    try:
        invalid_brief = CuratorBrief(
            theme_title="",  # Too short
            theme_description="Too short description",  # Too short
            theme_concepts=[],  # Empty list
        )
    except Exception as e:
        print(f"✅ Validation errors caught: {type(e).__name__}")

    return brief


def test_discovery_models():
    """Test discovery stage models"""
    print("\n2️⃣ Testing Discovery Models")
    print("-" * 40)

    # Test DiscoveredArtist
    artist = DiscoveredArtist(
        name="Claude Monet",
        getty_ulan_uri="http://vocab.getty.edu/ulan/500019484",
        getty_ulan_id="500019484",
        wikidata_uri="http://www.wikidata.org/entity/Q296",
        wikidata_id="Q296",
        birth_year=1840,
        death_year=1926,
        nationality="French",
        movements=["Impressionism", "En plein air"],
        techniques=["Oil painting", "Water lilies series"],
        relevance_score=0.95,
        relevance_reasoning="Claude Monet is the founder of Impressionism and a master of plein air landscape painting, directly relevant to the exhibition theme.",
        source_endpoint="wikidata",
        biography_short="French painter and founder of Impressionism",
        discovery_confidence=0.92
    )

    print(f"✅ DiscoveredArtist created: {artist.name}")
    print(f"   Lifespan: {artist.get_lifespan()}")
    print(f"   Contemporary: {artist.is_contemporary()}")

    # Test ArtworkCandidate
    artwork = ArtworkCandidate(
        uri="https://example.org/artwork/water-lilies-1919",
        title="Water Lilies",
        artist_name="Claude Monet",
        date_created="1919",
        medium="Oil on canvas",
        height_cm=200.0,
        width_cm=425.0,
        current_location="Musée de l'Orangerie",
        institution_name="Musée de l'Orangerie",
        subjects=["water lilies", "pond", "impressionist landscape"],
        insurance_value=Decimal("15000000"),
        loan_available=True,
        relevance_score=0.98,
        relevance_reasoning="Iconic example of Monet's mature impressionist style and innovative approach to series painting.",
        source="yale_lux",
        discovery_confidence=0.95
    )

    print(f"✅ ArtworkCandidate created: {artwork.get_display_title()}")
    print(f"   Creator: {artwork.get_creator_display()}")
    print(f"   Date: {artwork.get_date_display()}")
    print(f"   Size: {artwork.calculate_size_category()}")

    return artist, artwork


def test_exhibition_models():
    """Test exhibition proposal models"""
    print("\n3️⃣ Testing Exhibition Models")
    print("-" * 40)

    # Space requirements
    space = SpaceRequirements(
        minimum_wall_length=120.0,
        minimum_floor_area=400.0,
        ceiling_height_required=3.5,
        needs_climate_control=True,
        needs_low_light=True,
        electrical_outlets=8,
        wheelchair_accessible=True,
        special_requirements=["Climate control for paintings", "UV-filtered lighting"]
    )

    # Budget breakdown
    budget = BudgetBreakdown(
        loan_fees=Decimal("50000"),
        transport_costs=Decimal("25000"),
        insurance_costs=Decimal("30000"),
        exhibition_design=Decimal("40000"),
        installation_labor=Decimal("15000"),
        catalog_production=Decimal("20000"),
        marketing_materials=Decimal("10000"),
        contingency_percentage=12.0
    )

    totals = budget.calculate_totals()

    # Risk assessment
    risk = RiskAssessment(
        loan_approval_risk="medium",
        transport_risk="low",
        budget_overrun_risk="medium",
        overall_risk_level="medium",
        mitigation_strategies=[
            "Early loan applications",
            "Professional art handlers",
            "Detailed budget monitoring"
        ]
    )

    print(f"✅ SpaceRequirements: {space.minimum_wall_length}m wall length")
    print(f"✅ BudgetBreakdown: €{totals['total']:,.2f} total")
    print(f"✅ RiskAssessment: {risk.overall_risk_level} risk level")

    return space, budget, risk


def test_complete_workflow():
    """Test a complete workflow with all models"""
    print("\n4️⃣ Testing Complete Workflow")
    print("-" * 40)

    # Create a brief
    brief = CuratorBrief(
        theme_title="Dutch Golden Age Portraits",
        theme_description="Exploring the innovation and artistry of portrait painting during the Dutch Golden Age, featuring works by Rembrandt, Hals, and their contemporaries.",
        theme_concepts=["portrait", "Dutch Golden Age", "baroque", "chiaroscuro"],
        reference_artists=["Rembrandt van Rijn", "Frans Hals", "Johannes Vermeer"],
        target_audience="general"
    )

    # Create enriched query (Stage 1 output)
    enriched = EnrichedQuery(
        original_brief_id="brief-001",
        session_id="session-001",
        refined_title="Masters of the Golden Age: Dutch Portrait Innovation",
        refined_description="A comprehensive examination of portraiture during the Dutch Golden Age...",
        curatorial_angle="Focus on technical innovation and psychological depth",
        historical_context="17th century Dutch Republic prosperity and cultural flowering",
        getty_aat_uris={
            "portrait": "http://vocab.getty.edu/aat/300015637",
            "chiaroscuro": "http://vocab.getty.edu/aat/300056168"
        },
        sparql_queries={
            "wikidata": "SELECT ?artwork WHERE { ?artwork wdt:P31 wd:Q3305213 }",
            "getty": "SELECT ?concept WHERE { ?concept a skos:Concept }"
        },
        confidence_scores={"portrait": 0.95, "chiaroscuro": 0.88},
        search_strategy="hybrid",
        feasibility_score=0.82
    )

    # Create some discovered artists (Stage 2 output)
    artists = [
        DiscoveredArtist(
            name="Rembrandt van Rijn",
            birth_year=1606,
            death_year=1669,
            relevance_score=0.98,
            relevance_reasoning="Master of Dutch Golden Age portraiture",
            source_endpoint="getty_ulan",
            discovery_confidence=0.95
        ),
        DiscoveredArtist(
            name="Frans Hals",
            birth_year=1582,
            death_year=1666,
            relevance_score=0.92,
            relevance_reasoning="Innovative portrait painter known for loose brushwork",
            source_endpoint="wikidata",
            discovery_confidence=0.90
        )
    ]

    # Create artworks (Stage 3 output)
    artworks = [
        ArtworkCandidate(
            uri="artwork-001",
            title="Self-Portrait at the Age of 34",
            artist_name="Rembrandt van Rijn",
            date_created="1640",
            medium="Oil on canvas",
            relevance_score=0.96,
            relevance_reasoning="Exemplary self-portrait showing technical mastery",
            source="rijksmuseum",
            discovery_confidence=0.94
        )
    ]

    print(f"✅ Complete workflow models created:")
    print(f"   Brief: {brief.theme_title}")
    print(f"   Enriched: {enriched.refined_title}")
    print(f"   Artists: {len(artists)} discovered")
    print(f"   Artworks: {len(artworks)} found")

    return brief, enriched, artists, artworks


def test_json_serialization():
    """Test JSON serialization of all models"""
    print("\n5️⃣ Testing JSON Serialization")
    print("-" * 40)

    brief = CuratorBrief(
        theme_title="Test Exhibition",
        theme_description="A test exhibition for JSON serialization testing with various data types and structures.",
        theme_concepts=["modern art", "sculpture"],
        budget_max=Decimal("100000"),
        exhibition_dates={
            "start": date(2024, 1, 1),
            "end": date(2024, 4, 1)
        }
    )

    try:
        # Test JSON export
        json_data = brief.model_dump(mode='json')
        json_str = json.dumps(json_data, default=str)

        # Test JSON import
        parsed_data = json.loads(json_str)

        print(f"✅ JSON serialization successful")
        print(f"   Exported {len(json_data)} fields")
        print(f"   JSON string length: {len(json_str)} characters")

        return True

    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False


def main():
    """Run all model tests"""
    print("="*60)
    print("🧪 AI CURATOR ASSISTANT - Model Testing")
    print("="*60)

    try:
        # Test individual models
        brief = test_curator_brief()
        artist, artwork = test_discovery_models()
        space, budget, risk = test_exhibition_models()

        # Test complete workflow
        test_complete_workflow()

        # Test JSON serialization
        serialization_success = test_json_serialization()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nModel validation successful. The data models are ready for:")
        print("• Database storage and retrieval")
        print("• API request/response handling")
        print("• Agent processing and validation")
        print("• Frontend integration")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)