"""
Full Pipeline Test: Modern Art Based on Time
Real curator brief without any mock data - testing complete 3-stage workflow
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


async def test_modern_art_time_theme():
    """
    Test the full 3-stage pipeline with "Modern Art Based on Time" theme
    Real curator brief, no mock data
    """
    logger.info("=" * 100)
    logger.info("FULL PIPELINE TEST: Modern Art Based on Time")
    logger.info("=" * 100)

    async with EssentialDataClient() as client:
        # REAL CURATOR BRIEF - No mock data
        brief = CuratorBrief(
            theme_title="Modern Art Based on Time",
            theme_description=(
                "An exploration of how modern and contemporary artists have conceptualized, "
                "represented, and challenged notions of time through their work. From capturing "
                "fleeting moments in Impressionism to exploring duration in performance art, memory "
                "in photography, and temporal perception in video art. This exhibition examines how "
                "20th and 21st century artists use time as both subject matter and artistic medium, "
                "including works that explore sequence, repetition, decay, and the passage of time."
            ),
            theme_concepts=[
                "impressionism",
                "cubism",
                "futurism",
                "video art",
                "performance art",
                "photography",
                "conceptual art"
            ],
            reference_artists=[
                # Leave empty - let the system discover artists organically
            ],
            target_audience="general",
            space_type="main",
            duration_weeks=16,
            include_international=True
        )

        session_id = f"modern-art-time-{datetime.utcnow().timestamp()}"

        # ============================================================
        # STAGE 1: THEME REFINEMENT
        # ============================================================
        logger.info("\n" + "=" * 100)
        logger.info("STAGE 1: THEME REFINEMENT")
        logger.info("=" * 100)

        theme_agent = ThemeRefinementAgent(client)
        refined_theme = await theme_agent.refine_theme(brief, session_id)

        logger.info(f"\n{'=' * 100}")
        logger.info("REFINED EXHIBITION THEME")
        logger.info("=" * 100)
        logger.info(f"\nTitle: {refined_theme.exhibition_title}")
        if refined_theme.subtitle:
            logger.info(f"Subtitle: {refined_theme.subtitle}")

        logger.info(f"\n{'─' * 100}")
        logger.info("CURATORIAL STATEMENT")
        logger.info("─" * 100)
        logger.info(f"\n{refined_theme.curatorial_statement}\n")

        logger.info(f"{'─' * 100}")
        logger.info("SCHOLARLY RATIONALE")
        logger.info("─" * 100)
        logger.info(f"\n{refined_theme.scholarly_rationale}\n")

        logger.info(f"{'─' * 100}")
        logger.info(f"VALIDATED CONCEPTS ({len(refined_theme.validated_concepts)})")
        logger.info("─" * 100)
        for i, concept in enumerate(refined_theme.validated_concepts, 1):
            logger.info(f"\n{i}. {concept.refined_concept}")
            logger.info(f"   Original: {concept.original_concept}")
            logger.info(f"   Confidence: {concept.confidence_score:.2f}")
            logger.info(f"   Getty AAT ID: {concept.getty_aat_id or 'N/A'}")
            logger.info(f"   Definition: {concept.definition[:150]}...")
            if concept.related_concepts:
                logger.info(f"   Related: {', '.join(concept.related_concepts[:3])}")

        logger.info(f"\n{'─' * 100}")
        logger.info("RESEARCH BACKING")
        logger.info("─" * 100)
        logger.info(f"\nArt Historical Context:")
        logger.info(f"{refined_theme.research_backing.art_historical_context}\n")
        logger.info(f"Chronological Scope: {refined_theme.research_backing.chronological_scope}")
        logger.info(f"Geographical Scope: {refined_theme.research_backing.geographical_scope}")
        logger.info(f"Research Confidence: {refined_theme.research_backing.research_confidence:.2f}")

        logger.info(f"\n{'─' * 100}")
        logger.info("EXHIBITION PARAMETERS")
        logger.info("─" * 100)
        logger.info(f"Target Audience: {refined_theme.target_audience_refined}")
        logger.info(f"Complexity Level: {refined_theme.complexity_level}")
        logger.info(f"Estimated Duration: {refined_theme.estimated_duration}")
        logger.info(f"Primary Focus: {refined_theme.primary_focus}")
        logger.info(f"Secondary Themes: {', '.join(refined_theme.secondary_themes)}")

        if refined_theme.space_recommendations:
            logger.info(f"\nSpace Recommendations:")
            for rec in refined_theme.space_recommendations:
                logger.info(f"  • {rec}")

        logger.info(f"\nRefinement Confidence: {refined_theme.refinement_confidence:.2f}")

        # ============================================================
        # STAGE 2: ARTIST DISCOVERY
        # ============================================================
        logger.info("\n" + "=" * 100)
        logger.info("STAGE 2: ARTIST DISCOVERY")
        logger.info("=" * 100)

        artist_agent = ArtistDiscoveryAgent(client)
        discovered_artists = await artist_agent.discover_artists(
            refined_theme=refined_theme,
            session_id=session_id,
            max_artists=10,
            min_relevance=0.5,
            prioritize_diversity=True,
            diversity_targets={'min_female': 3, 'min_non_western': 2}
        )

        logger.info(f"\n{'=' * 100}")
        logger.info(f"DISCOVERED ARTISTS ({len(discovered_artists)})")
        logger.info("=" * 100)

        for i, artist in enumerate(discovered_artists, 1):
            logger.info(f"\n{'-' * 100}")
            logger.info(f"{i}. {artist.name}")
            logger.info("-" * 100)
            logger.info(f"Lifespan: {artist.get_lifespan() or 'Dates unknown'}")
            logger.info(f"Nationality: {artist.nationality or 'Unknown'}")
            logger.info(f"Birth Place: {artist.birth_place or 'Unknown'}")

            if artist.movements:
                logger.info(f"\nMovements: {', '.join(artist.movements[:5])}")

            if artist.techniques:
                logger.info(f"Techniques: {', '.join(artist.techniques[:5])}")

            if artist.genres:
                logger.info(f"Genres: {', '.join(artist.genres[:3])}")

            logger.info(f"\n✦ Relevance Score: {artist.relevance_score:.2f}")
            logger.info(f"✦ Discovery Confidence: {artist.discovery_confidence:.2f}")

            logger.info(f"\nRelevance Reasoning:")
            logger.info(f"{artist.relevance_reasoning}")

            if artist.known_works_count:
                logger.info(f"\nKnown Works: {artist.known_works_count}")

            if artist.institutional_connections:
                logger.info(f"Institutional Connections: {', '.join(artist.institutional_connections[:5])}")

            if artist.biography_short:
                logger.info(f"\nBiography:")
                logger.info(f"{artist.biography_short}")

            logger.info(f"\nData Sources: {', '.join(artist.discovery_sources)}")
            logger.info(f"Discovery Query: {artist.discovery_query or 'N/A'}")

        # Diversity metrics
        female_count = sum(1 for a in discovered_artists if a.raw_data.get('gender_normalized') == 'female')
        non_western_count = sum(1 for a in discovered_artists if a.raw_data.get('is_non_western', False))
        contemporary_count = sum(1 for a in discovered_artists if a.is_contemporary())

        logger.info(f"\n{'=' * 100}")
        logger.info("ARTIST DIVERSITY METRICS")
        logger.info("=" * 100)
        logger.info(f"Total Artists: {len(discovered_artists)}")
        if len(discovered_artists) > 0:
            logger.info(f"Female Artists: {female_count} ({female_count/len(discovered_artists)*100:.1f}%)")
            logger.info(f"Non-Western Artists: {non_western_count} ({non_western_count/len(discovered_artists)*100:.1f}%)")
            logger.info(f"Contemporary Artists: {contemporary_count} ({contemporary_count/len(discovered_artists)*100:.1f}%)")
        else:
            logger.warning("No artists discovered - check theme concepts and SPARQL queries")

        # ============================================================
        # STAGE 3: ARTWORK DISCOVERY
        # ============================================================
        logger.info("\n" + "=" * 100)
        logger.info("STAGE 3: ARTWORK DISCOVERY")
        logger.info("=" * 100)

        artwork_agent = ArtworkDiscoveryAgent(client)
        discovered_artworks = await artwork_agent.discover_artworks(
            refined_theme=refined_theme,
            selected_artists=discovered_artists,
            session_id=session_id,
            max_artworks=30,
            min_relevance=0.4,
            artworks_per_artist=5
        )

        logger.info(f"\n{'=' * 100}")
        logger.info(f"DISCOVERED ARTWORKS ({len(discovered_artworks)})")
        logger.info("=" * 100)

        # Group by artist
        by_artist = {}
        for artwork in discovered_artworks:
            artist = artwork.artist_name or 'Unknown'
            if artist not in by_artist:
                by_artist[artist] = []
            by_artist[artist].append(artwork)

        # Display artworks by artist
        for artist_name, artworks in by_artist.items():
            logger.info(f"\n{'-' * 100}")
            logger.info(f"ARTIST: {artist_name} ({len(artworks)} works)")
            logger.info("-" * 100)

            for i, artwork in enumerate(artworks, 1):
                logger.info(f"\n  {i}. {artwork.get_display_title()}")
                logger.info(f"     {'─' * 90}")
                logger.info(f"     Creator: {artwork.get_creator_display()}")
                logger.info(f"     Date: {artwork.get_date_display()}")

                if artwork.medium:
                    logger.info(f"     Medium: {artwork.medium}")

                if artwork.technique:
                    logger.info(f"     Technique: {artwork.technique}")

                if artwork.height_cm and artwork.width_cm:
                    size_cat = artwork.calculate_size_category()
                    logger.info(f"     Dimensions: {artwork.height_cm:.1f} x {artwork.width_cm:.1f} cm ({size_cat})")

                if artwork.institution_name:
                    logger.info(f"     Collection: {artwork.institution_name}")

                if artwork.inventory_number:
                    logger.info(f"     Inventory: {artwork.inventory_number}")

                logger.info(f"\n     ✦ Relevance Score: {artwork.relevance_score:.2f}")
                logger.info(f"     ✦ Completeness: {artwork.completeness_score:.2f}")
                logger.info(f"     ✦ Verification: {artwork.verification_status}")

                if artwork.subjects:
                    logger.info(f"\n     Subjects: {', '.join(artwork.subjects[:5])}")

                if artwork.theme_connections:
                    logger.info(f"\n     Theme Connections:")
                    for conn in artwork.theme_connections:
                        logger.info(f"       • {conn}")

                logger.info(f"\n     Relevance Reasoning:")
                logger.info(f"     {artwork.relevance_reasoning}")

                if artwork.iiif_manifest:
                    logger.info(f"\n     ✓ IIIF Manifest Available: {artwork.iiif_manifest}")

                if artwork.high_res_images:
                    logger.info(f"     ✓ High-res Images: {len(artwork.high_res_images)}")

                if artwork.loan_available is not None:
                    logger.info(f"\n     Loan Status: {'Available' if artwork.loan_available else 'Unknown'}")
                    if artwork.loan_conditions:
                        logger.info(f"     Loan Conditions: {artwork.loan_conditions}")

                logger.info(f"\n     Data Sources: {', '.join(artwork.all_sources)}")

                if artwork.description:
                    logger.info(f"\n     Description:")
                    logger.info(f"     {artwork.description[:300]}{'...' if len(artwork.description) > 300 else ''}")

        # ============================================================
        # FINAL SUMMARY & STATISTICS
        # ============================================================
        logger.info("\n" + "=" * 100)
        logger.info("EXHIBITION PROPOSAL SUMMARY")
        logger.info("=" * 100)

        logger.info(f"\n{'─' * 100}")
        logger.info("EXHIBITION OVERVIEW")
        logger.info("─" * 100)
        logger.info(f"Title: {refined_theme.exhibition_title}")
        logger.info(f"Target Audience: {refined_theme.target_audience_refined}")
        logger.info(f"Complexity: {refined_theme.complexity_level}")
        logger.info(f"Duration: {refined_theme.estimated_duration}")

        logger.info(f"\n{'─' * 100}")
        logger.info("CONTENT STATISTICS")
        logger.info("─" * 100)
        logger.info(f"Artists: {len(discovered_artists)}")
        logger.info(f"Artworks: {len(discovered_artworks)}")
        logger.info(f"Artists Represented: {len(by_artist)}")
        if len(by_artist) > 0:
            logger.info(f"Average Works per Artist: {len(discovered_artworks)/len(by_artist):.1f}")

        avg_artist_relevance = sum(a.relevance_score for a in discovered_artists) / len(discovered_artists) if discovered_artists else 0
        avg_artwork_relevance = sum(a.relevance_score for a in discovered_artworks) / len(discovered_artworks) if discovered_artworks else 0
        avg_completeness = sum(a.completeness_score for a in discovered_artworks) / len(discovered_artworks) if discovered_artworks else 0

        logger.info(f"\n{'─' * 100}")
        logger.info("QUALITY METRICS")
        logger.info("─" * 100)
        logger.info(f"Average Artist Relevance: {avg_artist_relevance:.2f}")
        logger.info(f"Average Artwork Relevance: {avg_artwork_relevance:.2f}")
        logger.info(f"Average Metadata Completeness: {avg_completeness:.2f}")
        logger.info(f"Theme Refinement Confidence: {refined_theme.refinement_confidence:.2f}")

        if discovered_artworks:
            with_iiif = sum(1 for a in discovered_artworks if a.iiif_manifest)
            with_images = sum(1 for a in discovered_artworks if a.thumbnail_url or a.high_res_images)
            with_dimensions = sum(1 for a in discovered_artworks if a.height_cm and a.width_cm)
            with_dates = sum(1 for a in discovered_artworks if a.date_created or a.date_created_earliest)

            logger.info(f"\n{'─' * 100}")
            logger.info("DIGITAL ASSETS & METADATA")
            logger.info("─" * 100)
            logger.info(f"With IIIF Manifests: {with_iiif} ({with_iiif/len(discovered_artworks)*100:.1f}%)")
            logger.info(f"With Images: {with_images} ({with_images/len(discovered_artworks)*100:.1f}%)")
            logger.info(f"With Dimensions: {with_dimensions} ({with_dimensions/len(discovered_artworks)*100:.1f}%)")
            logger.info(f"With Dates: {with_dates} ({with_dates/len(discovered_artworks)*100:.1f}%)")

        # Data source analysis
        artist_sources = {}
        for artist in discovered_artists:
            for source in artist.discovery_sources:
                artist_sources[source] = artist_sources.get(source, 0) + 1

        artwork_sources = {}
        for artwork in discovered_artworks:
            for source in artwork.all_sources:
                artwork_sources[source] = artwork_sources.get(source, 0) + 1

        logger.info(f"\n{'─' * 100}")
        logger.info("DATA SOURCES")
        logger.info("─" * 100)
        logger.info(f"Artist Sources:")
        for source, count in artist_sources.items():
            logger.info(f"  • {source}: {count} artists")
        logger.info(f"\nArtwork Sources:")
        for source, count in artwork_sources.items():
            logger.info(f"  • {source}: {count} artworks")

        logger.info("\n" + "=" * 100)
        logger.info("✓ FULL PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 100)

        return refined_theme, discovered_artists, discovered_artworks


async def main():
    """Run the full pipeline test"""
    try:
        await test_modern_art_time_theme()
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
