"""
Interactive Curator CLI Test
Allows curator to review and select artists and artworks during the pipeline
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.orchestrator_agent import OrchestratorAgent, PipelineStatus
from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief, DiscoveredArtist, ArtworkCandidate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text: str, char: str = "="):
    """Print a formatted header"""
    print("\n")
    print(char * 100)
    print(text.center(100))
    print(char * 100)
    print()


def print_artists_table(artists: List[DiscoveredArtist]):
    """Display artists in a formatted table"""
    print_header("🎨 DISCOVERED ARTISTS", "=")

    print(f"{'#':>3} | {'Name':<30} | {'Years':^12} | {'Relevance':^10} | {'Diversity':^10} | {'Reasoning':<30}")
    print("-" * 115)

    for i, artist in enumerate(artists, 1):
        years = f"{artist.birth_year or '?'}-{artist.death_year or 'present'}"
        diversity_info = artist.raw_data.get('gender', 'unknown') if hasattr(artist, 'raw_data') else 'unknown'
        is_diverse = artist.raw_data.get('is_diverse', False) if hasattr(artist, 'raw_data') else False
        diversity_marker = "✓" if is_diverse else "-"

        # Truncate reasoning if too long
        reasoning = artist.relevance_reasoning[:30] + "..." if len(artist.relevance_reasoning) > 30 else artist.relevance_reasoning

        print(f"{i:>3} | {artist.name:<30} | {years:^12} | {artist.relevance_score:^10.2f} | {diversity_marker:^10} | {reasoning:<30}")

    print("-" * 115)
    print(f"Total: {len(artists)} artists")
    print()


def print_artworks_table(artworks: List[ArtworkCandidate], max_display: int = 50):
    """Display artworks in a formatted table"""
    print_header("🖼️  DISCOVERED ARTWORKS", "=")

    display_artworks = artworks[:max_display]

    print(f"{'#':>3} | {'Title':<35} | {'Artist':<20} | {'Date':^6} | {'Relevance':^10} | {'Complete':^9} | {'IIIF':^4}")
    print("-" * 115)

    for i, artwork in enumerate(display_artworks, 1):
        title = artwork.title[:35] if artwork.title else "Untitled"
        artist = artwork.artist_name[:20] if artwork.artist_name else "Unknown"
        date = str(artwork.date_created_earliest) if artwork.date_created_earliest else "?"
        iiif_marker = "✓" if artwork.iiif_manifest else "-"

        print(f"{i:>3} | {title:<35} | {artist:<20} | {date:^6} | {artwork.relevance_score:^10.2f} | {artwork.completeness_score:^9.2f} | {iiif_marker:^4}")

    print("-" * 115)
    if len(artworks) > max_display:
        print(f"Showing top {max_display} of {len(artworks)} total artworks")
    else:
        print(f"Total: {len(artworks)} artworks")
    print()


def get_curator_selection(items: List, item_type: str, max_select: int) -> List[int]:
    """
    Interactive curator selection

    Returns:
        List of selected indices (0-based)
    """
    print(f"\n📝 SELECT {item_type.upper()}")
    print(f"Please select up to {max_select} {item_type}.")
    print(f"Enter numbers separated by commas (e.g., 1,3,5,12) or 'auto' for automatic top {max_select}:")
    print()

    while True:
        try:
            selection = input(f"Your selection (1-{len(items)}): ").strip()

            if selection.lower() == 'auto':
                # Auto-select top N by relevance
                print(f"✓ Auto-selecting top {max_select} by relevance...")
                return list(range(min(max_select, len(items))))

            # Parse comma-separated numbers
            indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip()]

            # Validate
            if not indices:
                print("❌ No valid selections. Please try again.")
                continue

            if len(indices) > max_select:
                print(f"❌ Too many selections ({len(indices)}). Maximum is {max_select}. Please try again.")
                continue

            if any(i < 0 or i >= len(items) for i in indices):
                print(f"❌ Invalid index. Must be between 1 and {len(items)}. Please try again.")
                continue

            print(f"✓ Selected {len(indices)} {item_type}")
            return indices

        except ValueError:
            print("❌ Invalid input format. Use comma-separated numbers (e.g., 1,3,5) or 'auto'.")
        except KeyboardInterrupt:
            print("\n\n❌ Selection cancelled by user")
            sys.exit(1)


async def interactive_curator_workflow():
    """
    Run the full curator pipeline with interactive selection points
    """
    print_header("🏛️  VAN BOMMEL VAN DAM MUSEUM - INTERACTIVE CURATOR WORKFLOW", "=")

    # Define curator brief
    curator_brief = CuratorBrief(
        theme_title="Color, Form, and Space in Contemporary Abstraction",
        theme_concepts=["geometric abstraction", "color field painting", "minimalism",
                        "de stijl", "concrete art", "monochrome painting"],
        theme_description="""This exhibition explores the evolution of abstract art from mid-20th century geometric
