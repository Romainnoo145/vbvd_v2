"""
Test the simple artist discovery approach
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.artist_discovery_simple import SimpleArtistDiscovery
from backend.models import RefinedTheme, ValidatedConcept
from backend.clients.essential_data_client import EssentialDataClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_simple_discovery():
    """Test simple Wikipedia-based discovery"""

    # Create a realistic theme
    theme = RefinedTheme(
        refined_title="Color, Form, and Space in Contemporary Abstraction",
        validated_concepts=[
            ValidatedConcept(
                refined_concept="De Stijl",
                confidence_score=0.8,
                wikipedia_uris=[]
            ),
            ValidatedConcept(
                refined_concept="Color Field Painting",
                confidence_score=0.7,
                wikipedia_uris=[]
            ),
            ValidatedConcept(
                refined_concept="Minimalism",
                confidence_score=0.7,
                wikipedia_uris=[]
            ),
        ],
        scholarly_context="Abstract art movements",
        recommended_periods=["20th century", "contemporary"],
        key_themes=["abstraction", "color", "form"]
    )

    reference_artists = ["Piet Mondrian", "Kazimir Malevich", "Josef Albers"]

    async with EssentialDataClient() as client:
        discoverer = SimpleArtistDiscovery(client)

        logger.info("=" * 100)
        logger.info("TESTING SIMPLE ARTIST DISCOVERY")
        logger.info("=" * 100)

        artists = await discoverer.discover_artists(
            refined_theme=theme,
            reference_artists=reference_artists,
            max_artists=20
        )

        logger.info(f"\n{'=' * 100}")
        logger.info(f"RESULTS: Found {len(artists)} artists")
        logger.info("=" * 100)

        for i, artist in enumerate(artists[:15], 1):
            logger.info(f"\n{i}. {artist['name']}")
            if artist.get('birth_year'):
                lifespan = f"{artist['birth_year']}"
                if artist.get('death_year'):
                    lifespan += f"-{artist['death_year']}"
                logger.info(f"   {lifespan}")
            logger.info(f"   {artist['description'][:150]}...")

        logger.info(f"\n{'=' * 100}")
        logger.info(f"✓ Simple discovery found {len(artists)} artists!")
        logger.info("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_simple_discovery())
