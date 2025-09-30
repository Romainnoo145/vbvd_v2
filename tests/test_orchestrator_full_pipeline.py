"""
Test Orchestrator Agent with Complete Pipeline
Real exhibition brief: "Modern Art Based on Time"
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
import json

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


async def test_orchestrated_pipeline():
    """
    Test the full orchestrated pipeline with a real curator brief
    Target: 15 artists, 50 artworks
    """
    logger.info("=" * 100)
    logger.info("ORCHESTRATED PIPELINE TEST: Modern Art Based on Time")
    logger.info("=" * 100)

    async with EssentialDataClient() as client:
        # Real curator brief - focused on concrete movements
        brief = CuratorBrief(
            theme_title="Time in Modern Art",
            theme_description=(
                "This exhibition explores how 20th and 21st century artists have represented "
                "and manipulated time through various media. From the fragmented simultaneity "
                "of Cubist paintings to the durational aspect of video installations, from "
                "Impressionist attempts to capture fleeting moments to contemporary conceptual "
                "works exploring memory and temporal perception. The exhibition traces how "
                "modernist and contemporary artists have made time itself a subject and medium "
                "of artistic investigation."
            ),
            theme_concepts=[
                "impressionism",
                "cubism",
                "abstract expressionism",
                "pop art",
                "conceptual art"
            ],
            reference_artists=[
                # Start with 2-3 known artists to seed the discovery
                "Claude Monet",
                "Pablo Picasso"
            ],
            target_audience="general",
            space_type="main",
            duration_weeks=16,
            include_international=True
        )

        session_id = f"orchestrated-{datetime.utcnow().timestamp()}"

        # Create orchestrator with progress callback
        orchestrator = OrchestratorAgent(
            data_client=client,
            progress_callback=progress_callback
        )

        # Configure pipeline for quality output
        config = {
            'max_artists': 15,
            'max_artworks': 50,
            'artworks_per_artist': 4,  # Balanced distribution
            'min_artist_relevance': 0.55,  # Higher threshold for quality
            'min_artwork_relevance': 0.45,  # Slightly lower to get volume
            'prioritize_diversity': True,
            'diversity_targets': {
                'min_female': 5,
                'min_non_western': 3
            }
        }

        logger.info("\nPipeline Configuration:")
        logger.info(json.dumps(config, indent=2))

        # Execute pipeline
        logger.info("\nStarting pipeline execution...\n")
        proposal = await orchestrator.execute_pipeline(brief, session_id, config)

        # Display results
        logger.info("\n" + "=" * 100)
        logger.info("EXHIBITION PROPOSAL")
        logger.info("=" * 100)

        logger.info(f"\nTitle: {proposal.exhibition_title}")
        if proposal.subtitle:
            logger.info(f"Subtitle: {proposal.subtitle}")

        logger.info(f"\n{'-' * 100}")
        logger.info("CURATORIAL STATEMENT")
        logger.info("-" * 100)
        logger.info(f"\n{proposal.curatorial_statement}\n")

        logger.info(f"{'-' * 100}")
        logger.info("CONTENT SUMMARY")
        logger.info("-" * 100)
        logger.info(f"Artists: {len(proposal.selected_artists)}")
        logger.info(f"Artworks: {len(proposal.selected_artworks)}")
        logger.info(f"Target Audience: {proposal.target_audience}")
        logger.info(f"Duration: {proposal.estimated_duration}")

        logger.info(f"\n{'-' * 100}")
        logger.info("QUALITY METRICS")
        logger.info("-" * 100)
        logger.info(f"Overall Quality Score: {proposal.overall_quality_score:.2f}")
        logger.info(f"Theme Confidence: {proposal.content_metrics['theme_confidence']:.2f}")
        logger.info(f"Avg Artist Relevance: {proposal.content_metrics['avg_artist_relevance']:.2f}")
        logger.info(f"Avg Artwork Relevance: {proposal.content_metrics['avg_artwork_relevance']:.2f}")
        logger.info(f"Avg Metadata Completeness: {proposal.content_metrics['avg_completeness']:.2f}")

        logger.info(f"\n{'-' * 100}")
        logger.info("ARTISTS ({})".format(len(proposal.selected_artists)))
        logger.info("-" * 100)

        for i, artist in enumerate(proposal.selected_artists[:10], 1):  # Show first 10
            logger.info(f"\n{i}. {artist.name} ({artist.get_lifespan() or 'dates unknown'})")
            logger.info(f"   Nationality: {artist.nationality or 'Unknown'}")
            if artist.movements:
                logger.info(f"   Movements: {', '.join(artist.movements[:3])}")
            logger.info(f"   Relevance: {artist.relevance_score:.2f}")
            logger.info(f"   Known Works: {artist.known_works_count or 'Unknown'}")

        if len(proposal.selected_artists) > 10:
            logger.info(f"\n... and {len(proposal.selected_artists) - 10} more artists")

        logger.info(f"\n{'-' * 100}")
        logger.info("ARTWORKS ({})".format(len(proposal.selected_artworks)))
        logger.info("-" * 100)

        # Group by artist
        by_artist = {}
        for artwork in proposal.selected_artworks:
            artist = artwork.artist_name or 'Unknown'
            if artist not in by_artist:
                by_artist[artist] = []
            by_artist[artist].append(artwork)

        # Show sample from each artist
        for artist_name in list(by_artist.keys())[:10]:  # First 10 artists
            artworks = by_artist[artist_name]
            logger.info(f"\n{artist_name} ({len(artworks)} works):")

            for artwork in artworks[:2]:  # Show 2 per artist
                logger.info(f"  • {artwork.get_display_title()}")
                logger.info(f"    Date: {artwork.get_date_display()}, Relevance: {artwork.relevance_score:.2f}")
                if artwork.institution_name:
                    logger.info(f"    Collection: {artwork.institution_name}")

        if len(by_artist) > 10:
            logger.info(f"\n... and {len(by_artist) - 10} more artists with artworks")

        logger.info(f"\n{'-' * 100}")
        logger.info("DIGITAL ASSETS")
        logger.info("-" * 100)
        logger.info(f"With IIIF Manifests: {proposal.content_metrics['with_iiif']}")
        logger.info(f"With Images: {proposal.content_metrics['with_images']}")
        logger.info(f"With Dimensions: {proposal.content_metrics['with_dimensions']}")

        logger.info(f"\n{'-' * 100}")
        logger.info("LOAN REQUIREMENTS")
        logger.info("-" * 100)
        for req in proposal.loan_requirements[:5]:
            logger.info(f"• {req}")

        logger.info(f"\n{'-' * 100}")
        logger.info("FEASIBILITY ASSESSMENT")
        logger.info("-" * 100)
        logger.info(f"{proposal.feasibility_notes}")

        logger.info(f"\n{'-' * 100}")
        logger.info("PROCESSING METRICS")
        logger.info("-" * 100)
        logger.info(f"Processing Time: {proposal.processing_time_seconds:.2f}s")
        logger.info(f"Session ID: {proposal.session_id}")

        logger.info("\n" + "=" * 100)
        logger.info("✓ ORCHESTRATED PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 100)

        # Return proposal for further inspection
        return proposal


async def main():
    """Run the orchestrated pipeline test"""
    try:
        proposal = await test_orchestrated_pipeline()

        # Additional validation
        logger.info("\n" + "=" * 100)
        logger.info("VALIDATION CHECKS")
        logger.info("=" * 100)

        checks_passed = 0
        total_checks = 0

        # Check 1: Minimum artists
        total_checks += 1
        if len(proposal.selected_artists) >= 10:
            logger.info("✓ Check 1: Minimum 10 artists found")
            checks_passed += 1
        else:
            logger.warning(f"✗ Check 1: Only {len(proposal.selected_artists)} artists (target: 10+)")

        # Check 2: Minimum artworks
        total_checks += 1
        if len(proposal.selected_artworks) >= 30:
            logger.info("✓ Check 2: Minimum 30 artworks found")
            checks_passed += 1
        else:
            logger.warning(f"✗ Check 2: Only {len(proposal.selected_artworks)} artworks (target: 30+)")

        # Check 3: Quality scores
        total_checks += 1
        if proposal.overall_quality_score >= 0.5:
            logger.info(f"✓ Check 3: Quality score acceptable ({proposal.overall_quality_score:.2f})")
            checks_passed += 1
        else:
            logger.warning(f"✗ Check 3: Quality score low ({proposal.overall_quality_score:.2f})")

        # Check 4: Metadata completeness
        total_checks += 1
        if proposal.content_metrics['avg_completeness'] >= 0.6:
            logger.info(f"✓ Check 4: Metadata completeness acceptable ({proposal.content_metrics['avg_completeness']:.2f})")
            checks_passed += 1
        else:
            logger.warning(f"✗ Check 4: Metadata completeness low ({proposal.content_metrics['avg_completeness']:.2f})")

        logger.info(f"\nValidation Result: {checks_passed}/{total_checks} checks passed")

        if checks_passed == total_checks:
            logger.info("✓ ALL VALIDATION CHECKS PASSED - READY FOR CLIENT PRESENTATION")
        elif checks_passed >= total_checks * 0.75:
            logger.info("⚠ MOST VALIDATION CHECKS PASSED - MINOR IMPROVEMENTS NEEDED")
        else:
            logger.warning("✗ VALIDATION FAILED - REQUIRES ATTENTION")

    except Exception as e:
        logger.error(f"Pipeline test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
