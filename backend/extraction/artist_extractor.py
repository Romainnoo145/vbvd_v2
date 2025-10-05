"""
Artist Extraction and Aggregation

Core innovation of Europeana-First: Discover artists FROM available artworks,
not the other way around.

Extracts artist names from artwork metadata, normalizes names, groups artworks
by artist, and aggregates metadata for each artist.
"""

import re
import logging
from typing import List, Dict, Set, Optional
from pydantic import BaseModel, Field
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class Artist(BaseModel):
    """Aggregated artist information from their artworks"""
    name: str = Field(description="Normalized artist name")
    original_names: List[str] = Field(default_factory=list, description="All name variants found")
    works_count: int = Field(description="Number of artworks")
    artworks: List[Dict] = Field(default_factory=list, description="Associated artwork records")

    # Aggregated metadata
    institutions: List[str] = Field(default_factory=list, description="Museums/institutions with works")
    countries: Dict[str, int] = Field(default_factory=dict, description="Countries with work counts")
    years: List[int] = Field(default_factory=list, description="Years of artworks")
    media_types: Dict[str, int] = Field(default_factory=dict, description="Media types with counts")
    sections: List[str] = Field(default_factory=list, description="Exhibition sections matched")

    # Computed fields
    year_range: Optional[tuple] = Field(default=None, description="(min_year, max_year)")
    primary_country: Optional[str] = Field(default=None, description="Most common country")
    primary_institution: Optional[str] = Field(default=None, description="Institution with most works")


class ArtistExtractionResults(BaseModel):
    """Results from artist extraction process"""
    total_artworks_processed: int
    artists_found: int
    artists_filtered: int = Field(description="Artists removed by filters")
    artists: List[Artist]

    # Statistics
    unknown_count: int = Field(default=0, description="Artworks with Unknown/missing artist")
    uri_count: int = Field(default=0, description="Artworks with URI-only artist")
    various_count: int = Field(default=0, description="Artworks with Various/Multiple artists")


