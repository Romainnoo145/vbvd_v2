"""
Real Curator Brief Test - Van Bommel van Dam Museum
Testing with authentic curatorial input as would be provided by VBvD curator
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.orchestrator_agent import OrchestratorAgent, PipelineStatus
from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def progress_callback(status: PipelineStatus):
    """Progress callback for real-time updates"""
    logger.info(
        f"[{status.progress_percentage:.0f}%] {status.current_stage.value}: {status.status_message}"
    )


async def test_vbvd_curator_brief():
    """
    Test with realistic Van Bommel van Dam curator brief
    Focus: Contemporary abstract and geometric art with emphasis on color and form
    """
    logger.info("=" * 100)
    logger.info("VAN BOMMEL VAN DAM MUSEUM - CURATOR BRIEF TEST")
    logger.info("=" * 100)

    async with EssentialDataClient() as client:
        # Realistic curator brief from Van Bommel van Dam perspective
        # VBvD focuses on contemporary abstract art, geometry, and color
        brief = CuratorBrief(
            theme_title="Color, Form, and Space in Contemporary Abstraction",
            theme_description=(
                "This exhibition explores the evolution of abstract art from mid-20th century "
                "geometric abstraction through contemporary color field painting and minimalism. "
                "Building on the legacy of artists like Mondrian and the De Stijl movement, we examine "
                "how contemporary artists continue to investigate the relationship between color, form, "
                "and spatial perception. The exhibition features works that demonstrate the ongoing "
                "relevance of pure abstraction, highlighting artists who push the boundaries of "
                "geometric composition, monochrome painting, and chromatic exploration. "
                "Special attention is given to European abstract traditions and their global influence."
            ),
            theme_concepts=[
                "geometric abstraction",
                "color field painting",
                "minimalism",
                "de stijl",
                "concrete art",
                "monochrome painting"
            ],
            reference_artists=[
                "Piet Mondrian",
                "Kazimir Malevich",
                "Josef Albers"
            ],
            target_audience="general",
            space_type="main",
            duration_weeks=20,  # Major exhibition
            include_international=True
        )

        session_id = f"vbvd-{datetime.utcnow().timestamp()}"

        logger.info("\n" + "=" * 100)
        logger.info("CURATOR BRIEF DETAILS")
        logger.info("=" * 100)
        logger.info(f"\nTheme: {brief.theme_title}")
        logger.info(f"Duration: {brief.duration_weeks} weeks")
        logger.info(f"Concepts: {', '.join(brief.theme_concepts)}")
        logger.info(f"Reference Artists: {', '.join(brief.reference_artists)}")
        logger.info(f"\nDescription:\n{brief.theme_description}")

        # Create orchestrator
        orchestrator = OrchestratorAgent(
            data_client=client,
            progress_callback=progress_callback
        )

        # Configure for VBvD quality standards
        config = {
            'max_artists': 15,  # Focused selection
            'max_artworks': 50,  # Substantial exhibition
            'artworks_per_artist': 4,
            'min_artist_relevance': 0.6,  # High quality threshold
            'min_artwork_relevance': 0.5,
            'prioritize_diversity': True,
            'diversity_targets': {
                'min_female': 5,
                'min_non_western': 3
            }
        }

        logger.info("\n" + "=" * 100)
        logger.info("PIPELINE CONFIGURATION")
        logger.info("=" * 100)
        logger.info(json.dumps(config, indent=2))

        # Execute pipeline
        logger.info("\n" + "=" * 100)
        logger.info("STARTING PIPELINE EXECUTION")
        logger.info("=" * 100)
        logger.info("")

        start_time = datetime.utcnow()
        proposal = await orchestrator.execute_pipeline(brief, session_id, config)
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        # Display Exhibition Proposal
        logger.info("\n" + "=" * 100)
        logger.info("EXHIBITION PROPOSAL - VAN BOMMEL VAN DAM")
        logger.info("=" * 100)

        logger.info(f"\n{'─' * 100}")
        logger.info("EXHIBITION TITLE")
        logger.info("─" * 100)
        logger.info(f"\n{proposal.exhibition_title}")
        if proposal.subtitle:
            logger.info(f"{proposal.subtitle}")

        logger.info(f"\n{'─' * 100}")
        logger.info("CURATORIAL STATEMENT")
        logger.info("─" * 100)
        logger.info(f"\n{proposal.curatorial_statement}\n")

        logger.info(f"{'─' * 100}")
        logger.info("SCHOLARLY RATIONALE")
        logger.info("─" * 100)
        logger.info(f"\n{proposal.scholarly_rationale}\n")

        logger.info(f"{'─' * 100}")
        logger.info("EXHIBITION PARAMETERS")
        logger.info("─" * 100)
        logger.info(f"Target Audience: {proposal.target_audience}")
        logger.info(f"Complexity Level: {proposal.complexity_level}")
        logger.info(f"Duration: {proposal.estimated_duration}")
        logger.info(f"Space Recommendations: {', '.join(proposal.space_recommendations)}")

        logger.info(f"\n{'─' * 100}")
        logger.info("QUALITY METRICS")
        logger.info("─" * 100)
        logger.info(f"Overall Quality Score: {proposal.overall_quality_score:.2f}/1.00")
        logger.info(f"Theme Confidence: {proposal.content_metrics['theme_confidence']:.2f}")
        logger.info(f"Average Artist Relevance: {proposal.content_metrics['avg_artist_relevance']:.2f}")
        logger.info(f"Average Artwork Relevance: {proposal.content_metrics['avg_artwork_relevance']:.2f}")
        logger.info(f"Average Completeness: {proposal.content_metrics['avg_completeness']:.2f}")
        logger.info(f"Processing Time: {processing_time:.1f} seconds")

        logger.info(f"\n{'─' * 100}")
        logger.info(f"SELECTED ARTISTS ({len(proposal.selected_artists)})")
        logger.info("─" * 100)

        for i, artist in enumerate(proposal.selected_artists, 1):
            logger.info(f"\n{i}. {artist.name}")
            logger.info(f"   {artist.get_lifespan() or 'Contemporary'}")
            if artist.nationality:
                logger.info(f"   Nationality: {artist.nationality}")
            if artist.movements:
                logger.info(f"   Movements: {', '.join(artist.movements[:3])}")
            logger.info(f"   Relevance Score: {artist.relevance_score:.2f}")
            logger.info(f"   {artist.relevance_reasoning[:150]}...")

        # Diversity analysis
        female_count = sum(1 for a in proposal.selected_artists if a.raw_data.get('gender_normalized') == 'female')
        non_western_count = sum(1 for a in proposal.selected_artists if a.raw_data.get('is_non_western', False))
        contemporary_count = sum(1 for a in proposal.selected_artists if a.is_contemporary())

        logger.info(f"\n{'─' * 100}")
        logger.info("ARTIST DIVERSITY")
        logger.info("─" * 100)
        logger.info(f"Female Artists: {female_count} ({female_count/len(proposal.selected_artists)*100:.0f}%)")
        logger.info(f"Non-Western Artists: {non_western_count} ({non_western_count/len(proposal.selected_artists)*100:.0f}%)")
        logger.info(f"Contemporary Artists: {contemporary_count} ({contemporary_count/len(proposal.selected_artists)*100:.0f}%)")

        logger.info(f"\n{'─' * 100}")
        logger.info(f"SELECTED ARTWORKS ({len(proposal.selected_artworks)})")
        logger.info("─" * 100)

        # Group by artist
        by_artist = {}
        for artwork in proposal.selected_artworks:
            artist = artwork.artist_name or 'Unknown'
            if artist not in by_artist:
                by_artist[artist] = []
            by_artist[artist].append(artwork)

        for artist_name in sorted(by_artist.keys()):
            artworks = by_artist[artist_name]
            logger.info(f"\n{artist_name} ({len(artworks)} works)")
            logger.info("─" * 100)

            for artwork in artworks:
                logger.info(f"\n  • {artwork.get_display_title()}")
                logger.info(f"    Date: {artwork.get_date_display()}")
                if artwork.medium:
                    logger.info(f"    Medium: {artwork.medium}")
                if artwork.height_cm and artwork.width_cm:
                    logger.info(f"    Dimensions: {artwork.height_cm:.0f} × {artwork.width_cm:.0f} cm")
                if artwork.institution_name:
                    logger.info(f"    Collection: {artwork.institution_name}")
                logger.info(f"    Relevance: {artwork.relevance_score:.2f}")
                if artwork.iiif_manifest:
                    logger.info(f"    ✓ IIIF manifest available")

        logger.info(f"\n{'─' * 100}")
        logger.info("DIGITAL ASSETS & METADATA")
        logger.info("─" * 100)
        logger.info(f"With IIIF Manifests: {proposal.content_metrics['with_iiif']} ({proposal.content_metrics['with_iiif']/len(proposal.selected_artworks)*100:.0f}%)")
        logger.info(f"With Images: {proposal.content_metrics['with_images']} ({proposal.content_metrics['with_images']/len(proposal.selected_artworks)*100:.0f}%)")
        logger.info(f"With Dimensions: {proposal.content_metrics['with_dimensions']} ({proposal.content_metrics['with_dimensions']/len(proposal.selected_artworks)*100:.0f}%)")

        logger.info(f"\n{'─' * 100}")
        logger.info("LOAN REQUIREMENTS")
        logger.info("─" * 100)
        for req in proposal.loan_requirements[:8]:
            logger.info(f"• {req}")

        logger.info(f"\n{'─' * 100}")
        logger.info("FEASIBILITY ASSESSMENT")
        logger.info("─" * 100)
        logger.info(f"{proposal.feasibility_notes}")

        # Final validation
        logger.info("\n" + "=" * 100)
        logger.info("VALIDATION REPORT")
        logger.info("=" * 100)

        checks = []

        # Check 1: Artist count
        if len(proposal.selected_artists) >= 12:
            checks.append(("✓", f"Artists: {len(proposal.selected_artists)}/15 target"))
        else:
            checks.append(("⚠", f"Artists: {len(proposal.selected_artists)}/15 target (below minimum)"))

        # Check 2: Artwork count
        if len(proposal.selected_artworks) >= 40:
            checks.append(("✓", f"Artworks: {len(proposal.selected_artworks)}/50 target"))
        else:
            checks.append(("⚠", f"Artworks: {len(proposal.selected_artworks)}/50 target (below recommended)"))

        # Check 3: Quality score
        if proposal.overall_quality_score >= 0.55:
            checks.append(("✓", f"Quality: {proposal.overall_quality_score:.2f} (excellent)"))
        elif proposal.overall_quality_score >= 0.45:
            checks.append(("✓", f"Quality: {proposal.overall_quality_score:.2f} (good)"))
        else:
            checks.append(("⚠", f"Quality: {proposal.overall_quality_score:.2f} (needs improvement)"))

        # Check 4: Diversity
        diversity_ok = female_count >= 4 and non_western_count >= 2
        if diversity_ok:
            checks.append(("✓", f"Diversity: {female_count} female, {non_western_count} non-Western (good)"))
        else:
            checks.append(("⚠", f"Diversity: {female_count} female, {non_western_count} non-Western (improve)"))

        # Check 5: Metadata completeness
        if proposal.content_metrics['avg_completeness'] >= 0.65:
            checks.append(("✓", f"Metadata: {proposal.content_metrics['avg_completeness']:.2f} (comprehensive)"))
        else:
            checks.append(("⚠", f"Metadata: {proposal.content_metrics['avg_completeness']:.2f} (acceptable)"))

        logger.info("")
        for symbol, message in checks:
            logger.info(f"{symbol} {message}")

        passed = sum(1 for s, _ in checks if s == "✓")
        total = len(checks)

        logger.info(f"\nValidation Score: {passed}/{total} checks passed")

        if passed == total:
            logger.info("\n✓ EXHIBITION PROPOSAL APPROVED - READY FOR CLIENT PRESENTATION")
        elif passed >= total * 0.75:
            logger.info("\n✓ EXHIBITION PROPOSAL ACCEPTED - Minor refinements recommended")
        else:
            logger.info("\n⚠ EXHIBITION PROPOSAL REQUIRES ATTENTION - Review and adjust")

        logger.info("\n" + "=" * 100)
        logger.info("✓ VAN BOMMEL VAN DAM CURATOR TEST COMPLETED")
        logger.info("=" * 100)

        return proposal


async def main():
    """Run the VBvD curator test"""
    try:
        proposal = await test_vbvd_curator_brief()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
