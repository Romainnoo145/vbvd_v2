"""
Real Pipeline Test - End-to-End Test with Actual Curator Input
Tests Stage 1 (Theme Refinement) → Stage 2 (Artist Discovery) with real data
"""
import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.clients.essential_data_client import EssentialDataClient
from backend.agents.theme_refinement_agent import ThemeRefinementAgent
from backend.agents.artist_discovery_agent import ArtistDiscoveryAgent
from backend.models import CuratorBrief


async def test_real_pipeline():
    """
    Test the full 2-stage pipeline with real curator input
    Stage 1: Theme Refinement → Stage 2: Artist Discovery
    """

    print("=" * 80)
    print("REAL AI CURATOR PIPELINE TEST")
    print("Stage 1: Theme Refinement → Stage 2: Artist Discovery")
    print("=" * 80)

    # Real curator input - simulating what a museum curator would submit
    curator_input = CuratorBrief(
        theme_title="Dutch Golden Age: Light and Domestic Life",
        theme_description="""
        I want to create an exhibition exploring how 17th century Dutch painters
        depicted everyday domestic scenes and the innovative use of light.
        Focus on interior scenes, still life, and the revolutionary painting
        techniques that made Dutch art unique during this period.
        """,
        theme_concepts=[
            "dutch golden age",
            "interior scenes",
            "still life",
            "chiaroscuro",
            "genre painting"
        ],
        reference_artists=[
            "Vermeer",
            "Rembrandt",
            "Jan Steen"
        ],
        target_audience="general",
        space_type="main",
        duration_weeks=16,
        include_international=True
    )

    print("\n📋 CURATOR INPUT:")
    print(f"   Theme: {curator_input.theme_title}")
    print(f"   Description: {curator_input.theme_description.strip()[:200]}...")
    print(f"   Concepts: {', '.join(curator_input.theme_concepts)}")
    print(f"   Reference Artists: {', '.join(curator_input.reference_artists)}")
    print(f"   Target Audience: {curator_input.target_audience}")
    print(f"   Duration: {curator_input.duration_weeks} weeks")

    session_id = f"real-test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    async with EssentialDataClient() as data_client:

        # ===================================================================
        # STAGE 1: THEME REFINEMENT
        # ===================================================================
        print("\n" + "=" * 80)
        print("STAGE 1: THEME REFINEMENT")
        print("=" * 80)
        print("\n🔍 Validating concepts with Getty AAT...")
        print("🔍 Researching art historical context via Wikipedia...")
        print("🔍 Gathering scholarly background...")

        theme_agent = ThemeRefinementAgent(data_client)

        try:
            refined_theme = await theme_agent.refine_theme(
                brief=curator_input,
                session_id=session_id
            )

            print("\n✅ STAGE 1 COMPLETE!")
            print("\n📊 REFINED THEME OUTPUT:")
            print(f"   Exhibition Title: {refined_theme.exhibition_title}")
            if refined_theme.subtitle:
                print(f"   Subtitle: {refined_theme.subtitle}")
            print(f"   Complexity Level: {refined_theme.complexity_level}")
            print(f"   Primary Focus: {refined_theme.primary_focus}")
            print(f"   Refinement Confidence: {refined_theme.refinement_confidence:.2%}")

            print(f"\n   📝 Curatorial Statement:")
            statement_lines = refined_theme.curatorial_statement.split('. ')
            for line in statement_lines[:3]:  # First 3 sentences
                if line.strip():
                    print(f"      {line.strip()}.")

            print(f"\n   🎯 Validated Concepts ({len(refined_theme.validated_concepts)}):")
            for concept in refined_theme.validated_concepts[:5]:
                getty_status = "✓ Getty AAT" if concept.getty_aat_uri else "✗ Not in Getty"
                print(f"      • {concept.refined_concept} (confidence: {concept.confidence_score:.2f}) - {getty_status}")

            print(f"\n   📚 Research Backing:")
            print(f"      • Wikipedia Sources: {len(refined_theme.research_backing.wikipedia_sources)}")
            print(f"      • Chronological Scope: {refined_theme.research_backing.chronological_scope}")
            print(f"      • Geographical Scope: {refined_theme.research_backing.geographical_scope}")
            print(f"      • Research Confidence: {refined_theme.research_backing.research_confidence:.2%}")

            # ===================================================================
            # STAGE 2: ARTIST DISCOVERY
            # ===================================================================
            print("\n" + "=" * 80)
            print("STAGE 2: ARTIST DISCOVERY")
            print("=" * 80)
            print("\n🔍 Building SPARQL queries from validated concepts...")
            print("🔍 Searching Wikidata for relevant artists...")
            print("🔍 Enriching with Getty ULAN authority records...")
            print("🔍 Adding biographical data from Wikipedia...")
            print("🔍 Checking institutional presence via Yale LUX...")
            print("🔍 Scoring artist relevance...")

            # Check for Anthropic API key
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_key:
                print("   ✅ Using LLM-based relevance scoring")
            else:
                print("   ⚠️  Using heuristic scoring (no Anthropic API key)")

            artist_agent = ArtistDiscoveryAgent(data_client, anthropic_api_key=anthropic_key)

            discovered_artists = await artist_agent.discover_artists(
                refined_theme=refined_theme,
                session_id=session_id,
                max_artists=15,
                min_relevance=0.3  # Lower threshold for diverse results
            )

            print("\n✅ STAGE 2 COMPLETE!")
            print(f"\n📊 DISCOVERED {len(discovered_artists)} RELEVANT ARTISTS")

            if discovered_artists:
                # ===================================================================
                # EXHIBITION PROPOSAL PREVIEW
                # ===================================================================
                print("\n" + "=" * 80)
                print("EXHIBITION PROPOSAL PREVIEW")
                print("=" * 80)

                print(f"\n🎨 EXHIBITION: {refined_theme.exhibition_title}")
                if refined_theme.subtitle:
                    print(f"    {refined_theme.subtitle}")

                print(f"\n📅 Duration: {refined_theme.estimated_duration}")
                print(f"👥 Target Audience: {refined_theme.target_audience_refined}")
                print(f"🎯 Complexity: {refined_theme.complexity_level.title()}")

                print(f"\n📋 Curatorial Statement (First Paragraph):")
                first_para = refined_theme.curatorial_statement.split('.')[0] + '.'
                print(f"   {first_para}")

                print(f"\n👨‍🎨 TOP ARTISTS FOR EXHIBITION ({len(discovered_artists[:10])} shown):")
                print("   " + "-" * 76)

                for i, artist in enumerate(discovered_artists[:10], 1):
                    print(f"\n   {i}. {artist.name}")

                    if artist.birth_year or artist.death_year:
                        lifespan = artist.get_lifespan()
                        print(f"      {lifespan}")

                    if artist.nationality:
                        print(f"      Nationality: {artist.nationality}")

                    print(f"      Relevance Score: {artist.relevance_score:.2%}")

                    if artist.movements:
                        print(f"      Movements: {', '.join(artist.movements[:2])}")

                    if artist.known_works_count:
                        print(f"      Known Works: {artist.known_works_count}")

                    # Show first sentence of reasoning
                    reasoning_first = artist.relevance_reasoning.split('.')[0] + '.'
                    print(f"      💡 Why: {reasoning_first}")

                    if artist.wikidata_id:
                        print(f"      🔗 https://www.wikidata.org/wiki/{artist.wikidata_id}")

                # ===================================================================
                # STATISTICS & INSIGHTS
                # ===================================================================
                print("\n" + "=" * 80)
                print("PIPELINE STATISTICS & INSIGHTS")
                print("=" * 80)

                print(f"\n📊 Theme Refinement:")
                print(f"   • Concepts Validated: {len(refined_theme.validated_concepts)}")
                print(f"   • Getty AAT Matches: {sum(1 for c in refined_theme.validated_concepts if c.getty_aat_uri)}")
                print(f"   • Wikipedia Sources: {len(refined_theme.research_backing.wikipedia_sources)}")
                print(f"   • Refinement Confidence: {refined_theme.refinement_confidence:.2%}")

                print(f"\n👨‍🎨 Artist Discovery:")
                print(f"   • Total Artists Found: {len(discovered_artists)}")

                avg_relevance = sum(a.relevance_score for a in discovered_artists) / len(discovered_artists)
                print(f"   • Average Relevance: {avg_relevance:.2%}")

                high_relevance = sum(1 for a in discovered_artists if a.relevance_score >= 0.7)
                print(f"   • High Relevance (≥70%): {high_relevance} artists")

                # Data source coverage
                source_counts = {}
                for artist in discovered_artists:
                    for source in artist.discovery_sources:
                        source_counts[source] = source_counts.get(source, 0) + 1

                print(f"\n📚 Data Source Coverage:")
                for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
                    percentage = (count / len(discovered_artists)) * 100
                    print(f"   • {source.title()}: {count} artists ({percentage:.1f}%)")

                # Movement distribution
                movement_counts = {}
                for artist in discovered_artists:
                    for movement in artist.movements:
                        movement_counts[movement] = movement_counts.get(movement, 0) + 1

                if movement_counts:
                    print(f"\n🎨 Art Movement Distribution:")
                    for movement, count in sorted(movement_counts.items(), key=lambda x: -x[1])[:5]:
                        print(f"   • {movement}: {count} artists")

                # Geographic distribution
                nationality_counts = {}
                for artist in discovered_artists:
                    if artist.nationality:
                        nationality_counts[artist.nationality] = nationality_counts.get(artist.nationality, 0) + 1

                if nationality_counts:
                    print(f"\n🌍 Geographic Distribution:")
                    for nat, count in sorted(nationality_counts.items(), key=lambda x: -x[1])[:5]:
                        print(f"   • {nat}: {count} artists")

                # Temporal distribution
                centuries = {}
                for artist in discovered_artists:
                    if artist.birth_year:
                        century = (artist.birth_year // 100) + 1
                        century_str = f"{century}th century"
                        centuries[century_str] = centuries.get(century_str, 0) + 1

                if centuries:
                    print(f"\n📅 Temporal Distribution:")
                    for century, count in sorted(centuries.items()):
                        print(f"   • {century}: {count} artists")

                print("\n" + "=" * 80)
                print("NEXT STEPS FOR CURATOR")
                print("=" * 80)
                print("""
   ✅ Stage 1 Complete: Theme validated and refined with scholarly backing
   ✅ Stage 2 Complete: Artists discovered and ranked by relevance

   🎯 Human-in-the-Loop Validation Point:
      → Review the discovered artists
      → Select artists for inclusion in exhibition
      → Provide feedback on relevance scores

   ⏭️  Next: Stage 3 - Artwork Discovery
      Once artists are validated, the system will:
      → Search Yale LUX for specific artworks by selected artists
      → Query Wikidata for additional artwork metadata
      → Fetch IIIF manifests for visual content
      → Score artwork relevance to exhibition theme
      → Check loan feasibility and practical considerations
      → Generate curated artwork list ready for exhibition
                """)

            else:
                print("\n⚠️  No artists discovered - API connectivity or query issues")
                print("    Check network connection to Wikidata, Getty, and Wikipedia")

            print("\n" + "=" * 80)
            print("PIPELINE TEST COMPLETE ✅")
            print("=" * 80)

            return refined_theme, discovered_artists

        except Exception as e:
            print(f"\n❌ Pipeline Error: {e}")
            import traceback
            traceback.print_exc()
            return None, None


if __name__ == "__main__":
    print("\n🎨 AI Curator Assistant - Real Pipeline Test")
    print("Testing 2-stage workflow with actual curator input and live data\n")

    # Run the pipeline
    results = asyncio.run(test_real_pipeline())

    if results[0] and results[1]:
        print(f"\n✨ Successfully completed 2-stage pipeline!")
        print(f"   Theme refined and {len(results[1])} artists discovered")
    else:
        print("\n⚠️  Pipeline test encountered issues")
        sys.exit(1)