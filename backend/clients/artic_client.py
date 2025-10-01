"""
Art Institute of Chicago API Client
Searches modern art collection with IIIF image support
"""
import logging
import httpx
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class ArticClient:
    """
    Client for Art Institute of Chicago API

    Features:
    - No authentication required
    - 129,000+ artworks
    - IIIF Image API 2.0 support
    - Rich metadata with public domain filter
    """

    BASE_URL = "https://api.artic.edu/api/v1"
    IIIF_BASE = "https://www.artic.edu/iiif/2"

    def __init__(self, timeout: float = 30.0):
        """Initialize client with timeout"""
        self.timeout = timeout
        self.client = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()

    async def search_artworks(
        self,
        artist_name: Optional[str] = None,
        query: Optional[str] = None,
        date_start: Optional[int] = None,
        date_end: Optional[int] = None,
        public_domain_only: bool = True,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search artworks with filters

        Args:
            artist_name: Filter by artist name
            query: General search query
            date_start: Minimum creation year
            date_end: Maximum creation year
            public_domain_only: Only return public domain works
            limit: Maximum results (max 100)

        Returns:
            List of artwork dictionaries with metadata and IIIF image URLs
        """
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)

        try:
            # Build search URL
            search_url = f"{self.BASE_URL}/artworks/search"

            # Build query string
            query_parts = []

            if artist_name:
                query_parts.append(artist_name)

            if query:
                query_parts.append(query)

            search_query = " ".join(query_parts) if query_parts else "*"

            params = {
                "q": search_query,
                "limit": min(limit, 100),
                "fields": ",".join([
                    "id",
                    "title",
                    "artist_display",
                    "artist_title",
                    "date_display",
                    "date_start",
                    "date_end",
                    "medium_display",
                    "dimensions",
                    "dimensions_detail",
                    "credit_line",
                    "department_title",
                    "classification_title",
                    "artwork_type_title",
                    "image_id",
                    "thumbnail",
                    "is_public_domain",
                    "is_zoomable",
                    "has_not_been_viewed_much",
                    "boost_rank",
                    "color",
                    "on_loan_display",
                    "gallery_title",
                    "place_of_origin"
                ])
            }

            response = await self.client.get(search_url, params=params)

            if response.status_code != 200:
                logger.error(f"Art Institute search failed with status {response.status_code}")
                return []

            data = response.json()
            artwork_ids = [item["id"] for item in data.get("data", [])]

            if not artwork_ids:
                return []

            # Fetch full details for matching artworks
            artworks = await self._fetch_artwork_details(
                artwork_ids,
                date_start,
                date_end,
                public_domain_only
            )

            return artworks[:limit]

        except Exception as e:
            logger.error(f"Art Institute search failed: {e}")
            return []

    async def _fetch_artwork_details(
        self,
        artwork_ids: List[int],
        date_start: Optional[int] = None,
        date_end: Optional[int] = None,
        public_domain_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Fetch full details for artworks by IDs"""
        artworks = []

        for artwork_id in artwork_ids:
            try:
                url = f"{self.BASE_URL}/artworks/{artwork_id}"
                params = {
                    "fields": ",".join([
                        "id",
                        "title",
                        "artist_display",
                        "artist_title",
                        "artist_id",
                        "date_display",
                        "date_start",
                        "date_end",
                        "medium_display",
                        "dimensions",
                        "dimensions_detail",
                        "credit_line",
                        "department_title",
                        "classification_title",
                        "artwork_type_title",
                        "image_id",
                        "thumbnail",
                        "is_public_domain",
                        "is_zoomable",
                        "color",
                        "place_of_origin",
                        "description",
                        "short_description",
                        "copyright_notice",
                        "publication_history"
                    ])
                }

                response = await self.client.get(url, params=params)

                if response.status_code == 200:
                    artwork = response.json().get("data", {})

                    # Apply filters
                    if public_domain_only and not artwork.get("is_public_domain", False):
                        continue

                    if date_start and artwork.get("date_start"):
                        if artwork["date_start"] < date_start:
                            continue

                    if date_end and artwork.get("date_end"):
                        if artwork["date_end"] > date_end:
                            continue

                    # Add IIIF image URLs if image_id exists
                    if artwork.get("image_id"):
                        artwork["iiif_url"] = self._construct_iiif_url(
                            artwork["image_id"],
                            size="full"
                        )
                        artwork["thumbnail_iiif_url"] = self._construct_iiif_url(
                            artwork["image_id"],
                            size="843,"
                        )

                    artworks.append(artwork)

            except Exception as e:
                logger.warning(f"Failed to fetch artwork {artwork_id}: {e}")
                continue

        return artworks

    def _construct_iiif_url(
        self,
        image_id: str,
        region: str = "full",
        size: str = "full",
        rotation: str = "0",
        quality: str = "default",
        format: str = "jpg"
    ) -> str:
        """
        Construct IIIF Image API URL

        Args:
            image_id: Image identifier
            region: Region parameter (default: "full")
            size: Size parameter (e.g., "full", "843,", "!512,512")
            rotation: Rotation in degrees
            quality: Image quality (default, color, gray, bitonal)
            format: Output format (jpg, png, webp)

        Returns:
            Complete IIIF image URL
        """
        return f"{self.IIIF_BASE}/{image_id}/{region}/{size}/{rotation}/{quality}.{format}"

    async def search_by_artist(
        self,
        artist_name: str,
        date_start: Optional[int] = None,
        date_end: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Convenience method to search artworks by artist name

        Args:
            artist_name: Artist name to search
            date_start: Minimum creation year
            date_end: Maximum creation year
            limit: Maximum results

        Returns:
            List of artworks by the artist
        """
        return await self.search_artworks(
            artist_name=artist_name,
            date_start=date_start,
            date_end=date_end,
            limit=limit
        )

    async def get_artwork_by_id(self, artwork_id: int) -> Optional[Dict[str, Any]]:
        """
        Get full details for a single artwork

        Args:
            artwork_id: Artwork ID

        Returns:
            Artwork dictionary or None if not found
        """
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)

        try:
            url = f"{self.BASE_URL}/artworks/{artwork_id}"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json().get("data", {})

                # Add IIIF URLs
                if data.get("image_id"):
                    data["iiif_url"] = self._construct_iiif_url(data["image_id"])
                    data["thumbnail_iiif_url"] = self._construct_iiif_url(
                        data["image_id"],
                        size="843,"
                    )

                return data

            return None

        except Exception as e:
            logger.error(f"Failed to get artwork {artwork_id}: {e}")
            return None


__all__ = ['ArticClient']
