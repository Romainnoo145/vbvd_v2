"""
Discovery Models
Pydantic models for discovered artists and artworks from Stages 2 and 3
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime
from decimal import Decimal


class DiscoveredArtist(BaseModel):
    """
    Artist discovered during Stage 2 - Artist Discovery
    """

    # Basic identification
    name: str = Field(min_length=2, max_length=255)
    uri: Optional[str] = Field(default=None, description="Primary URI identifier")

    # Authority record mappings
    getty_ulan_uri: Optional[str] = None
    getty_ulan_id: Optional[str] = None
    wikidata_uri: Optional[str] = None
    wikidata_id: Optional[str] = None

    # Biographical information
    birth_year: Optional[int] = Field(default=None, ge=1000, le=2100)
    death_year: Optional[int] = Field(default=None, ge=1000, le=2100)
    nationality: Optional[str] = Field(default=None, max_length=100)
    birth_place: Optional[str] = Field(default=None, max_length=255)

    # Professional classification
    movements: List[str] = Field(
        default=[],
        description="Art movements associated with the artist"
    )
    techniques: List[str] = Field(
        default=[],
        description="Artistic techniques and media"
    )
    themes: List[str] = Field(
        default=[],
        description="Thematic focuses in their work"
    )
    genres: List[str] = Field(
        default=[],
        description="Artistic genres (portrait, landscape, etc.)"
    )

    # Career information
    active_period_start: Optional[int] = None
    active_period_end: Optional[int] = None
    major_works: List[str] = Field(
        default=[],
        description="List of major artwork titles"
    )

    # Relationships
    influenced_by: List[str] = Field(
        default=[],
        description="Artists who influenced this artist"
    )
    influenced: List[str] = Field(
        default=[],
        description="Artists influenced by this artist"
    )
    contemporaries: List[str] = Field(
        default=[],
        description="Contemporary artists"
    )

    # Institutional connections
    institutional_connections: List[str] = Field(
        default=[],
        description="Museums/institutions that hold their work"
    )

    # Relevance to current exhibition theme
    relevance_score: float = Field(ge=0, le=1, description="AI-calculated relevance")
    relevance_reasoning: str = Field(
        description="Detailed explanation of relevance to exhibition theme"
    )

    # Quality metrics
    importance_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Art historical importance score"
    )

    known_works_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of known artworks"
    )

    # Source information
    source_endpoint: str = Field(
        description="Data source that provided this information"
    )
    discovery_sources: List[str] = Field(
        default=[],
        description="All sources that contributed data"
    )

    # Rich biographical data
    biography_short: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Brief biographical summary"
    )
    biography_long: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Detailed biographical information"
    )

    # Additional structured data
    raw_data: Dict[str, Any] = Field(
        default={},
        description="Raw data from discovery sources"
    )

    # Discovery metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    discovery_query: Optional[str] = None
    discovery_confidence: float = Field(ge=0, le=1)

    @field_validator('death_year')
    @classmethod
    def validate_death_after_birth(cls, v, info):
        """Ensure death year is after birth year"""
        if v is not None and 'birth_year' in info.data and info.data['birth_year'] is not None:
            if v <= info.data['birth_year']:
                raise ValueError("Death year must be after birth year")
        return v

    def get_lifespan(self) -> Optional[str]:
        """Get formatted lifespan string"""
        if self.birth_year and self.death_year:
            return f"{self.birth_year}–{self.death_year}"
        elif self.birth_year:
            return f"b. {self.birth_year}"
        elif self.death_year:
            return f"d. {self.death_year}"
        return None

    def is_contemporary(self) -> bool:
        """Check if artist is contemporary (still alive or died recently)"""
        if self.death_year is None:
            return True  # Assume still alive
        return self.death_year >= 1950


class ArtworkCandidate(BaseModel):
    """
    Artwork discovered during Stage 3 - Artwork Discovery
    """

    # Basic identification
    uri: str = Field(description="Unique artwork identifier")
    title: str = Field(min_length=1, max_length=500)

    # Alternative titles
    alternative_titles: List[str] = Field(default=[])

    # Creator information
    artist_name: Optional[str] = Field(default=None, max_length=255)
    artist_uri: Optional[str] = None
    attribution_qualifier: Optional[str] = Field(
        default=None,
        description="e.g., 'attributed to', 'circle of', 'after'"
    )

    # Multiple creators for collaborative works
    creators: List[Dict[str, str]] = Field(
        default=[],
        description="List of creators with roles"
    )

    # Temporal information
    date_created: Optional[str] = Field(
        default=None,
        description="Creation date in flexible format"
    )
    date_created_earliest: Optional[int] = None
    date_created_latest: Optional[int] = None
    period: Optional[str] = Field(default=None, max_length=100)
    century: Optional[str] = None

    # Physical characteristics
    medium: Optional[str] = Field(default=None, max_length=255)
    support: Optional[str] = Field(default=None, max_length=255)
    technique: Optional[str] = Field(default=None, max_length=255)

    # Dimensions with flexible structure
    dimensions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Flexible dimension structure"
    )

    # Standard measurements (in cm)
    height_cm: Optional[float] = Field(default=None, gt=0)
    width_cm: Optional[float] = Field(default=None, gt=0)
    depth_cm: Optional[float] = Field(default=None, gt=0)

    # Classification
    artwork_type: Optional[str] = Field(default=None, max_length=100)
    genre: Optional[str] = Field(default=None, max_length=100)
    style: Optional[str] = Field(default=None, max_length=100)

    # Subject matter
    subjects: List[str] = Field(
        default=[],
        description="Subject matter and iconography"
    )
    iconclass_codes: List[str] = Field(default=[])

    # Current status and location
    current_location: Optional[str] = Field(default=None, max_length=255)
    institution_name: Optional[str] = Field(default=None, max_length=255)
    institution_uri: Optional[str] = None
    inventory_number: Optional[str] = Field(default=None, max_length=100)

    # Loan and exhibition information
    loan_available: Optional[bool] = None
    loan_conditions: Optional[str] = None
    on_permanent_display: Optional[bool] = None
    last_exhibited: Optional[str] = None

    # Condition and conservation
    condition: Optional[str] = None
    conservation_notes: Optional[str] = None
    condition_report_date: Optional[datetime] = None

    # Valuation and insurance
    insurance_value: Optional[Decimal] = Field(default=None, gt=0)
    insurance_currency: str = Field(default="EUR", max_length=3)
    valuation_date: Optional[datetime] = None

    # Provenance
    provenance: List[str] = Field(
        default=[],
        description="Ownership history"
    )
    acquisition_method: Optional[str] = None
    acquisition_date: Optional[str] = None

    # Digital assets
    iiif_manifest: Optional[str] = Field(default=None, description="IIIF manifest URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail image URL")
    high_res_images: List[str] = Field(default=[], description="High resolution image URLs")

    # Copyright and permissions
    copyright_status: Optional[str] = None
    reproduction_rights: Optional[str] = None

    # Exhibition relevance
    relevance_score: float = Field(
        ge=0,
        le=1,
        description="AI-calculated relevance to exhibition theme"
    )

    relevance_reasoning: str = Field(
        description="Detailed explanation of why this artwork fits the theme"
    )

    # Thematic connections
    theme_connections: List[str] = Field(
        default=[],
        description="Specific thematic connections to exhibition"
    )

    # Quality and completeness metrics
    completeness_score: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="How complete the metadata is"
    )

    verification_status: Literal['unverified', 'verified', 'disputed', 'needs_review'] = Field(
        default='unverified'
    )

    # Source information
    source: str = Field(description="Primary data source")
    source_url: Optional[str] = None
    all_sources: List[str] = Field(
        default=[],
        description="All sources that contributed data"
    )

    # Rich descriptive data
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Artwork description"
    )

    # Full source data
    raw_data: Dict[str, Any] = Field(
        default={},
        description="Complete raw data from sources"
    )

    # Discovery metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    discovery_query: Optional[str] = None
    discovery_confidence: float = Field(ge=0, le=1)

    @field_validator('insurance_value')
    @classmethod
    def validate_insurance_value(cls, v):
        """Validate insurance value is reasonable"""
        if v is not None:
            if v < 100:  # Minimum 100 EUR
                raise ValueError("Insurance value too low")
            if v > 1000000000:  # Maximum 1 billion EUR
                raise ValueError("Insurance value unreasonably high")
        return v

    def get_display_title(self) -> str:
        """Get title for display, handling untitled works"""
        if self.title.lower().strip() in ['untitled', 'unknown', '']:
            return f"Untitled ({self.medium or 'artwork'})"
        return self.title

    def get_creator_display(self) -> str:
        """Get creator name for display"""
        if self.artist_name:
            if self.attribution_qualifier:
                return f"{self.attribution_qualifier} {self.artist_name}"
            return self.artist_name
        elif self.creators:
            return ", ".join([c.get('name', 'Unknown') for c in self.creators[:3]])
        return "Unknown artist"

    def get_date_display(self) -> str:
        """Get formatted date for display"""
        if self.date_created:
            return self.date_created
        elif self.date_created_earliest and self.date_created_latest:
            if self.date_created_earliest == self.date_created_latest:
                return str(self.date_created_earliest)
            return f"{self.date_created_earliest}–{self.date_created_latest}"
        elif self.period:
            return self.period
        return "Date unknown"

    def calculate_size_category(self) -> Optional[str]:
        """Calculate size category based on dimensions"""
        if not (self.height_cm and self.width_cm):
            return None

        area = self.height_cm * self.width_cm

        if area < 100:  # Less than 10x10 cm
            return "miniature"
        elif area < 2500:  # Less than 50x50 cm
            return "small"
        elif area < 10000:  # Less than 100x100 cm
            return "medium"
        elif area < 40000:  # Less than 200x200 cm
            return "large"
        else:
            return "monumental"


class ArtworkCollection(BaseModel):
    """
    Collection of artworks for an exhibition with metadata
    """

    title: str
    description: Optional[str] = None
    artworks: List[ArtworkCandidate]

    # Collection statistics
    total_count: int = Field(ge=0)
    average_relevance: float = Field(ge=0, le=1)
    completeness_average: float = Field(ge=0, le=1)

    # Practical information
    total_insurance_value: Optional[Decimal] = None
    loan_requirements: List[str] = Field(default=[])

    # Collection metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    selection_criteria: Optional[str] = None

    @field_validator('total_count')
    @classmethod
    def validate_count_matches_artworks(cls, v, info):
        """Ensure count matches actual artwork list length"""
        if 'artworks' in info.data:
            actual_count = len(info.data['artworks'])
            if v != actual_count:
                raise ValueError(f"Total count ({v}) doesn't match artwork list length ({actual_count})")
        return v


__all__ = [
    'DiscoveredArtist',
    'ArtworkCandidate',
    'ArtworkCollection'
]