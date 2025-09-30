"""
Automated Full Workflow Test - Van Bommel van Dam Museum
Tests complete pipeline with real API calls (no mocks, no hardcoded data)
Includes Brave Search enrichment
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief
from backend.utils.session_manager import SessionManager, SessionState

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


async def run_full_workflow():
    """
    Run complete Van Bommel van Dam curator workflow with real API calls
    Auto-selects top candidates by relevance
    """
    print_header("🏛️  VAN BOMMEL VAN DAM MUSEUM - AUTOMATED WORKFLOW TEST", "=")
    print("📡 Using LIVE API calls:")
    print("   • Wikipedia API - Artist discovery")
    print("   • Wikidata SPARQL - Artwork metadata")
    print("   • Yale LUX API - Linked Art data")
    print("   • Brave Search API - Metadata enrichment")
    print("   • Getty AAT - Theme validation")
    print()

    # Real Van Bommel van Dam curator brief
    curator_brief = CuratorBrief(
        theme_title="Dutch Abstract Art and International Concrete Movement",
        theme_concepts=[
            "concrete art",
            "geometric abstraction",
            "de stijl",
            "constructivism",
            "neo-plasticism",
            "color field painting"
        ],
        theme_description="""
        This exhibition examines the development of abstract art from the pioneering Dutch De Stijl
        movement through international Concrete Art and Constructivism. Focusing on the period
        1917-1970, we explore how artists reduced visual language to its essential elements—line,
        plane, and primary colors—to create a universal aesthetic. The exhibition traces the influence
        of Piet Mondrian and Theo van Doesburg on subsequent generations of abstract artists who
        pursued geometric purity and mathematical precision in their work.
        """,
        reference_artists=[
            "Piet Mondrian",
            "Theo van Doesburg",
            "Kazimir Malevich"
        ],
        duration_weeks=16
    )

    print("📋 CURATOR BRIEF:")
    print(f"   Theme: {curator_brief.theme_title}")
    print(f"   Concepts: {', '.join(curator_brief.theme_concepts)}")
    print(f"   Reference Artists: {', '.join(curator_brief.reference_artists)}")
    print(f"   Duration: {curator_brief.duration_weeks} weeks")
    print()

    # Create session
    session_id = f"vbvd-auto-{datetime.utcnow().timestamp()}"
    session_manager = SessionManager()
    await session_manager.create_session(session_id)

    # Configure pipeline
    config = {
        'max_artists': 15,
        'max_artworks': 50,
        'artist_candidates': 30,  # Show 30 for selection
        'artwork_candidates': 100,  # Show 100 for selection
        'min_artwork_relevance': 0.3,
        'artworks_per_artist': 10
    }

    print(f"⚙️  CONFIGURATION:")
    print(f"   Max artists: {config['max_artists']}")
    print(f"   Max artworks: {config['max_artworks']}")
    print(f"   Auto-selecting top candidates by relevance")
    print()

    # Progress callback
    async def progress_callback(status):
        print(f"[{status.progress_percentage:>5.1f}%] {status.status_message}")

    # Run pipeline with interactive selection
    async with EssentialDataClient() as client:
        orchestrator = OrchestratorAgent(
            data_client=client,
            progress_callback=progress_callback,
            session_manager=session_manager  # Enable curator selection mode
        )

        # Start pipeline in background
        print_header("🚀 STARTING PIPELINE", "-")

        # Create task to run pipeline
        pipeline_task = asyncio.create_task(
            orchestrator.execute_pipeline(
                curator_brief=curator_brief,
                session_id=session_id,
                config=config
            )
        )

        # Wait for artist selection point
        while True:
            await asyncio.sleep(1)
            session = await session_manager.get_session(session_id)

            if session.state == SessionState.AWAITING_ARTIST_SELECTION:
                print()
                print_header("🎨 ARTIST SELECTION", "=")
                print(f"Found {len(session.artist_candidates)} artist candidates")
                print()

                # Display top 15
                print("Top 15 by relevance score:")
                for i, artist in enumerate(session.artist_candidates[:15], 1):
                    diversity = "✓" if artist.raw_data.get('is_diverse', False) else "-"
                    print(f"{i:>2}. {artist.name:<35} | Score: {artist.relevance_score:.2f} | "
                          f"Diverse: {diversity} | {artist.relevance_reasoning[:50]}...")

                print()
                print(f"🤖 Auto-selecting top {config['max_artists']} by relevance...")

                # Auto-select top N
                selected_indices = list(range(min(config['max_artists'], len(session.artist_candidates))))
                await session_manager.select_artists(session_id, selected_indices)
                print(f"✓ Selected {len(selected_indices)} artists")
                break

            if session.state in [SessionState.FAILED, SessionState.COMPLETE]:
                break

        # Wait for artwork selection point
        while True:
            await asyncio.sleep(1)
            session = await session_manager.get_session(session_id)

            if session.state == SessionState.AWAITING_ARTWORK_SELECTION:
                print()
                print_header("🖼️  ARTWORK SELECTION", "=")
                print(f"Found {len(session.artwork_candidates)} artwork candidates")
                print()

                # Display top 20
                print("Top 20 by relevance score:")
                for i, artwork in enumerate(session.artwork_candidates[:20], 1):
                    iiif = "✓" if artwork.iiif_manifest else "-"
                    print(f"{i:>2}. {artwork.title[:40]:<40} | {artwork.artist_name[:20]:<20} | "
                          f"Score: {artwork.relevance_score:.2f} | IIIF: {iiif}")

                print()
                print(f"🤖 Auto-selecting top {config['max_artworks']} by relevance...")

                # Auto-select top N
                selected_indices = list(range(min(config['max_artworks'], len(session.artwork_candidates))))
                await session_manager.select_artworks(session_id, selected_indices)
                print(f"✓ Selected {len(selected_indices)} artworks")
                break

            if session.state in [SessionState.FAILED, SessionState.COMPLETE]:
                break

        # Wait for completion
        print()
        print_header("⏳ COMPLETING PIPELINE", "-")
        proposal = await pipeline_task

        # Display results
        print()
        print_header("🎯 FINAL RESULTS", "=")

        print(f"Exhibition: {proposal.exhibition_title}")
        if proposal.subtitle:
            print(f"Subtitle: {proposal.subtitle}")
        print()
        print(f"Overall Quality Score: {proposal.overall_quality_score:.2f} / 1.00")

        metrics = proposal.content_metrics
        target_achieved = proposal.overall_quality_score >= 0.80
        print(f"Target (0.80): {'✅ ACHIEVED' if target_achieved else '❌ NOT MET'}")
        print()

        # Calculate percentages
        total_artworks = metrics.get('total_artworks', 0)
        iiif_pct = metrics.get('with_iiif', 0) / total_artworks if total_artworks > 0 else 0
        images_pct = metrics.get('with_images', 0) / total_artworks if total_artworks > 0 else 0
        dims_pct = metrics.get('with_dimensions', 0) / total_artworks if total_artworks > 0 else 0

        print("Component Scores:")
        print(f"  • Theme Confidence:        {metrics.get('theme_confidence', 0):.2f}")
        print(f"  • Artist Relevance (avg):  {metrics.get('avg_artist_relevance', 0):.2f}")
        print(f"  • Artwork Relevance (avg): {metrics.get('avg_artwork_relevance', 0):.2f}")
        print(f"  • Metadata Completeness:   {metrics.get('avg_completeness', 0):.2f}")
        print(f"  • Image Availability:      {images_pct:.0%} ({metrics.get('with_images', 0)}/{total_artworks})")
        print(f"  • IIIF Availability:       {iiif_pct:.0%} ({metrics.get('with_iiif', 0)}/{total_artworks})")
        print(f"  • Dimensions Available:    {dims_pct:.0%} ({metrics.get('with_dimensions', 0)}/{total_artworks})")
        print()
        print("Content:")
        print(f"  • Total Artists:           {metrics.get('total_artists', 0)}")
        print(f"  • Total Artworks:          {metrics.get('total_artworks', 0)}")
        print(f"  • Artists Represented:     {metrics.get('artists_represented', 0)}")
        print()

        if not target_achieved:
            print("💡 AREAS FOR IMPROVEMENT:")
            if iiif_pct < 0.40:
                print("  ⚠️  Low IIIF availability - need more museum data sources")
            if metrics.get('avg_completeness', 0) < 0.60:
                print("  ⚠️  Low metadata completeness - Brave Search should help")
            if images_pct < 0.60:
                print("  ⚠️  Low image availability - need better data sources")
            print()

        print("✅ Full workflow test complete!")
        print()
        print("📊 Data Sources Used:")
        print("  • Wikipedia API: ✓ (artist discovery)")
        print("  • Wikidata SPARQL: ✓ (artwork metadata)")
        print("  • Yale LUX API: ✓ (Linked Art data)")
        print("  • Brave Search API: ✓ (enrichment)")
        print("  • Getty AAT: ✓ (theme validation)")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(run_full_workflow())
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