class ArtistExtractor:
    """
    Extract and aggregate artists from Europeana artwork data

    Handles:
    - Different name formats: "Last, First" / "First Last" / URIs
    - Name normalization and deduplication
    - Filtering invalid/generic names
    - Metadata aggregation per artist
    """

    # Names to filter out (case-insensitive)
    INVALID_NAMES = {
        'unknown', 'onbekend', 'various', 'diverse', 'meerdere',
        'multiple', 'anonymous', 'anoniem', 'not recorded', 'niet vermeld',
        'n/a', 'none', 'geen', 'unidentified', 'niet geïdentificeerd'
    }

    # URI patterns to detect
    URI_PATTERN = re.compile(r'^https?://|^urn:|^http://')

    def __init__(self, min_works: int = 1):
        """
        Initialize extractor

        Args:
            min_works: Minimum number of works required to include artist (default: 1)
        """
        self.min_works = min_works
        logger.info(f"ArtistExtractor initialized with min_works={min_works}")

    def extract_artists(self, artworks: List[Dict]) -> ArtistExtractionResults:
        """
        Extract artists from artwork list

        Args:
            artworks: List of artwork dicts from Europeana

        Returns:
            ArtistExtractionResults with aggregated artist data
        """
        if not artworks:
            logger.warning("No artworks provided for artist extraction")
            return ArtistExtractionResults(
                total_artworks_processed=0,
                artists_found=0,
                artists=[]
            )

        logger.info(f"Extracting artists from {len(artworks)} artworks...")

        # Group artworks by artist
        artist_groups: Dict[str, List[Dict]] = defaultdict(list)
        unknown_count = 0
        uri_count = 0
        various_count = 0

        for artwork in artworks:
            # Extract creator name(s)
            creators = self._extract_creators(artwork)

            if not creators:
                unknown_count += 1
                continue

            # Process each creator
            for creator in creators:
                # Normalize name
                normalized = self._normalize_name(creator)

                if not normalized:
                    unknown_count += 1
                    continue

                # Check if it's a URI
                if self.URI_PATTERN.match(creator):
                    uri_count += 1
                    continue

                # Check if it's an invalid name
                if self._is_invalid_name(normalized):
                    if 'various' in normalized.lower() or 'multiple' in normalized.lower():
                        various_count += 1
                    else:
                        unknown_count += 1
                    continue

                # Add to artist's artworks
                artist_groups[normalized].append(artwork)

        logger.info(f"Found {len(artist_groups)} unique artist names")
        logger.info(f"Filtered: {unknown_count} unknown, {uri_count} URIs, {various_count} various/multiple")

        # Build Artist objects
        artists = []
        for normalized_name, artist_artworks in artist_groups.items():
            # Filter by minimum works
            if len(artist_artworks) < self.min_works:
                continue

            artist = self._build_artist(normalized_name, artist_artworks)
            artists.append(artist)

        # Sort by works count (descending)
        artists.sort(key=lambda a: a.works_count, reverse=True)

        filtered_count = len(artist_groups) - len(artists)

        logger.info(f"Extracted {len(artists)} artists (filtered {filtered_count} with <{self.min_works} works)")

        return ArtistExtractionResults(
            total_artworks_processed=len(artworks),
            artists_found=len(artists),
            artists_filtered=filtered_count,
            artists=artists,
            unknown_count=unknown_count,
            uri_count=uri_count,
            various_count=various_count
        )

    def _extract_creators(self, artwork: Dict) -> List[str]:
        """Extract creator names from artwork metadata"""
        creators = []

        # Try dcCreator field
        dc_creator = artwork.get('dcCreator', [])
        if isinstance(dc_creator, list):
            creators.extend([c for c in dc_creator if c])
        elif dc_creator:
            creators.append(dc_creator)

        # Fallback: try edmAgent
        if not creators:
            edm_agent = artwork.get('edmAgent', [])
            if isinstance(edm_agent, list):
                creators.extend([a for a in edm_agent if a])
            elif edm_agent:
                creators.append(edm_agent)

        return creators

    def _normalize_name(self, name: str) -> str:
        """
        Normalize artist name

        Handles formats:
        - "Last, First" → "First Last"
        - "First Last" → "First Last"
        - Extra whitespace → single space
        - Parentheses/dates removed
        """
        if not name or not isinstance(name, str):
            return ""

        # Clean up
        name = name.strip()

        # Remove dates in parentheses: "Name (1920-1980)" → "Name"
        name = re.sub(r'\s*\([^)]*\d{4}[^)]*\)', '', name)

        # Remove other parenthetical info
        name = re.sub(r'\s*\([^)]*\)', '', name)

        # Handle "Last, First" format
        if ',' in name:
            parts = name.split(',', 1)
            if len(parts) == 2:
                last, first = parts
                name = f"{first.strip()} {last.strip()}"

        # Normalize whitespace
        name = ' '.join(name.split())

        # Title case for consistency
        name = name.title()

        return name

    def _is_invalid_name(self, name: str) -> bool:
        """Check if name should be filtered out"""
        name_lower = name.lower()

        # Check against invalid names list
        for invalid in self.INVALID_NAMES:
            if invalid in name_lower:
                return True

        # Check if too short
        if len(name) < 2:
            return True

        # Check if looks like a number
        if name.replace(' ', '').isdigit():
            return True

        return False

    def _build_artist(self, normalized_name: str, artworks: List[Dict]) -> Artist:
        """Build Artist object with aggregated metadata"""

        # Collect original name variants
        original_names = set()
        for artwork in artworks:
            creators = self._extract_creators(artwork)
            for creator in creators:
                if self._normalize_name(creator) == normalized_name:
                    original_names.add(creator)

        # Aggregate metadata
        institutions = set()
        countries = Counter()
        years = []
        media_types = Counter()
        sections = set()

        for artwork in artworks:
            # Institutions
            provider = artwork.get('dataProvider', [])
            if isinstance(provider, list):
                institutions.update(provider)
            elif provider:
                institutions.add(provider)

            # Countries
            country = artwork.get('country', [])
            if isinstance(country, list):
                countries.update(country)
            elif country:
                countries[country] += 1

            # Years
            year = artwork.get('year')
            if year:
                if isinstance(year, list):
                    year = year[0] if year else None
                if year:
                    try:
                        year_int = int(str(year)[:4])
                        if 1000 <= year_int <= 2100:  # Sanity check
                            years.append(year_int)
                    except (ValueError, TypeError):
                        pass

            # Media types
            dc_type = artwork.get('dcType', [])
            if isinstance(dc_type, list):
                for dt in dc_type:
                    if dt:
                        media_types[dt] += 1
            elif dc_type:
                media_types[dc_type] += 1

            # Sections
            section = artwork.get('_section_title')
            if section:
                sections.add(section)

        # Compute derived fields
        year_range = (min(years), max(years)) if years else None
        primary_country = countries.most_common(1)[0][0] if countries else None
        primary_institution = list(institutions)[0] if institutions else None

        return Artist(
            name=normalized_name,
            original_names=sorted(list(original_names)),
            works_count=len(artworks),
            artworks=artworks,
            institutions=sorted(list(institutions)),
            countries=dict(countries.most_common(5)),  # Top 5 countries
            years=sorted(years),
            media_types=dict(media_types.most_common(5)),  # Top 5 media types
            sections=sorted(list(sections)),
            year_range=year_range,
            primary_country=primary_country,
            primary_institution=primary_institution
        )
