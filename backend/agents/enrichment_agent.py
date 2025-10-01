"""
Artwork Enrichment Agent
Uses Brave Search API to find missing metadata, images, and IIIF manifests
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
import httpx

from backend.models import ArtworkCandidate
from backend.config.data_sources import EssentialDataConfig

logger = logging.getLogger(__name__)


class ArtworkEnrichmentAgent:
    """
    Enriches artwork data using Brave Search API

    Searches for:
    - Missing metadata (dimensions, dates, medium)
    - High-resolution images
    - IIIF manifests
    - Current location/institution
    """

    def __init__(self):
        self.brave_api_key = EssentialDataConfig.get_api_key('brave_search')
        self.brave_enabled = bool(self.brave_api_key)

        if not self.brave_enabled:
            logger.warning("Brave Search API key not configured - enrichment disabled")
        else:
            logger.info("Brave Search enrichment enabled")

    async def enrich_artworks(
        self,
        artworks: List[ArtworkCandidate],
        max_concurrent: int = 3
    ) -> List[ArtworkCandidate]:
        """
        Enrich multiple artworks with Brave Search data

        Args:
            artworks: List of artwork candidates to enrich
            max_concurrent: Maximum concurrent Brave Search requests

        Returns:
            Enriched artwork list
        """
        if not self.brave_enabled:
            logger.warning("Brave Search disabled - skipping enrichment")
            return artworks

        logger.info(f"Starting enrichment for {len(artworks)} artworks")

        # Create enrichment tasks with semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_with_limit(artwork):
            async with semaphore:
                return await self._enrich_single_artwork(artwork)

        # Run enrichment in parallel with rate limiting
        enriched_artworks = await asyncio.gather(
            *[enrich_with_limit(artwork) for artwork in artworks],
            return_exceptions=True
        )

        # Filter out exceptions
        successful = []
        for i, result in enumerate(enriched_artworks):
            if isinstance(result, Exception):
                logger.error(f"Enrichment failed for '{artworks[i].title}': {result}")
                successful.append(artworks[i])  # Keep original
            else:
                successful.append(result)

        # Calculate improvement metrics
        before_iiif = sum(1 for a in artworks if a.iiif_manifest)
        after_iiif = sum(1 for a in successful if a.iiif_manifest)

        before_images = sum(1 for a in artworks if a.thumbnail_url or a.high_res_images)
        after_images = sum(1 for a in successful if a.thumbnail_url or a.high_res_images)

        logger.info(f"Enrichment complete:")
        logger.info(f"  IIIF manifests: {before_iiif} → {after_iiif} (+{after_iiif - before_iiif})")
        logger.info(f"  Images: {before_images} → {after_images} (+{after_images - before_images})")

        return successful

    async def _enrich_single_artwork(
        self,
        artwork: ArtworkCandidate
    ) -> ArtworkCandidate:
        """
        Enrich a single artwork using Brave Search
        """
        enriched = artwork.model_copy(deep=True)

        # Build search query
        query = self._build_search_query(artwork)

        logger.debug(f"Enriching '{artwork.title}' with query: {query}")

        # Search for general information
        search_results = await self._brave_search(query)

        if not search_results:
            return enriched

        # Extract enrichment data from results
        enriched = await self._extract_enrichment_data(enriched, search_results)

        # If still missing IIIF, search specifically for it
        if not enriched.iiif_manifest:
            iiif_results = await self._brave_search(f"{query} IIIF manifest")
            if iiif_results:
                enriched = await self._extract_iiif_data(enriched, iiif_results)

        # If still missing images, search for them
        if not enriched.thumbnail_url and not enriched.high_res_images:
            image_results = await self._brave_search(
                f"{query} high resolution image",
                search_type="image"
            )
            if image_results:
                enriched = await self._extract_image_data(enriched, image_results)

        return enriched

    def _build_search_query(self, artwork: ArtworkCandidate) -> str:
        """Build search query from artwork data"""
        parts = []

        if artwork.title:
            parts.append(f'"{artwork.title}"')

        if artwork.artist_name:
            parts.append(artwork.artist_name)

        if artwork.date_created_earliest:
            parts.append(str(artwork.date_created_earliest))

        return " ".join(parts)

    async def _brave_search(
        self,
        query: str,
        search_type: str = "web",
        count: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute Brave Search API query

        Args:
            query: Search query
            search_type: "web" or "image"
            count: Number of results

        Returns:
            List of search results or None
        """
        if not self.brave_api_key:
            return None

        try:
            if search_type == "web":
                url = "https://api.search.brave.com/res/v1/web/search"
            else:
                url = "https://api.search.brave.com/res/v1/images/search"

            headers = {
                "X-Subscription-Token": self.brave_api_key,
                "Accept": "application/json"
            }

            params = {
                "q": query,
                "count": count,
                "search_lang": "en",
                "country": "US",
                "safesearch": "moderate"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()

                if search_type == "web":
                    return data.get("web", {}).get("results", [])
                else:
                    return data.get("results", [])

        except httpx.HTTPError as e:
            logger.error(f"Brave Search API error for '{query}': {e}")
            return None
        except Exception as e:
            logger.error(f"Brave Search failed for '{query}': {e}")
            return None

    async def _extract_enrichment_data(
        self,
        artwork: ArtworkCandidate,
        results: List[Dict[str, Any]]
    ) -> ArtworkCandidate:
        """Extract general enrichment data from search results"""

        for result in results:
            title = result.get("title", "")
            description = result.get("description", "")
            url = result.get("url", "")
            combined_text = f"{title} {description}".lower()

            # Extract dimensions if missing
            if not artwork.height_cm or not artwork.width_cm:
                dims = self._extract_dimensions(combined_text)
                if dims:
                    if not artwork.height_cm:
                        artwork.height_cm = dims.get("height")
                    if not artwork.width_cm:
                        artwork.width_cm = dims.get("width")

            # Extract medium if missing
            if not artwork.medium:
                medium = self._extract_medium(combined_text)
                if medium:
                    artwork.medium = medium

            # Extract institution if missing
            if not artwork.institution_name:
                institution = self._extract_institution(combined_text, url)
                if institution:
                    artwork.institution_name = institution

            # Extract dates if missing
            if not artwork.date_created_earliest:
                date = self._extract_date(combined_text)
                if date:
                    artwork.date_created_earliest = date
                    if not artwork.date_created:
                        artwork.date_created = str(date)

        return artwork

    async def _extract_iiif_data(
        self,
        artwork: ArtworkCandidate,
        results: List[Dict[str, Any]]
    ) -> ArtworkCandidate:
        """
        Extract and parse IIIF manifest URLs from search results
        Fetches manifests and extracts actual image URLs
        """
        from backend.utils.iiif_utils import fetch_and_parse_manifest

        for result in results:
            url = result.get("url", "")
            description = result.get("description", "")

            manifest_url = None

            # Look for IIIF manifest URLs
            if "iiif" in url.lower() and "manifest" in url.lower():
                if url.endswith(".json") or "/manifest" in url:
                    manifest_url = url

            # Check description for manifest links
            if not manifest_url:
                manifest_match = re.search(r'(https?://[^\s]+manifest[^\s]*\.json)', description)
                if manifest_match:
                    manifest_url = manifest_match.group(1)

            # If we found a manifest URL, fetch and parse it
            if manifest_url:
                logger.debug(f"Found IIIF manifest: {manifest_url}")
                artwork.iiif_manifest = manifest_url

                try:
                    # Fetch and parse the manifest
                    metadata, images = await fetch_and_parse_manifest(manifest_url, timeout=10.0)

                    if images:
                        # Extract image URLs
                        image_urls = []
                        for img in images[:5]:
                            if 'iiif_url' in img:
                                image_urls.append(img['iiif_url'])
                            elif 'url' in img:
                                image_urls.append(img['url'])

                        if image_urls:
                            artwork.high_res_images = image_urls
                            if not artwork.thumbnail_url:
                                artwork.thumbnail_url = image_urls[0]
                            logger.debug(f"Extracted {len(image_urls)} images from IIIF manifest")

                except Exception as e:
                    logger.warning(f"Failed to parse IIIF manifest {manifest_url}: {e}")

                break

        return artwork

    async def _extract_image_data(
        self,
        artwork: ArtworkCandidate,
        results: List[Dict[str, Any]]
    ) -> ArtworkCandidate:
        """Extract image URLs from search results"""

        if not results:
            return artwork

        # Get first high-quality image
        for result in results[:3]:  # Check top 3 images
            image_url = result.get("url") or result.get("thumbnail", {}).get("src")
            if image_url:
                if not artwork.thumbnail_url:
                    artwork.thumbnail_url = image_url

                if not artwork.high_res_images:
                    artwork.high_res_images = [image_url]
                else:
                    artwork.high_res_images.append(image_url)

                logger.debug(f"Found image: {image_url}")

        return artwork

    def _extract_dimensions(self, text: str) -> Optional[Dict[str, float]]:
        """Extract dimensions from text (cm or inches)"""

        # Pattern: 123 x 456 cm or 123 × 456 cm
        cm_pattern = r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*cm'
        match = re.search(cm_pattern, text, re.IGNORECASE)

        if match:
            return {
                "height": float(match.group(1)),
                "width": float(match.group(2))
            }

        # Pattern: 12 x 18 inches
        inch_pattern = r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(?:inch|in|")'
        match = re.search(inch_pattern, text, re.IGNORECASE)

        if match:
            # Convert inches to cm
            return {
                "height": float(match.group(1)) * 2.54,
                "width": float(match.group(2)) * 2.54
            }

        return None

    def _extract_medium(self, text: str) -> Optional[str]:
        """Extract medium/technique from text"""

        media = [
            "oil on canvas", "oil on panel", "oil on board",
            "acrylic on canvas", "watercolor", "gouache",
            "tempera", "fresco", "mixed media",
            "bronze", "marble", "wood", "steel",
            "photograph", "print", "lithograph", "etching",
            "digital", "video", "installation"
        ]

        for medium in media:
            if medium in text.lower():
                return medium.title()

        return None

    def _extract_institution(self, text: str, url: str) -> Optional[str]:
        """Extract museum/institution name"""

        # Common institution patterns
        institutions = [
            r'(museum of [^,\.]+)',
            r'([^,\.]+ museum)',
            r'(rijksmuseum)',
            r'(metropolitan museum)',
            r'(louvre)',
            r'(tate [^,\.]+)',
            r'(national gallery[^,\.]*)',
            r'(getty [^,\.]+)'
        ]

        combined = f"{text} {url}".lower()

        for pattern in institutions:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return match.group(1).title()

        return None

    def _extract_date(self, text: str) -> Optional[int]:
        """Extract creation date from text"""

        # Pattern: years like 1920, 1850, etc.
        year_pattern = r'\b(1[4-9]\d{2}|20[0-2]\d)\b'
        matches = re.findall(year_pattern, text)

        if matches:
            # Return first reasonable year
            for year_str in matches:
                year = int(year_str)
                if 1400 <= year <= 2025:
                    return year

        return None


__all__ = ['ArtworkEnrichmentAgent']
