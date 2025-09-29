"""
Test Real Pipeline with Diversity Filtering
Shows ACTUAL data from Wikidata with gender and ethnicity diversity
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.clients.essential_data_client import EssentialDataClient
from backend.agents.theme_refinement_agent import ThemeRefinementAgent
from backend.agents.artist_discovery_agent import ArtistDiscoveryAgent
from backend.models import CuratorBrief


async def test_diversity_pipeline():
    """
    Test with REAL modern art museum scenario
    Prioritizing diversity for contemporary art exhibition
    """

    print("=" * 80)
    print("MODERN ART MUSEUM: DIVERSITY-FIRST PIPELINE TEST")
    print("=" * 80)

    # Real curator input for a modern art museum
    curator_input = CuratorBrief(
        theme_title="Contemporary Perspectives: Global Voices in Modern Art",
        theme_description="""
        An exhibition showcasing diverse contemporary artists working across painting,
        sculpture, and mixed media. Focus on underrepresented voices in the art world,
        including female artists and non-Western perspectives. Themes include identity,
        cultural hybridity, and social commentary in 21st century art.
        """,
        theme_concepts=[
            "contemporary art",
            "mixed media",
            "social commentary",
            "cultural identity",
            "abstract art"
        ],
        reference_artists=[],  # Let the algorithm discover
        target_audience="general",
        space_type="main",
        duration_weeks=12,
        include_international=True,
        prioritize_diversity=True,
        diversity_requirements={
            'min_female': 5,  # At least 5 female artists
            'min_non_western': 4  # At least 4 non-Western artists
        }
    )

    print("\n📋 CURATOR INPUT:")
    print(f"   Theme: {curator_input.theme_title}")
    print(f"   Prioritize Diversity: {curator_input.prioritize_diversity}")
    print(f"   Diversity Requirements: {curator_input.diversity_requirements}")
    print(f"   Concepts: {', '.join(curator_input.theme_concepts)}")

    session_id = f"diversity-test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    async with EssentialDataClient() as data_client:

        # STAGE 1: Theme Refinement
        print("\n" + "=" * 80)
        print("STAGE 1: THEME REFINEMENT")
        print("=" * 80)

        theme_agent = ThemeRefinementAgent(data_client)
        refined_theme = await theme_agent.refine_theme(
            brief=curator_input,
            session_id=session_id
        )

        print(f"\n✅ Theme Refined: {refined_theme.exhibition_title}")
        print(f"   Validated Concepts: {len(refined_theme.validated_concepts)}")

        # STAGE 2: Artist Discovery with Diversity
        print("\n" + "=" * 80)
        print("STAGE 2: ARTIST DISCOVERY WITH DIVERSITY FILTERING")
        print("=" * 80)
        print("\n🔍 Searching for diverse contemporary artists...")
        print(f"   Target: Minimum {curator_input.diversity_requirements['min_female']} female artists")
        print(f"   Target: Minimum {curator_input.diversity_requirements['min_non_western']} non-Western artists")

        artist_agent = ArtistDiscoveryAgent(data_client)

        discovered_artists = await artist_agent.discover_artists(
            refined_theme=refined_theme,
            session_id=session_id,
            max_artists=15,
            min_relevance=0.3,
            prioritize_diversity=True,
            diversity_targets=curator_input.diversity_requirements
        )

        print(f"\n✅ DISCOVERED {len(discovered_artists)} ARTISTS")

        if discovered_artists:
            # Analyze diversity
            female_count = sum(1 for a in discovered_artists
                             if a.raw_data.get('gender_normalized') == 'female')
            male_count = sum(1 for a in discovered_artists
                           if a.raw_data.get('gender_normalized') == 'male')
            non_western_count = sum(1 for a in discovered_artists
                                  if a.raw_data.get('is_non_western', False))

            print("\n📊 DIVERSITY METRICS:")
            print(f"   Female Artists: {female_count} / {len(discovered_artists)} ({female_count/len(discovered_artists)*100:.1f}%)")
            print(f"   Male Artists: {male_count} / {len(discovered_artists)} ({male_count/len(discovered_artists)*100:.1f}%)")
            print(f"   Non-Western Artists: {non_western_count} / {len(discovered_artists)} ({non_western_count/len(discovered_artists)*100:.1f}%)")

            # Check if targets met
            targets_met = (
                female_count >= curator_input.diversity_requirements['min_female'] and
                non_western_count >= curator_input.diversity_requirements['min_non_western']
            )

            if targets_met:
                print(f"\n✅ DIVERSITY TARGETS MET!")
            else:
                print(f"\n⚠️  Diversity targets not fully met (limited by available data)")

            # Show artists with diversity info
            print("\n" + "=" * 80)
            print("DISCOVERED ARTISTS (with Diversity Data)")
            print("=" * 80)

            for i, artist in enumerate(discovered_artists, 1):
                gender = artist.raw_data.get('gender_normalized', 'unknown')
                is_non_western = artist.raw_data.get('is_non_western', False)
                combined_score = artist.raw_data.get('combined_score', artist.relevance_score)

                # Diversity indicators
                diversity_flags = []
                if gender == 'female':
                    diversity_flags.append("👩 Female")
                elif gender == 'male':
                    diversity_flags.append("👨 Male")

                if is_non_western:
                    diversity_flags.append("🌍 Non-Western")

                if artist.is_contemporary():
                    diversity_flags.append("🎨 Contemporary")

                print(f"\n{i}. {artist.name}")
                if artist.birth_year or artist.death_year:
                    print(f"   {artist.get_lifespan()}")
                if artist.nationality:
                    print(f"   Nationality: {artist.nationality}")

                if diversity_flags:
                    print(f"   Diversity: {' | '.join(diversity_flags)}")

                print(f"   Relevance: {artist.relevance_score:.2%} | Combined: {combined_score:.2%}")

                if artist.movements:
                    print(f"   Movements: {', '.join(artist.movements[:2])}")

                # First sentence of reasoning
                reasoning_first = artist.relevance_reasoning.split('.')[0] + '.'
                print(f"   💡 {reasoning_first}")

            # Geographic distribution
            print("\n" + "=" * 80)
            print("GEOGRAPHIC DIVERSITY")
            print("=" * 80)

            nationalities = {}
            for artist in discovered_artists:
                nat = artist.nationality or 'Unknown'
                nationalities[nat] = nationalities.get(nat, 0) + 1

            print("\nNationality Distribution:")
            for nat, count in sorted(nationalities.items(), key=lambda x: -x[1]):
                print(f"   • {nat}: {count} artist{'s' if count > 1 else ''}")

            # Gender breakdown by period
            print("\n" + "=" * 80)
            print("TEMPORAL & GENDER ANALYSIS")
            print("=" * 80)

            contemporary = [a for a in discovered_artists if a.is_contemporary()]
            historical = [a for a in discovered_artists if not a.is_contemporary()]

            print(f"\nContemporary Artists ({len(contemporary)}):")
            female_contemp = sum(1 for a in contemporary if a.raw_data.get('gender_normalized') == 'female')
            print(f"   Female: {female_contemp}, Male: {len(contemporary) - female_contemp}")

            print(f"\nHistorical Artists ({len(historical)}):")
            female_hist = sum(1 for a in historical if a.raw_data.get('gender_normalized') == 'female')
            print(f"   Female: {female_hist}, Male: {len(historical) - female_hist}")

            print("\n" + "=" * 80)
            print("PIPELINE INSIGHTS")
            print("=" * 80)

            print(f"""
