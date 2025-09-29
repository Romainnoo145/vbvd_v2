"""
Test script for Artist Discovery Agent (Stage 2)
"""
import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.clients.essential_data_client import EssentialDataClient
from backend.agents.theme_refinement_agent import ThemeRefinementAgent, RefinedTheme, ConceptValidation, ThemeResearch
from backend.agents.artist_discovery_agent import ArtistDiscoveryAgent
from backend.models import CuratorBrief


async def test_artist_discovery():
    """Test the Artist Discovery Agent with a sample theme"""

    print("=" * 80)
    print("TESTING ARTIST DISCOVERY AGENT (Stage 2)")
    print("=" * 80)

    # Create a mock refined theme (output from Stage 1)
    # In production, this would come from the ThemeRefinementAgent
    mock_theme = RefinedTheme(
        original_brief_id="test-brief-001",
        session_id="test-session-001",
        exhibition_title="Impressionism and Light",
        subtitle="The Evolution of Color in 19th Century France",
        curatorial_statement="This exhibition explores how Impressionist artists revolutionized the depiction of light and color in painting.",
        theme_description="An exploration of Impressionist art and techniques",
        scholarly_rationale="Recent scholarship has emphasized the importance of Impressionism in modern art history.",
        validated_concepts=[
            ConceptValidation(
                original_concept="impressionism",
                refined_concept="Impressionism",
                getty_aat_uri="http://vocab.getty.edu/aat/300021503",
                getty_aat_id="300021503",
                definition="A style of painting that originated in France in the 1860s",
                confidence_score=0.95,
                historical_context="Revolutionary art movement of 19th century France",
                related_concepts=["Post-Impressionism", "Plein air painting"]
            ),
            ConceptValidation(
                original_concept="landscape painting",
                refined_concept="Landscape Painting",
                getty_aat_uri="http://vocab.getty.edu/aat/300015636",
                getty_aat_id="300015636",
                definition="Paintings depicting natural scenery",
                confidence_score=0.90,
                historical_context="Genre of art depicting outdoor scenes",
                related_concepts=["Seascape", "Cityscape"]
            ),
        ],
        primary_focus="Impressionism",
        secondary_themes=["Light", "Color Theory", "Plein Air Painting"],
        research_backing=ThemeResearch(
            wikipedia_sources=[],
            art_historical_context="Impressionism emerged in 1860s France",
            scholarly_background="Extensive scholarship on Impressionist techniques",
            current_discourse="Contemporary exhibitions emphasize technical innovation",
            key_developments=["Development of tube paints", "Plein air painting"],
            chronological_scope="1860s-1900s",
            geographical_scope="Primarily France, with international influence",
            research_confidence=0.85
        ),
        target_audience_refined="Art enthusiasts and general public",
        complexity_level="accessible",
        estimated_duration="3-4 months recommended",
        space_recommendations=["Natural lighting essential", "Large wall spaces"],
        refinement_confidence=0.88,
        created_at=datetime.utcnow(),
        agent_version="1.0"
    )

    print("\n📋 Mock Exhibition Theme:")
    print(f"   Title: {mock_theme.exhibition_title}")
    print(f"   Subtitle: {mock_theme.subtitle}")
    print(f"   Primary Focus: {mock_theme.primary_focus}")
    print(f"   Validated Concepts: {', '.join([c.refined_concept for c in mock_theme.validated_concepts])}")

    # Initialize data client and artist discovery agent
    async with EssentialDataClient() as data_client:
        # Check if Anthropic API key is available
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            print("\n✅ Anthropic API key found - LLM scoring enabled")
        else:
            print("\n⚠️  No Anthropic API key - using heuristic scoring fallback")

        artist_agent = ArtistDiscoveryAgent(data_client, anthropic_api_key=anthropic_key)

        print("\n🔍 Starting Artist Discovery...")
        print("   This will:")
        print("   1. Build SPARQL queries from validated concepts")
        print("   2. Search Wikidata for relevant artists")
        print("   3. Enrich with Getty ULAN authority data")
        print("   4. Add biographical info from Wikipedia")
        print("   5. Check institutional connections via Yale LUX")
        print("   6. Score relevance using LLM analysis")
        print()

        try:
            # Discover artists (limit to 10 for testing)
            discovered_artists = await artist_agent.discover_artists(
                refined_theme=mock_theme,
                session_id="test-session-001",
                max_artists=10,
                min_relevance=0.4  # Lower threshold for testing
            )

            print(f"\n✅ Discovery Complete!")
            print(f"   Found {len(discovered_artists)} relevant artists")
            print()

            # Display top artists
            print("=" * 80)
            print("TOP DISCOVERED ARTISTS")
            print("=" * 80)

            for i, artist in enumerate(discovered_artists[:5], 1):
                print(f"\n{i}. {artist.name}")
                print(f"   Relevance Score: {artist.relevance_score:.2f}")

                if artist.birth_year or artist.death_year:
                    lifespan = artist.get_lifespan()
                    print(f"   Lifespan: {lifespan}")

                if artist.nationality:
                    print(f"   Nationality: {artist.nationality}")

                if artist.movements:
                    print(f"   Movements: {', '.join(artist.movements[:3])}")

                if artist.known_works_count:
                    print(f"   Known Works: {artist.known_works_count}")

                if artist.institutional_connections:
                    print(f"   Institutions: {', '.join(artist.institutional_connections[:3])}")

                print(f"\n   💡 Relevance Reasoning:")
                reasoning_lines = artist.relevance_reasoning.split('. ')
                for line in reasoning_lines:
                    if line.strip():
                        print(f"      • {line.strip()}.")

                print(f"\n   📊 Data Sources: {', '.join(artist.discovery_sources)}")

                if artist.wikidata_id:
                    print(f"   🔗 Wikidata: https://www.wikidata.org/wiki/{artist.wikidata_id}")

                print()

            # Summary statistics
            print("=" * 80)
            print("DISCOVERY STATISTICS")
            print("=" * 80)

            if discovered_artists:
                avg_relevance = sum(a.relevance_score for a in discovered_artists) / len(discovered_artists)
                print(f"\nAverage Relevance Score: {avg_relevance:.2f}")
            else:
                print("\n⚠️  No artists discovered - check API connectivity and query logic")

            # Count by source
            source_counts = {}
            for artist in discovered_artists:
                for source in artist.discovery_sources:
                    source_counts[source] = source_counts.get(source, 0) + 1

            print(f"\nData Source Coverage:")
            for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
                print(f"   {source}: {count} artists")

            # Movement distribution
            movement_counts = {}
            for artist in discovered_artists:
                for movement in artist.movements:
                    movement_counts[movement] = movement_counts.get(movement, 0) + 1

            if movement_counts:
                print(f"\nTop Art Movements:")
                for movement, count in sorted(movement_counts.items(), key=lambda x: -x[1])[:5]:
                    print(f"   {movement}: {count} artists")

            # Nationality distribution
            nationality_counts = {}
            for artist in discovered_artists:
                if artist.nationality:
                    nationality_counts[artist.nationality] = nationality_counts.get(artist.nationality, 0) + 1

            if nationality_counts:
                print(f"\nNationality Distribution:")
                for nationality, count in sorted(nationality_counts.items(), key=lambda x: -x[1])[:5]:
                    print(f"   {nationality}: {count} artists")

            print("\n" + "=" * 80)
            print("TEST COMPLETED SUCCESSFULLY! ✅")
            print("=" * 80)

            return discovered_artists

        except Exception as e:
            print(f"\n❌ Error during artist discovery: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    print("\n🎨 AI Curator Assistant - Artist Discovery Agent Test")
    print("Testing Stage 2 of the 3-stage workflow\n")

    # Run the test
    results = asyncio.run(test_artist_discovery())

    if results:
        print(f"\n✨ Successfully discovered {len(results)} artists for the exhibition!")
    else:
        print("\n⚠️  Test completed with errors")
        sys.exit(1)