"""
Artist Extraction and Aggregation

Core innovation of Europeana-First: Discover artists FROM available artworks,
not the other way around.

Extracts artist names from artwork metadata, normalizes names, groups artworks
by artist, and aggregates metadata for each artist.
"""

import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from pydantic import BaseModel, Field
from collections import defaultdict, Counter

from backend.scoring import QualityScorer

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

    # IIIF availability tracking
    iiif_count: int = Field(default=0, description="Number of works with IIIF manifests")
    iiif_percentage: float = Field(default=0.0, description="Percentage of works with IIIF (0-100)")

    # Computed fields
    year_range: Optional[tuple] = Field(default=None, description="(min_year, max_year)")
    primary_country: Optional[str] = Field(default=None, description="Most common country")
    primary_institution: Optional[str] = Field(default=None, description="Institution with most works")

    # Derived fields (from Europeana data - no Wikipedia needed!)
    estimated_birth_year: Optional[int] = Field(default=None, description="Estimated based on first artwork year - 25")
    estimated_death_year: Optional[int] = Field(default=None, description="Estimated if not active recently")
    nationality: Optional[str] = Field(default=None, description="Derived from primary_country")
    relevance_reasoning: str = Field(default="", description="Generated explanation of artist relevance")
    movement: Optional[str] = Field(default=None, description="Art movement derived from exhibition sections")

    # Quality scoring (added by quality_scorer)
    quality_score: Optional[float] = Field(default=None, description="Overall quality score (0-100)")
    quality_breakdown: Optional[Dict[str, float]] = Field(default=None, description="Score breakdown by component")

    # Wikipedia enrichment (optional - Task 37)
    wikidata_id: Optional[str] = Field(default=None, description="Wikidata ID from Wikipedia")
    wikipedia_bio: Optional[str] = Field(default=None, description="Biography from Wikipedia")
    confirmed_birth_year: Optional[int] = Field(default=None, description="Confirmed birth year from Wikipedia")
    confirmed_death_year: Optional[int] = Field(default=None, description="Confirmed death year from Wikipedia")


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

    def __init__(self, min_works: int = 1, theme_period: Optional[Tuple[int, int]] = None):
        """
        Initialize extractor

        Args:
            min_works: Minimum number of works required to include artist (default: 1)
            theme_period: Optional (start_year, end_year) for quality scoring
        """
        self.min_works = min_works
        self.theme_period = theme_period
        self.quality_scorer = QualityScorer(theme_period=theme_period)
        logger.info(f"ArtistExtractor initialized with min_works={min_works}, theme_period={theme_period}")

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

            # Calculate quality score
            quality_score = self.quality_scorer.score_artist(
                works_count=artist.works_count,
                iiif_percentage=artist.iiif_percentage,
                institution_count=len(artist.institutions),
                year_range=artist.year_range
            )

            # Add quality score to artist
            artist.quality_score = quality_score.total_score
            artist.quality_breakdown = {
                'availability': quality_score.availability_score,
                'iiif': quality_score.iiif_score,
                'institution_diversity': quality_score.institution_diversity_score,
                'time_period_match': quality_score.time_period_match_score,
                'details': quality_score.breakdown
            }

            artists.append(artist)

        # Sort by quality score (descending) - artists with best availability rank highest
        artists.sort(key=lambda a: a.quality_score if a.quality_score else 0, reverse=True)

        filtered_count = len(artist_groups) - len(artists)

        logger.info(f"Extracted {len(artists)} artists (filtered {filtered_count} with <{self.min_works} works)")

        if artists:
            top_artist = artists[0]
            logger.info(f"Top artist: {top_artist.name} (quality: {top_artist.quality_score:.1f}, works: {top_artist.works_count}, IIIF: {top_artist.iiif_percentage:.0f}%)")

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

    def _derive_birth_year(self, year_range: Optional[tuple]) -> Optional[int]:
        """
        Estimate birth year from first artwork year
        Assumption: Artist typically starts creating artworks around age 25
        """
        if not year_range or not year_range[0]:
            return None
        return year_range[0] - 25

    def _derive_death_year(self, year_range: Optional[tuple]) -> Optional[int]:
        """
        Estimate death year if artist seems inactive
        If last work is recent (>= 2020), assume still alive (return None)
        Otherwise, estimate death ~5 years after last work
        """
        if not year_range or not year_range[1]:
            return None

        last_year = year_range[1]
        if last_year >= 2020:
            return None  # Likely still active

        return last_year + 5  # Estimate stopped working ~5 years before death

    def _derive_nationality(self, primary_country: Optional[str]) -> Optional[str]:
        """
        Convert country code to nationality adjective
        e.g., "Poland" -> "Polish", "Netherlands" -> "Dutch"
        """
        if not primary_country:
            return None

        # Common country to nationality mappings
        nationality_map = {
            'poland': 'Polish',
            'netherlands': 'Dutch',
            'belgium': 'Belgian',
            'germany': 'German',
            'france': 'French',
            'spain': 'Spanish',
            'italy': 'Italian',
            'united kingdom': 'British',
            'united states': 'American',
            'denmark': 'Danish',
            'sweden': 'Swedish',
            'norway': 'Norwegian',
            'finland': 'Finnish',
            'austria': 'Austrian',
            'switzerland': 'Swiss',
            'portugal': 'Portuguese',
            'greece': 'Greek',
            'czech republic': 'Czech',
            'hungary': 'Hungarian',
            'romania': 'Romanian',
            'croatia': 'Croatian',
            'slovenia': 'Slovenian',
            'estonia': 'Estonian',
            'latvia': 'Latvian',
            'lithuania': 'Lithuanian',
        }

        country_lower = primary_country.lower()
        return nationality_map.get(country_lower, primary_country)

    def _generate_relevance_reasoning(
        self,
        name: str,
        works_count: int,
        institutions: set,
        primary_country: Optional[str],
        media_types: Counter,
        year_range: Optional[tuple],
        sections: set
    ) -> str:
        """
        Generate human-readable relevance reasoning from Europeana metadata
        Explains why this artist is relevant for the exhibition
        """
        parts = []

        # Works availability
        parts.append(f"{works_count} {'work' if works_count == 1 else 'works'} available")

        # Geographic info
        if primary_country:
            parts.append(f"primarily from {primary_country}")

        # Institution count
        inst_count = len(institutions)
        if inst_count > 1:
            parts.append(f"across {inst_count} institutions")

        # Media types (top 2)
        if media_types:
            top_media = [media for media, _ in media_types.most_common(2)]
            if top_media:
                media_str = ' and '.join(top_media)
                parts.append(f"working in {media_str}")

        # Time period
        if year_range:
            start, end = year_range
            if start == end:
                parts.append(f"({start})")
            else:
                parts.append(f"({start}-{end})")

        # Exhibition section matches
        if sections:
            section_count = len(sections)
            parts.append(f"matching {section_count} exhibition {'section' if section_count == 1 else 'sections'}")

        return "; ".join(parts).capitalize() + "."

    def _derive_movement(self, sections: set) -> Optional[str]:
        """
        Derive art movement from exhibition section names
        Matches common art movements
        """
        if not sections:
            return None

        # Common movements to look for in section names
        movements = [
            'surrealism', 'contemporary art', 'modernism', 'abstract',
            'expressionism', 'cubism', 'dadaism', 'pop art',
            'minimalism', 'conceptual art', 'installation art'
        ]

        sections_lower = ' '.join(sections).lower()

        for movement in movements:
            if movement in sections_lower:
                return movement.title()

        return None

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
        iiif_count = 0

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

            # IIIF availability tracking
            edm_is_shown_by = artwork.get('edmIsShownBy')
            if edm_is_shown_by:
                iiif_count += 1

        # Compute derived fields
        year_range = (min(years), max(years)) if years else None
        primary_country = countries.most_common(1)[0][0] if countries else None
        primary_institution = list(institutions)[0] if institutions else None

        # Calculate IIIF percentage
        iiif_percentage = (iiif_count / len(artworks) * 100) if artworks else 0.0

        # Derive additional fields
        estimated_birth_year = self._derive_birth_year(year_range)
        estimated_death_year = self._derive_death_year(year_range)
        nationality = self._derive_nationality(primary_country)
        relevance_reasoning = self._generate_relevance_reasoning(
            name=normalized_name,
            works_count=len(artworks),
            institutions=institutions,
            primary_country=primary_country,
            media_types=media_types,
            year_range=year_range,
            sections=sections
        )
        movement = self._derive_movement(sections)

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
            iiif_count=iiif_count,
            iiif_percentage=round(iiif_percentage, 1),
            year_range=year_range,
            primary_country=primary_country,
            primary_institution=primary_institution,
            estimated_birth_year=estimated_birth_year,
            estimated_death_year=estimated_death_year,
            nationality=nationality,
            relevance_reasoning=relevance_reasoning,
            movement=movement
        )
