"""
Backend Models Module
Pydantic models for the AI Curator Assistant 3-stage workflow
"""

from .curator_brief import (
    CuratorBrief,
    ThemeValidation,
    ArtistValidation,
    ValidationReport,
    EnrichedQuery
)

from .discovery import (
    DiscoveredArtist,
    ArtworkCandidate,
    ArtworkCollection
)

from .exhibition import (
    ExhibitionSection,
    VisitorJourneyStep,
    SpaceRequirements,
    BudgetBreakdown,
    RiskAssessment,
    ExhibitionProposal,
    ProposalComparison
)

__all__ = [
    # Curator input and validation
    'CuratorBrief',
    'ThemeValidation',
    'ArtistValidation',
    'ValidationReport',
    'EnrichedQuery',

    # Discovery stage outputs
    'DiscoveredArtist',
    'ArtworkCandidate',
    'ArtworkCollection',

    # Exhibition proposal
    'ExhibitionSection',
    'VisitorJourneyStep',
    'SpaceRequirements',
    'BudgetBreakdown',
    'RiskAssessment',
    'ExhibitionProposal',
    'ProposalComparison'
]