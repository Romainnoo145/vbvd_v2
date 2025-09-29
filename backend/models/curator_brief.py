"""
Curator Brief Models
Pydantic models for the curator input and workflow validation
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Optional, Literal, Dict, Any, Union
from datetime import date, datetime
from decimal import Decimal
import re


class CuratorBrief(BaseModel):
    """
    Input from curator via web form - VALIDATED for Linked Art compatibility
    This is the starting point of the 3-stage workflow
    """

    # Core exhibition concept
    theme_title: str = Field(
        min_length=5,
        max_length=200,
        description="Main exhibition title or theme"
    )

    theme_description: str = Field(
        min_length=50,
        max_length=2000,
        description="Detailed description of the exhibition concept"
    )

    # CRITICAL: These concepts must be mappable to Getty AAT terms
    theme_concepts: List[str] = Field(
        min_length=1,
        max_length=10,
        description="Key concepts that can be resolved to Getty AAT URIs"
    )

    # Artist preferences
    reference_artists: Optional[List[str]] = Field(
        default=[],
        max_length=20,
        description="Artist names resolvable to Getty ULAN URIs"
    )

    # Inspiration sources
    reference_works: Optional[List[str]] = Field(
        default=[],
        description="URLs or titles of reference artworks"
    )

    # Constraints
    exclude_artists: Optional[List[str]] = Field(
        default=[],
        description="Artists to exclude from consideration"
    )

    # Budget and logistics
    budget_max: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Maximum budget in EUR"
    )

    insurance_max: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Maximum insurance value in EUR"
    )

    # Physical space
    space_type: Literal['main', 'project', 'outdoor', 'digital'] = Field(
        default='main',
        description="Type of exhibition space"
    )

    dimensions: Optional[Dict[str, float]] = Field(
        default=None,
        description="Space dimensions (length, width, height in meters)"
    )

    # Audience and experience
    target_audience: Literal['general', 'academic', 'youth', 'family', 'specialists'] = Field(
        default='general',
        description="Primary target audience"
    )

    # Timeline
    exhibition_dates: Optional[Dict[str, date]] = Field(
        default=None,
        description="Proposed start and end dates"
    )

    duration_weeks: Optional[int] = Field(
        default=12,
        ge=2,
        le=52,
        description="Exhibition duration in weeks"
    )

    # Institution context
    institution_id: str = Field(
        default="bommel_van_dam",
        description="Institution identifier"
    )

    # Scope preferences
    include_international: bool = Field(
        default=True,
        description="Include international loans"
    )

    priority_regional: bool = Field(
        default=False,
        description="Prioritize regional/local artworks"
    )

    # Accessibility
    required_accessibility: List[str] = Field(
        default=[],
        description="Special accessibility requirements"
    )

    # Diversity and representation
    prioritize_diversity: bool = Field(
        default=True,
        description="Prioritize diverse representation (gender, ethnicity, geography)"
    )

    diversity_requirements: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Specific diversity targets, e.g., {'min_female_artists': 3, 'min_non_western': 2}"
    )

    # Curatorial approach
    narrative_style: Optional[Literal['chronological', 'thematic', 'dialogic', 'immersive']] = Field(
        default='thematic',
        description="Preferred curatorial narrative approach"
    )

    # Metadata
    curator_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Name of the curator submitting the brief"
    )

    contact_email: Optional[str] = Field(
        default=None,
        description="Contact email for follow-up"
    )

    @field_validator('theme_concepts')
    @classmethod
    def validate_concepts(cls, v):
        """Ensure concepts are appropriate for Getty AAT resolution"""
        if not v:
            raise ValueError("At least one theme concept is required")

        invalid_concepts = []
        for concept in v:
            concept_clean = concept.strip().lower()

            # Basic validation rules
            if len(concept_clean) < 3:
                invalid_concepts.append(f"'{concept}' too short")
            elif len(concept_clean) > 100:
                invalid_concepts.append(f"'{concept}' too long")
            elif not re.match(r'^[a-zA-Z0-9\s\-_]+$', concept):
                invalid_concepts.append(f"'{concept}' contains invalid characters")

        if invalid_concepts:
            raise ValueError(f"Invalid concepts: {', '.join(invalid_concepts)}")

        return [c.strip() for c in v]

    @field_validator('reference_artists')
    @classmethod
    def validate_artists(cls, v):
        """Basic validation for artist names"""
        if not v:
            return v

        invalid_artists = []
        for artist in v:
            artist_clean = artist.strip()
            if len(artist_clean) < 2:
                invalid_artists.append(f"'{artist}' too short")
            elif len(artist_clean) > 200:
                invalid_artists.append(f"'{artist}' too long")

        if invalid_artists:
            raise ValueError(f"Invalid artist names: {', '.join(invalid_artists)}")

        return [a.strip() for a in v]

    @field_validator('dimensions')
    @classmethod
    def validate_dimensions(cls, v):
        """Validate space dimensions"""
        if v is None:
            return v

        required_keys = ['length', 'width']
        missing_keys = [key for key in required_keys if key not in v]

        if missing_keys:
            raise ValueError(f"Missing dimension keys: {missing_keys}")

        for key, value in v.items():
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"Dimension '{key}' must be a positive number")

        return v

    @field_validator('exhibition_dates')
    @classmethod
    def validate_dates(cls, v):
        """Validate exhibition date range"""
        if v is None:
            return v

        if 'start' in v and 'end' in v:
            if v['start'] >= v['end']:
                raise ValueError("Start date must be before end date")

        return v

    def get_concept_string(self) -> str:
        """Get concepts as a searchable string"""
        return " ".join(self.theme_concepts)

    def get_artist_string(self) -> str:
        """Get reference artists as a searchable string"""
        return " ".join(self.reference_artists or [])

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        str_strip_whitespace = True


class ThemeValidation(BaseModel):
    """Validation result for theme concepts against Getty AAT"""

    concept: str
    valid: bool
    getty_aat_uri: Optional[str] = None
    getty_aat_id: Optional[str] = None
    confidence_score: float = Field(ge=0, le=1)
    suggested_alternatives: List[str] = Field(default=[])
    error_message: Optional[str] = None


class ArtistValidation(BaseModel):
    """Validation result for artists against Getty ULAN"""

    artist_name: str
    valid: bool
    getty_ulan_uri: Optional[str] = None
    getty_ulan_id: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    nationality: Optional[str] = None
    confidence_score: float = Field(ge=0, le=1)
    suggested_alternatives: List[str] = Field(default=[])
    error_message: Optional[str] = None


class ValidationReport(BaseModel):
    """Complete validation report for a curator brief"""

    brief_id: str
    theme_validations: List[ThemeValidation]
    artist_validations: List[ArtistValidation]
    overall_valid: bool
    confidence_score: float = Field(ge=0, le=1)
    recommendations: List[str] = Field(default=[])
    estimated_success_rate: float = Field(ge=0, le=1)

    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    validation_duration_ms: Optional[int] = None

    @field_validator('overall_valid')
    @classmethod
    def calculate_overall_validity(cls, v, info):
        """Calculate overall validity based on individual validations"""
        # This will be computed dynamically based on theme and artist validations
        return v


class EnrichedQuery(BaseModel):
    """
    Processed query after Stage 1 (Theme Refinement)
    Contains validated concepts and enriched information
    """

    original_brief_id: str
    session_id: str

    # Refined theme information
    refined_title: str
    refined_description: str
    curatorial_angle: str
    historical_context: str

    # Validated Getty AAT mappings
    getty_aat_uris: Dict[str, str] = Field(
        description="Concept -> Getty AAT URI mapping"
    )

    # Validated artist mappings
    ulan_artist_uris: Dict[str, str] = Field(
        default={},
        description="Artist name -> Getty ULAN URI mapping"
    )

    # Additional structured data
    iconclass_codes: List[str] = Field(
        default=[],
        description="Resolved iconographic classification codes"
    )

    # Query strategies for each data source
    sparql_queries: Dict[str, str] = Field(
        description="Data source -> SPARQL query mapping"
    )

    # Semantic embeddings for similarity search
    embedding_vectors: List[float] = Field(
        default=[],
        description="OpenAI embedding for semantic search"
    )

    # Confidence metrics
    confidence_scores: Dict[str, float] = Field(
        description="Per-concept confidence scores"
    )

    # Search strategy
    search_strategy: Literal['exact', 'semantic', 'hybrid'] = Field(
        default='hybrid',
        description="Recommended search approach"
    )

    # Research sources
    research_sources: List[str] = Field(
        default=[],
        description="URLs and sources used for enrichment"
    )

    # Estimated scope and feasibility
    estimated_artwork_count: Optional[int] = None
    estimated_artist_count: Optional[int] = None
    feasibility_score: float = Field(ge=0, le=1)

    # Processing metadata
    stage1_agent_version: str = Field(default="1.0")
    processing_duration_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
    'CuratorBrief',
    'ThemeValidation',
    'ArtistValidation',
    'ValidationReport',
    'EnrichedQuery'
]