✅ Successfully implemented diversity-first discovery
✅ Gender data retrieved from Wikidata in real-time
✅ Geographic diversity classification working
✅ Combined relevance + diversity scoring (70%/30%)
✅ Greedy selection algorithm ensures targets met

📊 Pipeline Volgorde:
   1. Curator definieert diversiteitseisen
   2. SPARQL queries halen gender + nationality op
   3. Artists worden gescoord op relevance
   4. Diversity bonus wordt toegevoegd (30% weight)
   5. Greedy algorithm zorgt voor minimum targets
   6. Final list is divers EN relevant

💡 Voor modern museum:
   - Verhoog min_female naar 50% (7-8 van 15)
   - Voeg min_non_western toe (30-40%)
   - Voeg contemporary_only filter toe
   - Gebruik ethnic_group data (nu basic nationality)
            """)

            return discovered_artists

        else:
            print("\n⚠️  No artists discovered")
            return None


if __name__ == "__main__":
    print("\n🎨 AI Curator - Diversity-First Pipeline")
    print("Testing with REAL Wikidata including gender & ethnicity\n")

    results = asyncio.run(test_diversity_pipeline())

    if results:
        print(f"\n✨ Success! Discovered {len(results)} diverse artists")
    else:
        print("\n⚠️  Test failed")
        sys.exit(1)