abstraction through contemporary color field painting and minimalism. Building on the legacy of artists like
Mondrian and the De Stijl movement, we examine how contemporary artists continue to investigate the relationship
between color, form, and spatial perception.""",
        reference_artists=["Piet Mondrian", "Kazimir Malevich", "Josef Albers"],
        duration_weeks=20
    )

    print("📋 CURATOR BRIEF:")
    print(f"   Theme: {curator_brief.theme_title}")
    print(f"   Concepts: {', '.join(curator_brief.theme_concepts)}")
    print(f"   Reference Artists: {', '.join(curator_brief.reference_artists)}")
    print(f"   Duration: {curator_brief.duration_weeks} weeks")
    print()

    input("Press ENTER to start artist discovery...")

    # ===========================================
    # PHASE 1: ARTIST DISCOVERY
    # ===========================================

    print_header("PHASE 1: ARTIST DISCOVERY", "-")
    print("🔍 Discovering artists from Wikipedia and related sources...")
    print()

    session_id = f"interactive-{datetime.utcnow().timestamp()}"

    async with EssentialDataClient() as client:
        orchestrator = OrchestratorAgent(data_client=client)

        # Run artist discovery (get 30 candidates for curator to review)
        from backend.agents.artist_discovery_simple import SimpleArtistDiscovery
        from backend.agents.theme_refinement_agent import ThemeRefinementAgent

        # First refine theme
        theme_agent = ThemeRefinementAgent(client)
        refined_theme = await theme_agent.refine_theme(curator_brief, session_id)

        print(f"✓ Theme refined: {refined_theme.exhibition_title}")
        print(f"✓ Validated {len(refined_theme.validated_concepts)} concepts")
        print()

        # Discover artists
        simple_discoverer = SimpleArtistDiscovery(client)
        raw_artists = await simple_discoverer.discover_artists(
            refined_theme=refined_theme,
            reference_artists=curator_brief.reference_artists or [],
            max_artists=30  # Get 30 candidates for review
        )

        print(f"✓ Discovered {len(raw_artists)} artist candidates")

        # Convert to DiscoveredArtist objects with relevance scoring
        from backend.utils.relevance_scoring import score_artist_relevance

        discovered_artists = []
        # Extract concept names from validated concepts (could be Pydantic objects or dicts)
        theme_concepts = []
        for c in refined_theme.validated_concepts:
            if hasattr(c, 'concept'):
                # Pydantic ConceptValidation object
                theme_concepts.append(c.concept)
            elif isinstance(c, dict):
                theme_concepts.append(c.get('concept', c.get('name', '')))
            else:
                theme_concepts.append(str(c))

        for artist_data in raw_artists:
            relevance_score, relevance_reasoning = score_artist_relevance(
                artist_data=artist_data,
                theme_concepts=theme_concepts,
                reference_artists=curator_brief.reference_artists
            )

            discovered_artist = DiscoveredArtist(
                name=artist_data['name'],
                birth_year=artist_data.get('birth_year'),
                death_year=artist_data.get('death_year'),
                nationality=None,
                movements=[],
                biography=artist_data.get('description', ''),
                known_works_count=None,
                wikidata_id=artist_data.get('wikidata_id'),
                getty_ulan_id=None,
                source_endpoint='wikipedia',
                discovery_confidence=relevance_score,
                relevance_score=relevance_score,
                relevance_reasoning=relevance_reasoning,
                raw_data=artist_data
            )
            discovered_artists.append(discovered_artist)

        # Sort by relevance
        discovered_artists.sort(key=lambda a: a.relevance_score, reverse=True)

        # Display artists to curator
        print_artists_table(discovered_artists)

        # Curator selects artists
        selected_indices = get_curator_selection(discovered_artists, "artists", max_select=15)
        selected_artists = [discovered_artists[i] for i in selected_indices]

        print(f"\n✓ Proceeding with {len(selected_artists)} selected artists")

        # Calculate diversity metrics
        female_count = sum(1 for a in selected_artists
                          if a.raw_data.get('gender') == 'female')
        diverse_count = sum(1 for a in selected_artists
                           if a.raw_data.get('is_diverse', False))

        print(f"   - Female artists: {female_count}/{len(selected_artists)} ({female_count/len(selected_artists)*100:.0f}%)")
        print(f"   - Diverse artists: {diverse_count}/{len(selected_artists)} ({diverse_count/len(selected_artists)*100:.0f}%)")

        input("\nPress ENTER to start artwork discovery...")

        # ===========================================
        # PHASE 2: ARTWORK DISCOVERY
        # ===========================================

        print_header("PHASE 2: ARTWORK DISCOVERY", "-")
        print(f"🔍 Discovering artworks by {len(selected_artists)} selected artists...")
        print()

        # Run artwork discovery
        from backend.agents.artwork_discovery_agent import ArtworkDiscoveryAgent

        artwork_agent = ArtworkDiscoveryAgent(client)
        discovered_artworks = await artwork_agent.discover_artworks(
            refined_theme=refined_theme,
            selected_artists=selected_artists,
            session_id=session_id,
            max_artworks=100,  # Get 100 candidates for review
            min_relevance=0.3,  # Lower threshold to get more candidates
            artworks_per_artist=10
        )

        print(f"✓ Discovered {len(discovered_artworks)} artwork candidates")

        if not discovered_artworks:
            print("❌ No artworks found. This might be due to:")
            print("   - Strict completeness filtering")
            print("   - Limited data in Yale LUX/Wikidata for these artists")
            print("   - Need to add more data sources")
            return

        # Sort by relevance
        discovered_artworks.sort(key=lambda a: a.relevance_score, reverse=True)

        # Display artworks to curator
        print_artworks_table(discovered_artworks, max_display=50)

        # Curator selects artworks
        max_artworks = min(50, len(discovered_artworks))
        selected_artwork_indices = get_curator_selection(discovered_artworks, "artworks", max_select=max_artworks)
        selected_artworks = [discovered_artworks[i] for i in selected_artwork_indices]

        print(f"\n✓ Proceeding with {len(selected_artworks)} selected artworks")

        # Calculate metrics
        iiif_count = sum(1 for a in selected_artworks if a.iiif_manifest)
        avg_completeness = sum(a.completeness_score for a in selected_artworks) / len(selected_artworks)
        avg_relevance = sum(a.relevance_score for a in selected_artworks) / len(selected_artworks)

        print(f"   - Avg relevance: {avg_relevance:.2f}")
        print(f"   - Avg completeness: {avg_completeness:.2f}")
        print(f"   - IIIF manifests: {iiif_count}/{len(selected_artworks)} ({iiif_count/len(selected_artworks)*100:.0f}%)")

        # ===========================================
        # PHASE 3: QUALITY METRICS
        # ===========================================

        print_header("PHASE 3: EXHIBITION QUALITY METRICS", "-")

        from backend.utils.quality_metrics import calculate_quality_score

        quality_metrics = calculate_quality_score(
            theme=refined_theme,
            artists=selected_artists,
            artworks=selected_artworks
        )

        print_header("🎯 FINAL RESULTS", "=")
        print(f"Overall Quality Score: {quality_metrics.overall_quality_score:.2f} / 1.00")
        print(f"Target (0.80): {'✓ ACHIEVED' if quality_metrics.target_achieved else '✗ NOT MET'}")
        print()
        print("Component Scores:")
        print(f"  - Theme Confidence:        {quality_metrics.theme_confidence:.2f}")
        print(f"  - Artist Relevance:        {quality_metrics.artist_relevance_avg:.2f}")
        print(f"  - Artist Filtering:        {quality_metrics.artist_filtering_quality:.2f}")
        print(f"  - Artwork Relevance:       {quality_metrics.artwork_relevance_avg:.2f}")
        print(f"  - Metadata Completeness:   {quality_metrics.metadata_completeness_avg:.2f}")
        print(f"  - Image Availability:      {quality_metrics.image_availability_pct:.0%}")
        print(f"  - IIIF Availability:       {quality_metrics.iiif_availability_pct:.0%}")
        print(f"  - Diversity Representation:{quality_metrics.diversity_representation_pct:.0%}")
        print()
        print("Content:")
        print(f"  - Total Artists:           {quality_metrics.total_artists}")
        print(f"  - Total Artworks:          {quality_metrics.total_artworks}")
        print()

        if not quality_metrics.target_achieved:
            print("💡 SUGGESTIONS TO IMPROVE QUALITY:")
            if quality_metrics.iiif_availability_pct < 0.40:
                print("  - Add more museum data sources with IIIF support")
            if quality_metrics.metadata_completeness_avg < 0.60:
                print("  - Implement Brave Search enrichment to fill metadata gaps")
            if quality_metrics.diversity_representation_pct < 0.30:
                print("  - Select more diverse artists in Phase 1")

        print()
        print("✅ Interactive curator workflow complete!")


if __name__ == "__main__":
    try:
        asyncio.run(interactive_curator_workflow())
    except KeyboardInterrupt:
        print("\n\n❌ Workflow cancelled by user")
        sys.exit(1)
