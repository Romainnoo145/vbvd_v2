"""
Test Artwork Discovery Agent (Stage 3)
Tests the full artwork discovery pipeline with real Yale LUX and Wikidata data
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.artwork_discovery_agent import ArtworkDiscoveryAgent
from backend.agents.artist_discovery_agent import ArtistDiscoveryAgent
from backend.agents.theme_refinement_agent import ThemeRefinementAgent
from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_artwork_discovery_full_pipeline():
    """
    Test the full 3-stage pipeline: Theme → Artists → Artworks
    """
    logger.info("=" * 80)
    logger.info("Testing Full 3-Stage Pipeline: Theme → Artists → Artworks")
    logger.info("=" * 80)

    async with EssentialDataClient() as client:
        # Create test curator brief
        brief = CuratorBrief(
            theme_title="Dutch Golden Age Painting",
            theme_description="An exploration of 17th century Dutch painting focusing on genre scenes, portraits, and still life",
            theme_concepts=["dutch golden age", "genre painting", "still life", "portrait"],
            reference_artists=["Rembrandt", "Vermeer"],
            target_audience="general",
            space_type="main",
            duration_weeks=12,
            include_international=False
        )

        session_id = f"test-{datetime.utcnow().timestamp()}"

        # STAGE 1: Theme Refinement
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 1: Theme Refinement")
        logger.info("=" * 60)

        theme_agent = ThemeRefinementAgent(client)
        refined_theme = await theme_agent.refine_theme(brief, session_id)

        logger.info(f"\n✓ Exhibition Title: {refined_theme.exhibition_title}")
        if refined_theme.subtitle:
            logger.info(f"  Subtitle: {refined_theme.subtitle}")
        logger.info(f"\n✓ Validated Concepts: {len(refined_theme.validated_concepts)}")
        for concept in refined_theme.validated_concepts[:3]:
            logger.info(f"  - {concept.refined_concept} (confidence: {concept.confidence_score:.2f})")

        # STAGE 2: Artist Discovery
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 2: Artist Discovery")
        logger.info("=" * 60)

        artist_agent = ArtistDiscoveryAgent(client)
        discovered_artists = await artist_agent.discover_artists(
            refined_theme=refined_theme,
            session_id=session_id,
            max_artists=5,  # Limit for testing
            min_relevance=0.5
        )

        logger.info(f"\n✓ Discovered Artists: {len(discovered_artists)}")
        for i, artist in enumerate(discovered_artists[:5], 1):
            logger.info(
                f"\n{i}. {artist.name} ({artist.get_lifespan() or 'dates unknown'})"
            )
            logger.info(f"   Relevance: {artist.relevance_score:.2f}")
            logger.info(f"   Movements: {', '.join(artist.movements[:3]) if artist.movements else 'None'}")
            logger.info(f"   Known Works: {artist.known_works_count or 'Unknown'}")
            logger.info(f"   Reasoning: {artist.relevance_reasoning[:150]}...")

        # STAGE 3: Artwork Discovery
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 3: Artwork Discovery")
        logger.info("=" * 60)

        artwork_agent = ArtworkDiscoveryAgent(client)
        discovered_artworks = await artwork_agent.discover_artworks(
            refined_theme=refined_theme,
            selected_artists=discovered_artists,
            session_id=session_id,
            max_artworks=20,  # Limit for testing
            min_relevance=0.4,
            artworks_per_artist=5
        )

        logger.info(f"\n✓ Discovered Artworks: {len(discovered_artworks)}")

        # Group by artist
        by_artist = {}
        for artwork in discovered_artworks:
            artist = artwork.artist_name or 'Unknown'
            if artist not in by_artist:
                by_artist[artist] = []
            by_artist[artist].append(artwork)

        # Display artworks by artist
        for artist_name, artworks in by_artist.items():
            logger.info(f"\n--- {artist_name} ({len(artworks)} works) ---")

            for i, artwork in enumerate(artworks[:3], 1):  # Show top 3 per artist
                logger.info(f"\n  {i}. {artwork.get_display_title()}")
                logger.info(f"     Date: {artwork.get_date_display()}")
                logger.info(f"     Medium: {artwork.medium or 'Unknown'}")

                if artwork.height_cm and artwork.width_cm:
                    logger.info(f"     Dimensions: {artwork.height_cm:.1f} x {artwork.width_cm:.1f} cm")

                logger.info(f"     Collection: {artwork.institution_name or 'Unknown'}")
                logger.info(f"     Relevance: {artwork.relevance_score:.2f}")
                logger.info(f"     Completeness: {artwork.completeness_score:.2f}")

                if artwork.subjects:
                    logger.info(f"     Subjects: {', '.join(artwork.subjects[:3])}")

                if artwork.iiif_manifest:
                    logger.info(f"     ✓ IIIF manifest available")

                logger.info(f"     Reasoning: {artwork.relevance_reasoning[:200]}...")

                if artwork.theme_connections:
                    logger.info(f"     Theme connections:")
                    for conn in artwork.theme_connections[:2]:
                        logger.info(f"       • {conn}")

        # Summary statistics
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY STATISTICS")
        logger.info("=" * 60)

        avg_relevance = sum(a.relevance_score for a in discovered_artworks) / len(discovered_artworks) if discovered_artworks else 0
        avg_completeness = sum(a.completeness_score for a in discovered_artworks) / len(discovered_artworks) if discovered_artworks else 0

        with_iiif = sum(1 for a in discovered_artworks if a.iiif_manifest)
        with_images = sum(1 for a in discovered_artworks if a.thumbnail_url or a.high_res_images)
        with_dimensions = sum(1 for a in discovered_artworks if a.height_cm and a.width_cm)

        logger.info(f"\nTotal Artworks: {len(discovered_artworks)}")
        logger.info(f"Artists Represented: {len(by_artist)}")
        logger.info(f"Average Relevance Score: {avg_relevance:.2f}")
        logger.info(f"Average Completeness: {avg_completeness:.2f}")
        logger.info(f"With IIIF Manifests: {with_iiif} ({with_iiif/len(discovered_artworks)*100:.1f}%)")
        logger.info(f"With Images: {with_images} ({with_images/len(discovered_artworks)*100:.1f}%)")
        logger.info(f"With Dimensions: {with_dimensions} ({with_dimensions/len(discovered_artworks)*100:.1f}%)")

        # Data sources
        source_counts = {}
        for artwork in discovered_artworks:
            for source in artwork.all_sources:
                source_counts[source] = source_counts.get(source, 0) + 1

        logger.info(f"\nData Sources:")
        for source, count in source_counts.items():
            logger.info(f"  - {source}: {count} artworks")

        logger.info("\n" + "=" * 60)
        logger.info("✓ Full pipeline test completed successfully!")
        logger.info("=" * 60)

        return refined_theme, discovered_artists, discovered_artworks


async def test_artwork_discovery_impressionism():
    """
    Test artwork discovery with Impressionism theme
    """
    logger.info("=" * 80)
    logger.info("Testing Artwork Discovery: Impressionism")
    logger.info("=" * 80)

    async with EssentialDataClient() as client:
        brief = CuratorBrief(
            theme_title="Impressionism and Light",
            theme_description="Exploring how Impressionist painters captured light and atmosphere in their works",
            theme_concepts=["impressionism", "landscape painting", "light"],
            reference_artists=["Claude Monet", "Pierre-Auguste Renoir"],
            target_audience="general",
            space_type="main",
            duration_weeks=16
        )

        session_id = f"test-impressionism-{datetime.utcnow().timestamp()}"

        # Run stages
        theme_agent = ThemeRefinementAgent(client)
        refined_theme = await theme_agent.refine_theme(brief, session_id)

        artist_agent = ArtistDiscoveryAgent(client)
        artists = await artist_agent.discover_artists(
            refined_theme=refined_theme,
            session_id=session_id,
            max_artists=3,
            min_relevance=0.6
        )

        artwork_agent = ArtworkDiscoveryAgent(client)
        artworks = await artwork_agent.discover_artworks(
            refined_theme=refined_theme,
            selected_artists=artists,
            session_id=session_id,
            max_artworks=15,
            min_relevance=0.5
        )

        logger.info(f"\n✓ Theme: {refined_theme.exhibition_title}")
        logger.info(f"✓ Artists: {len(artists)}")
        logger.info(f"✓ Artworks: {len(artworks)}")

        # Show top 5 artworks
        logger.info("\nTop 5 Artworks:")
        for i, artwork in enumerate(artworks[:5], 1):
            logger.info(f"\n{i}. {artwork.get_display_title()}")
            logger.info(f"   Artist: {artwork.get_creator_display()}")
            logger.info(f"   Date: {artwork.get_date_display()}")
            logger.info(f"   Relevance: {artwork.relevance_score:.2f}")
            logger.info(f"   Collection: {artwork.institution_name or 'Unknown'}")

        logger.info("\n✓ Impressionism test completed!")


async def test_artwork_metadata_enrichment():
    """
    Test metadata enrichment and completeness scoring
    """
    logger.info("=" * 80)
    logger.info("Testing Artwork Metadata Enrichment")
    logger.info("=" * 80)

    async with EssentialDataClient() as client:
        # Use a well-documented artist for better metadata
        brief = CuratorBrief(
            theme_title="Rembrandt's Legacy",
            theme_description="Exploring Rembrandt's mastery of light and shadow",
            theme_concepts=["baroque", "dutch golden age", "portrait"],
            reference_artists=["Rembrandt"],
            target_audience="scholarly"
        )

        session_id = f"test-metadata-{datetime.utcnow().timestamp()}"

        theme_agent = ThemeRefinementAgent(client)
        refined_theme = await theme_agent.refine_theme(brief, session_id)

        artist_agent = ArtistDiscoveryAgent(client)
        artists = await artist_agent.discover_artists(
            refined_theme=refined_theme,
            session_id=session_id,
            max_artists=1,  # Just Rembrandt
            min_relevance=0.5
        )

        if artists:
            artwork_agent = ArtworkDiscoveryAgent(client)
            artworks = await artwork_agent.discover_artworks(
                refined_theme=refined_theme,
                selected_artists=artists[:1],
                session_id=session_id,
                max_artworks=10,
                min_relevance=0.3
            )

            logger.info(f"\nFound {len(artworks)} Rembrandt artworks")

            # Analyze metadata completeness
            logger.info("\nMetadata Completeness Analysis:")

            for artwork in artworks[:5]:
                logger.info(f"\n- {artwork.title}")
                logger.info(f"  Completeness Score: {artwork.completeness_score:.2f}")
                logger.info(f"  Has Title: {'✓' if artwork.title else '✗'}")
                logger.info(f"  Has Date: {'✓' if artwork.date_created else '✗'}")
                logger.info(f"  Has Medium: {'✓' if artwork.medium else '✗'}")
                logger.info(f"  Has Dimensions: {'✓' if artwork.height_cm else '✗'}")
                logger.info(f"  Has Description: {'✓' if artwork.description else '✗'}")
                logger.info(f"  Has IIIF: {'✓' if artwork.iiif_manifest else '✗'}")
                logger.info(f"  Has Subjects: {'✓' if artwork.subjects else '✗'}")
                logger.info(f"  Sources: {', '.join(artwork.all_sources)}")

            logger.info("\n✓ Metadata enrichment test completed!")
        else:
            logger.warning("No artists found for metadata test")


async def main():
    """Run all tests"""
    try:
        # Test 1: Full pipeline with Dutch Golden Age
        await test_artwork_discovery_full_pipeline()

        logger.info("\n\n")

        # Test 2: Impressionism
        await test_artwork_discovery_impressionism()

        logger.info("\n\n")

        # Test 3: Metadata enrichment
        await test_artwork_metadata_enrichment()

        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
