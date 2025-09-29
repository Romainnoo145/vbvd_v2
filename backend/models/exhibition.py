"""
Exhibition Models
Pydantic models for final exhibition proposals and related structures
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime, date
from decimal import Decimal

from .discovery import ArtworkCandidate


class ExhibitionSection(BaseModel):
    """
    A thematic section within an exhibition
    """

    title: str = Field(min_length=1, max_length=200)
    subtitle: Optional[str] = Field(default=None, max_length=300)
    description: str = Field(min_length=50, max_length=1500)

    # Content
    artworks: List[str] = Field(
        description="List of artwork URIs in this section"
    )
    key_themes: List[str] = Field(
        description="Main themes explored in this section"
    )

    # Presentation
    wall_text: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Introductory wall text for the section"
    )

    # Spatial organization
    suggested_layout: Optional[str] = Field(
        default=None,
        description="Suggested physical layout for this section"
    )

    # Estimated space requirements
    wall_length_meters: Optional[float] = Field(default=None, gt=0)
    floor_area_sqm: Optional[float] = Field(default=None, gt=0)

    # Educational content
    key_artworks: List[str] = Field(
        default=[],
        description="URIs of key artworks that need detailed labels"
    )

    # Section metadata
    order_index: int = Field(ge=1, description="Order within the exhibition")
    estimated_viewing_time: Optional[int] = Field(
        default=None,
        ge=1,
        description="Estimated viewing time in minutes"
    )


class VisitorJourneyStep(BaseModel):
    """
    A step in the visitor journey through the exhibition
    """

    step_number: int = Field(ge=1)
    location: str = Field(description="Physical location or section")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=20, max_length=800)

    # Experience design
    emotional_tone: Optional[str] = Field(
        default=None,
        description="Intended emotional response"
    )

    key_takeaway: str = Field(
        min_length=10,
        max_length=300,
        description="Main message or insight for visitors"
    )

    # Practical information
    estimated_duration: Optional[int] = Field(
        default=None,
        ge=1,
        description="Time to spend at this step in minutes"
    )

    # Interactive elements
    interactive_elements: List[str] = Field(
        default=[],
        description="Interactive or multimedia elements"
    )


class SpaceRequirements(BaseModel):
    """
    Physical space requirements for the exhibition
    """

    # Basic dimensions
    minimum_wall_length: float = Field(gt=0, description="Minimum wall length in meters")
    minimum_floor_area: float = Field(gt=0, description="Minimum floor area in square meters")
    ceiling_height_required: Optional[float] = Field(
        default=None,
        gt=0,
        description="Minimum ceiling height in meters"
    )

    # Specialized spaces
    needs_climate_control: bool = Field(default=True)
    needs_low_light: bool = Field(default=False)
    needs_high_security: bool = Field(default=False)

    # Technical requirements
    electrical_outlets: int = Field(default=0, ge=0)
    network_connections: int = Field(default=0, ge=0)
    audio_visual_setup: bool = Field(default=False)

    # Accessibility
    wheelchair_accessible: bool = Field(default=True)
    audio_description_points: int = Field(default=0, ge=0)
    tactile_elements: bool = Field(default=False)

    # Storage and work areas
    preparation_space_required: bool = Field(default=False)
    storage_space_required: bool = Field(default=False)

    # Special considerations
    special_requirements: List[str] = Field(
        default=[],
        description="Any special spatial or technical requirements"
    )


class BudgetBreakdown(BaseModel):
    """
    Detailed budget breakdown for the exhibition
    """

    # Loan and transport costs
    loan_fees: Decimal = Field(default=Decimal('0'), ge=0)
    transport_costs: Decimal = Field(default=Decimal('0'), ge=0)
    insurance_costs: Decimal = Field(default=Decimal('0'), ge=0)
    courier_fees: Decimal = Field(default=Decimal('0'), ge=0)

    # Installation and design
    exhibition_design: Decimal = Field(default=Decimal('0'), ge=0)
    installation_labor: Decimal = Field(default=Decimal('0'), ge=0)
    materials_construction: Decimal = Field(default=Decimal('0'), ge=0)

    # Technology and multimedia
    av_equipment: Decimal = Field(default=Decimal('0'), ge=0)
    interactive_elements: Decimal = Field(default=Decimal('0'), ge=0)
    lighting: Decimal = Field(default=Decimal('0'), ge=0)

    # Content and communication
    catalog_production: Decimal = Field(default=Decimal('0'), ge=0)
    wall_texts_labels: Decimal = Field(default=Decimal('0'), ge=0)
    marketing_materials: Decimal = Field(default=Decimal('0'), ge=0)

    # Staffing
    curator_fees: Decimal = Field(default=Decimal('0'), ge=0)
    conservation_costs: Decimal = Field(default=Decimal('0'), ge=0)
    additional_staff: Decimal = Field(default=Decimal('0'), ge=0)

    # Events and programming
    opening_event: Decimal = Field(default=Decimal('0'), ge=0)
    educational_programs: Decimal = Field(default=Decimal('0'), ge=0)
    special_events: Decimal = Field(default=Decimal('0'), ge=0)

    # Contingency
    contingency_percentage: float = Field(default=10.0, ge=0, le=50)
    contingency_amount: Optional[Decimal] = None

    # Currency
    currency: str = Field(default="EUR", max_length=3)

    def calculate_totals(self) -> Dict[str, Decimal]:
        """Calculate budget totals and subtotals"""
        # Direct costs
        direct_costs = (
            self.loan_fees + self.transport_costs + self.insurance_costs +
            self.courier_fees + self.exhibition_design + self.installation_labor +
            self.materials_construction
        )

        # Technology costs
        technology_costs = (
            self.av_equipment + self.interactive_elements + self.lighting
        )

        # Content costs
        content_costs = (
            self.catalog_production + self.wall_texts_labels + self.marketing_materials
        )

        # Staffing costs
        staffing_costs = (
            self.curator_fees + self.conservation_costs + self.additional_staff
        )

        # Programming costs
        programming_costs = (
            self.opening_event + self.educational_programs + self.special_events
        )

        # Subtotal
        subtotal = (
            direct_costs + technology_costs + content_costs +
            staffing_costs + programming_costs
        )

        # Contingency
        contingency = subtotal * (Decimal(str(self.contingency_percentage)) / 100)

        # Total
        total = subtotal + contingency

        return {
            'direct_costs': direct_costs,
            'technology_costs': technology_costs,
            'content_costs': content_costs,
            'staffing_costs': staffing_costs,
            'programming_costs': programming_costs,
            'subtotal': subtotal,
            'contingency': contingency,
            'total': total
        }


class RiskAssessment(BaseModel):
    """
    Risk assessment for the exhibition
    """

    # Loan risks
    loan_approval_risk: Literal['low', 'medium', 'high'] = Field(default='medium')
    transport_risk: Literal['low', 'medium', 'high'] = Field(default='medium')
    condition_risk: Literal['low', 'medium', 'high'] = Field(default='low')

    # Budget risks
    budget_overrun_risk: Literal['low', 'medium', 'high'] = Field(default='medium')
    funding_shortfall_risk: Literal['low', 'medium', 'high'] = Field(default='low')

    # Timeline risks
    installation_delay_risk: Literal['low', 'medium', 'high'] = Field(default='low')
    content_development_risk: Literal['low', 'medium', 'high'] = Field(default='low')

    # External risks
    covid_impact_risk: Literal['low', 'medium', 'high'] = Field(default='medium')
    political_sensitivity_risk: Literal['low', 'medium', 'high'] = Field(default='low')

    # Mitigation strategies
    mitigation_strategies: List[str] = Field(
        default=[],
        description="Strategies to mitigate identified risks"
    )

    # Overall risk level
    overall_risk_level: Literal['low', 'medium', 'high'] = Field(default='medium')
    risk_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Additional risk considerations"
    )


class ExhibitionProposal(BaseModel):
    """
    Complete exhibition proposal - final output of the 3-stage workflow
    """

    # Identification
    id: str = Field(description="Unique proposal identifier")
    session_id: str = Field(description="Source curator session")

    # Core exhibition information
    title: str = Field(min_length=5, max_length=500)
    subtitle: Optional[str] = Field(default=None, max_length=500)

    # Curatorial content
    narrative: str = Field(
        min_length=200,
        max_length=5000,
        description="Main exhibition narrative"
    )

    curatorial_statement: str = Field(
        min_length=100,
        max_length=2000,
        description="Curator's scholarly statement"
    )

    # Content structure
    artworks: List[ArtworkCandidate] = Field(
        min_length=5,
        description="Selected artworks for the exhibition"
    )

    sections: List[ExhibitionSection] = Field(
        min_length=1,
        description="Thematic sections of the exhibition"
    )

    themes: List[str] = Field(
        min_length=1,
        description="Major themes explored"
    )

    # Visitor experience
    visitor_journey: List[VisitorJourneyStep] = Field(
        description="Structured visitor experience"
    )

    target_audience: str = Field(description="Primary target audience")

    estimated_visitor_capacity: Optional[int] = Field(
        default=None,
        ge=1,
        description="Estimated daily visitor capacity"
    )

    # Practical planning
    space_requirements: SpaceRequirements
    budget_breakdown: BudgetBreakdown
    risk_assessment: RiskAssessment

    # Timeline
    recommended_duration: int = Field(
        ge=2,
        le=52,
        description="Recommended exhibition duration in weeks"
    )

    preparation_time_weeks: int = Field(
        ge=8,
        le=104,
        description="Estimated preparation time in weeks"
    )

    # Quick estimates for planning
    budget_estimate: Decimal = Field(gt=0, description="Total budget estimate")
    insurance_estimate: Decimal = Field(gt=0, description="Total insurance value")

    # Feasibility and quality metrics
    feasibility_score: float = Field(
        ge=0,
        le=1,
        description="Overall feasibility score"
    )

    quality_score: float = Field(
        ge=0,
        le=1,
        description="Content quality score"
    )

    innovation_score: float = Field(
        ge=0,
        le=1,
        description="Innovation and uniqueness score"
    )

    # Detailed feasibility analysis
    feasibility_notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Detailed feasibility analysis"
    )

    # Educational and public programming
    educational_opportunities: List[str] = Field(
        default=[],
        description="Educational programs and opportunities"
    )

    public_programs: List[str] = Field(
        default=[],
        description="Public programs and events"
    )

    # Scholarly contribution
    scholarly_significance: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Contribution to art historical scholarship"
    )

    research_opportunities: List[str] = Field(
        default=[],
        description="Research opportunities arising from the exhibition"
    )

    # Approval workflow
    curator_approved: Optional[bool] = Field(default=None)
    director_approved: Optional[bool] = Field(default=None)
    board_approved: Optional[bool] = Field(default=None)

    approval_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Notes from approval process"
    )

    # Version and metadata
    proposal_version: int = Field(default=1, ge=1)
    generated_by_agent: str = Field(description="Agent system version")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Generation metadata
    generation_duration_ms: Optional[int] = None
    agent_confidence: float = Field(ge=0, le=1, description="AI confidence in proposal")

    @field_validator('artworks')
    @classmethod
    def validate_artwork_distribution(cls, v):
        """Ensure reasonable distribution of artworks"""
        if len(v) > 200:
            raise ValueError("Too many artworks for a single exhibition")

        # Check for variety in artists
        artists = set(artwork.artist_name for artwork in v if artwork.artist_name)
        if len(artists) < max(1, len(v) // 10):
            raise ValueError("Exhibition should include works by multiple artists")

        return v

    @field_validator('budget_estimate')
    @classmethod
    def validate_budget_reasonable(cls, v):
        """Ensure budget is reasonable"""
        if v < 1000:
            raise ValueError("Budget too low for a professional exhibition")
        if v > 10000000:  # 10 million EUR
            raise ValueError("Budget unreasonably high")
        return v

    def get_artwork_count(self) -> int:
        """Get total number of artworks"""
        return len(self.artworks)

    def get_artist_count(self) -> int:
        """Get number of unique artists"""
        artists = set(artwork.artist_name for artwork in self.artworks if artwork.artist_name)
        return len(artists)

    def get_average_relevance(self) -> float:
        """Get average relevance score of artworks"""
        if not self.artworks:
            return 0.0

        total_relevance = sum(artwork.relevance_score for artwork in self.artworks)
        return total_relevance / len(self.artworks)

    def get_total_insurance_value(self) -> Decimal:
        """Calculate total insurance value"""
        total = Decimal('0')
        for artwork in self.artworks:
            if artwork.insurance_value:
                # Convert to EUR if necessary
                if artwork.insurance_currency == 'EUR':
                    total += artwork.insurance_value
                # Add currency conversion logic here if needed

        return total

    def get_space_summary(self) -> Dict[str, Any]:
        """Get summary of space requirements"""
        return {
            'minimum_wall_length': self.space_requirements.minimum_wall_length,
            'minimum_floor_area': self.space_requirements.minimum_floor_area,
            'special_requirements': len(self.space_requirements.special_requirements),
            'accessibility_features': sum([
                self.space_requirements.wheelchair_accessible,
                self.space_requirements.audio_description_points > 0,
                self.space_requirements.tactile_elements
            ])
        }


class ProposalComparison(BaseModel):
    """
    Comparison between multiple exhibition proposals
    """

    proposals: List[ExhibitionProposal] = Field(min_length=2, max_length=5)

    # Comparison metrics
    comparison_criteria: List[str] = Field(
        default=['feasibility_score', 'budget_estimate', 'innovation_score'],
        description="Criteria used for comparison"
    )

    # Rankings
    feasibility_ranking: List[str] = Field(
        description="Proposal IDs ranked by feasibility"
    )

    budget_ranking: List[str] = Field(
        description="Proposal IDs ranked by budget (low to high)"
    )

    innovation_ranking: List[str] = Field(
        description="Proposal IDs ranked by innovation"
    )

    # Recommendation
    recommended_proposal_id: str = Field(
        description="ID of recommended proposal"
    )

    recommendation_reasoning: str = Field(
        min_length=100,
        max_length=1000,
        description="Reasoning for recommendation"
    )

    # Comparison timestamp
    compared_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
    'ExhibitionSection',
    'VisitorJourneyStep',
    'SpaceRequirements',
    'BudgetBreakdown',
    'RiskAssessment',
    'ExhibitionProposal',
    'ProposalComparison'
]