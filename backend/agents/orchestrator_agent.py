"""
Orchestrator Agent - Coordinates the 3-stage AI Curator Pipeline
Manages Theme Refinement → Artist Discovery → Artwork Discovery with progress tracking
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import json

from backend.clients.essential_data_client import EssentialDataClient
from backend.agents.theme_refinement_agent import ThemeRefinementAgent, RefinedTheme
from backend.agents.artist_discovery_simple import SimpleArtistDiscovery
from backend.agents.artwork_discovery_agent import ArtworkDiscoveryAgent
from backend.agents.enrichment_agent import ArtworkEnrichmentAgent
from backend.models import CuratorBrief, DiscoveredArtist, ArtworkCandidate
from backend.utils.relevance_scoring import score_artist_relevance

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Pipeline execution stages"""
    VALIDATION = "validation"
    THEME_REFINEMENT = "theme_refinement"
    ARTIST_DISCOVERY = "artist_discovery"
    ARTWORK_DISCOVERY = "artwork_discovery"
    PROPOSAL_GENERATION = "proposal_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStatus(BaseModel):
    """Current pipeline execution status"""
    session_id: str
    current_stage: PipelineStage
    progress_percentage: float = Field(ge=0, le=100)
    status_message: str
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Stage-specific data
    refined_theme: Optional[RefinedTheme] = None
    discovered_artists: List[DiscoveredArtist] = Field(default_factory=list)
    discovered_artworks: List[ArtworkCandidate] = Field(default_factory=list)

    # Metrics
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ExhibitionProposal(BaseModel):
    """Complete exhibition proposal output"""
    session_id: str

    # Core exhibition data
    exhibition_title: str
    subtitle: Optional[str] = None
    curatorial_statement: str
    scholarly_rationale: str

    # Content
    refined_theme: RefinedTheme
    selected_artists: List[DiscoveredArtist]
    selected_artworks: List[ArtworkCandidate]

    # Exhibition parameters
    target_audience: str
    complexity_level: str
    estimated_duration: str
    space_recommendations: List[str]

    # Quality metrics
    overall_quality_score: float = Field(ge=0, le=1)
    content_metrics: Dict[str, Any]

    # Practical information
    loan_requirements: List[str] = Field(default_factory=list)
    feasibility_notes: str = ""

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: float


class OrchestratorAgent:
    """
    Orchestrates the complete 3-stage AI curator pipeline

    Features:
    - Sequential stage execution with progress tracking
    - Error handling and recovery
    - Progress callbacks for real-time updates
    - Configurable parameters per stage
    - Comprehensive metrics collection
    """

    def __init__(
        self,
        data_client: EssentialDataClient,
        openai_api_key: Optional[str] = None,
        progress_callback: Optional[Callable[[PipelineStatus], None]] = None,
        session_manager: Optional[Any] = None  # SessionManager for interactive mode
    ):
        self.data_client = data_client
        self.progress_callback = progress_callback
        self.session_manager = session_manager

        # Initialize OpenAI client for LLM-enhanced artist scoring
        try:
            from openai import OpenAI
            import os
            api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
            self.openai_client = OpenAI(api_key=api_key) if api_key else None
        except ImportError:
            logger.warning("OpenAI SDK not installed - artist scoring will use heuristics only")
            self.openai_client = None

        # Initialize stage agents with OpenAI support
        self.theme_agent = ThemeRefinementAgent(data_client, openai_api_key)
        self.artwork_agent = ArtworkDiscoveryAgent(data_client, openai_api_key)
        self.enrichment_agent = ArtworkEnrichmentAgent()
        # Note: We create SimpleArtistDiscovery per-pipeline for better reliability

        logger.info("OrchestratorAgent initialized")

    async def execute_pipeline(
        self,
        curator_brief: CuratorBrief,
        session_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ExhibitionProposal:
        """
        Execute the complete 3-stage pipeline

        Args:
            curator_brief: Input from curator
            session_id: Unique session identifier
            config: Optional configuration overrides
                {
                    'max_artists': 15,
                    'max_artworks': 50,
                    'min_artist_relevance': 0.5,
                    'min_artwork_relevance': 0.4,
                    'prioritize_diversity': True,
                    'diversity_targets': {'min_female': 5, 'min_non_western': 3}
                }

        Returns:
            Complete ExhibitionProposal
        """
        start_time = datetime.utcnow()

        # Default configuration
        default_config = {
            'max_artists': 15,
            'max_artworks': 50,
            'artworks_per_artist': 5,
            'min_artist_relevance': 0.5,
            'min_artwork_relevance': 0.4,
            'prioritize_diversity': True,
            'diversity_targets': {'min_female': 5, 'min_non_western': 3}
        }

        config = {**default_config, **(config or {})}

        # Initialize status
        status = PipelineStatus(
            session_id=session_id,
            current_stage=PipelineStage.VALIDATION,
            progress_percentage=0,
            status_message="Starting pipeline execution",
            started_at=start_time,
            updated_at=start_time
        )

        try:
            # STAGE 0: Validation (5%)
            await self._update_progress(status, PipelineStage.VALIDATION, 5, "Validating curator brief")
            logger.info(f"Session {session_id}: Validating curator brief")

            # STAGE 1: Theme Refinement (25%)
            await self._update_progress(status, PipelineStage.THEME_REFINEMENT, 10, "Refining exhibition theme")
            logger.info(f"Session {session_id}: Starting theme refinement")

            refined_theme = await self.theme_agent.refine_theme(curator_brief, session_id)
            status.refined_theme = refined_theme
            status.metrics['theme_confidence'] = refined_theme.refinement_confidence
            status.metrics['validated_concepts'] = len(refined_theme.validated_concepts)

            await self._update_progress(status, PipelineStage.THEME_REFINEMENT, 25,
                f"Theme refined: {refined_theme.exhibition_title}")
            logger.info(f"Session {session_id}: Theme refined with {len(refined_theme.validated_concepts)} concepts")

            # STAGE 2: Artist Discovery (55%) - Using simple Wikipedia-based approach
            await self._update_progress(status, PipelineStage.ARTIST_DISCOVERY, 30,
                "Discovering relevant artists via Wikipedia")
            logger.info(f"Session {session_id}: Starting simple artist discovery (target: {config['max_artists']} artists)")

            # Use simple Wikipedia-based discovery (much faster and more reliable)
            simple_discoverer = SimpleArtistDiscovery(self.data_client)
            raw_artists = await simple_discoverer.discover_artists(
                refined_theme=refined_theme,
                reference_artists=curator_brief.reference_artists or [],
                max_artists=config['max_artists'] * 2  # Get 2x for filtering
            )

            # Convert to DiscoveredArtist objects with calculated relevance scores
            discovered_artists = []
            # Extract concept names from validated concepts (could be Pydantic objects or dicts)
            theme_concepts = []
            for c in refined_theme.validated_concepts:
                if hasattr(c, 'concept'):
                    # Pydantic ConceptValidation object
                    theme_concepts.append(c.concept)
                elif isinstance(c, dict):
                    theme_concepts.append(c.get('concept', c.get('name', '')))
                else:
                    theme_concepts.append(str(c))

            for artist_data in raw_artists[:config['max_artists']]:
                # Calculate relevance score using LLM (with heuristic fallback)
                relevance_score, relevance_reasoning = await self._score_artist_with_llm(
                    artist_data=artist_data,
                    refined_theme=refined_theme,
                    reference_artists=curator_brief.reference_artists
                )

                discovered_artist = DiscoveredArtist(
                    name=artist_data['name'],
                    birth_year=artist_data.get('birth_year'),
                    death_year=artist_data.get('death_year'),
                    nationality=None,
                    movements=[],
                    biography=artist_data.get('description', ''),
                    known_works_count=None,
                    wikidata_id=artist_data.get('wikidata_id'),
                    getty_ulan_id=None,
                    source_endpoint='wikipedia',
                    discovery_confidence=relevance_score,  # Use calculated score
                    relevance_score=relevance_score,
                    relevance_reasoning=relevance_reasoning,
                    raw_data=artist_data
                )
                discovered_artists.append(discovered_artist)

            status.discovered_artists = discovered_artists
            status.metrics['total_artists'] = len(discovered_artists)
            status.metrics['avg_artist_relevance'] = (
                sum(a.relevance_score for a in discovered_artists) / len(discovered_artists)
                if discovered_artists else 0
            )

            await self._update_progress(status, PipelineStage.ARTIST_DISCOVERY, 55,
                f"Discovered {len(discovered_artists)} artists")
            logger.info(f"Session {session_id}: Discovered {len(discovered_artists)} artists")

            if not discovered_artists:
                raise ValueError("No artists found - theme may be too specific or abstract")

            # CURATOR SELECTION POINT 1: Artist Selection
            if self.session_manager:
                # Interactive mode - pause for curator selection
                logger.info(f"Session {session_id}: Pausing for curator artist selection")
                selected_artists = await self.session_manager.set_artist_candidates(
                    session_id,
                    discovered_artists
                )
                logger.info(f"Session {session_id}: Curator selected {len(selected_artists)} artists")
            else:
                # Automatic mode - use all discovered artists
                selected_artists = discovered_artists

            # STAGE 3: Artwork Discovery (90%)
            await self._update_progress(status, PipelineStage.ARTWORK_DISCOVERY, 60,
                "Discovering artworks from selected artists")
            logger.info(f"Session {session_id}: Starting artwork discovery (target: {config['max_artworks']} artworks)")

            discovered_artworks = await self.artwork_agent.discover_artworks(
                refined_theme=refined_theme,
                selected_artists=selected_artists,  # Use curator-selected artists
                session_id=session_id,
                max_artworks=config['max_artworks'] * 2,  # Get 2x candidates for selection
                min_relevance=config['min_artwork_relevance'],
                artworks_per_artist=config['artworks_per_artist']
            )

            status.discovered_artworks = discovered_artworks
            status.metrics['total_artworks'] = len(discovered_artworks)
            status.metrics['avg_artwork_relevance'] = (
                sum(a.relevance_score for a in discovered_artworks) / len(discovered_artworks)
                if discovered_artworks else 0
            )

            await self._update_progress(status, PipelineStage.ARTWORK_DISCOVERY, 90,
                f"Discovered {len(discovered_artworks)} artworks")
            logger.info(f"Session {session_id}: Discovered {len(discovered_artworks)} artworks")

            if not discovered_artworks:
                raise ValueError("No artworks found - check artist discovery and data sources")

            # CURATOR SELECTION POINT 2: Artwork Selection
            if self.session_manager:
                # Interactive mode - pause for curator selection
                logger.info(f"Session {session_id}: Pausing for curator artwork selection")
                selected_artworks = await self.session_manager.set_artwork_candidates(
                    session_id,
                    discovered_artworks
                )
                logger.info(f"Session {session_id}: Curator selected {len(selected_artworks)} artworks")
            else:
                # Automatic mode - use top artworks
                selected_artworks = discovered_artworks[:config['max_artworks']]

            # STAGE 3.5: Enrichment - Brave Search for missing data (93%)
            await self._update_progress(status, PipelineStage.ARTWORK_DISCOVERY, 93,
                "Enriching artwork metadata with web search")
            logger.info(f"Session {session_id}: Enriching {len(selected_artworks)} artworks with Brave Search")

            enriched_artworks = await self.enrichment_agent.enrich_artworks(
                selected_artworks,
                max_concurrent=3
            )

            logger.info(f"Session {session_id}: Enrichment complete")

            # STAGE 4: Proposal Generation (100%)
            await self._update_progress(status, PipelineStage.PROPOSAL_GENERATION, 95,
                "Generating exhibition proposal")
            logger.info(f"Session {session_id}: Generating final proposal")

            proposal = await self._generate_proposal(
                session_id=session_id,
                refined_theme=refined_theme,
                discovered_artists=selected_artists,  # Use curator-selected artists
                discovered_artworks=enriched_artworks,  # Use enriched artworks
                start_time=start_time
            )

            # Complete
            status.current_stage = PipelineStage.COMPLETED
            status.progress_percentage = 100
            status.status_message = "Exhibition proposal complete"
            status.completed_at = datetime.utcnow()
            await self._send_progress(status)

            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Session {session_id}: Pipeline completed in {processing_time:.2f}s")

            return proposal

        except Exception as e:
            logger.error(f"Session {session_id}: Pipeline failed: {e}", exc_info=True)
            status.current_stage = PipelineStage.FAILED
            status.error_message = str(e)
            status.completed_at = datetime.utcnow()
            await self._send_progress(status)
            raise

    async def _generate_proposal(
        self,
        session_id: str,
        refined_theme: RefinedTheme,
        discovered_artists: List[DiscoveredArtist],
        discovered_artworks: List[ArtworkCandidate],
        start_time: datetime
    ) -> ExhibitionProposal:
        """Generate the final exhibition proposal"""

        # Calculate quality metrics
        overall_quality = self._calculate_overall_quality(
            refined_theme, discovered_artists, discovered_artworks
        )

        # Generate loan requirements
        loan_requirements = self._generate_loan_requirements(discovered_artworks)

        # Generate feasibility notes
        feasibility_notes = self._generate_feasibility_notes(
            discovered_artists, discovered_artworks
        )

        # Compile metrics
        content_metrics = {
            'total_artists': len(discovered_artists),
            'total_artworks': len(discovered_artworks),
            'artists_represented': len(set(a.artist_name for a in discovered_artworks)),
            'avg_artist_relevance': sum(a.relevance_score for a in discovered_artists) / len(discovered_artists),
            'avg_artwork_relevance': sum(a.relevance_score for a in discovered_artworks) / len(discovered_artworks),
            'avg_completeness': sum(a.completeness_score for a in discovered_artworks) / len(discovered_artworks),
            'with_iiif': sum(1 for a in discovered_artworks if a.iiif_manifest),
            'with_images': sum(1 for a in discovered_artworks if a.thumbnail_url or a.high_res_images),
            'with_dimensions': sum(1 for a in discovered_artworks if a.height_cm and a.width_cm),
            'theme_confidence': refined_theme.refinement_confidence
        }

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        proposal = ExhibitionProposal(
            session_id=session_id,
            exhibition_title=refined_theme.exhibition_title,
            subtitle=refined_theme.subtitle,
            curatorial_statement=refined_theme.curatorial_statement,
            scholarly_rationale=refined_theme.scholarly_rationale,
            refined_theme=refined_theme,
            selected_artists=discovered_artists,
            selected_artworks=discovered_artworks,
            target_audience=refined_theme.target_audience_refined,
            complexity_level=refined_theme.complexity_level,
            estimated_duration=refined_theme.estimated_duration,
            space_recommendations=refined_theme.space_recommendations,
            overall_quality_score=overall_quality,
            content_metrics=content_metrics,
            loan_requirements=loan_requirements,
            feasibility_notes=feasibility_notes,
            processing_time_seconds=processing_time
        )

        return proposal

    async def _score_artist_with_llm(
        self,
        artist_data: Dict[str, Any],
        refined_theme: RefinedTheme,
        reference_artists: List[str]
    ) -> Tuple[float, str]:
        """
        Score artist relevance using OpenAI GPT-4 with Museum Van Bommel Van Dam expertise

        Returns:
            (score, reasoning) tuple where score is 0.0-1.0
        """
        if not self.openai_client:
            # Fallback to heuristic scoring
            from backend.utils.relevance_scoring import score_artist_relevance
            theme_concepts = [c.refined_concept for c in refined_theme.validated_concepts]
            return score_artist_relevance(artist_data, theme_concepts, reference_artists)

        try:
            artist_name = artist_data.get('name', 'Unknown Artist')
            artist_bio = artist_data.get('description', 'No description available')
            birth_year = artist_data.get('birth_year', 'Unknown')
            death_year = artist_data.get('death_year', 'Unknown')

            # Build context
            concepts_str = ', '.join([c.refined_concept for c in refined_theme.validated_concepts[:5]])
            reference_str = ', '.join(reference_artists[:3]) if reference_artists else 'Various modern artists'

            prompt = f"""You are a curator at Museum Van Bommel Van Dam evaluating artists for an exhibition.

Museum Van Bommel Van Dam's Expertise:
- We specialize in modern and contemporary art (1900-present)
- Our collection strengths: geometric abstraction, De Stijl, Dutch modernism, conceptual art
- We seek artists whose work challenges conventional seeing
- We value both historical significance and contemporary relevance
- We prioritize artists whose work connects to our collection and regional identity

Exhibition Context:
Title: {refined_theme.exhibition_title}
Theme Concepts: {concepts_str}
Reference Artists: {reference_str}
Target Audience: {refined_theme.target_audience_refined}

Artist to Evaluate:
Name: {artist_name}
Birth-Death: {birth_year} - {death_year}
Biography: {artist_bio[:400]}

Task:
Evaluate this artist's relevance to OUR exhibition at Museum Van Bommel Van Dam.

Consider:
1. Does their work align with modern/contemporary art (our specialty)?
2. Do they work in relevant movements/styles (abstract, geometric, conceptual)?
3. Are they active in the right time period for this theme?
4. Would their work complement our collection and exhibition goals?
5. Is this a serious fine artist (not graphic designer, illustrator, etc.)?

Be CRITICAL. Many candidates will be marginally relevant or wrong.
- Score 0.0-0.3: Not relevant (wrong period, wrong medium, wrong style)
- Score 0.4-0.6: Moderate relevance (some connection but not strong)
- Score 0.7-0.9: Strong relevance (clear fit with theme and museum)
- Score 0.9-1.0: Exceptional relevance (perfect fit, reference-quality artist)

Format your response EXACTLY as:
SCORE: [0.0 to 1.0]
REASONING: [2-3 sentences explaining your evaluation]"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=250,
                temperature=0.3,  # Conservative for evaluation
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.choices[0].message.content.strip()

            # Parse response
            score = 0.5  # Default fallback
            reasoning = f"{artist_name} shows moderate relevance to exhibition theme."

            if "SCORE:" in response_text:
                score_line = response_text.split("SCORE:")[1].split("\n")[0].strip()
                try:
                    score = float(score_line)
                    score = max(0.0, min(1.0, score))  # Clamp to 0-1
                except:
                    logger.warning(f"Failed to parse LLM score: {score_line}")

            if "REASONING:" in response_text:
                reasoning = response_text.split("REASONING:")[1].strip()

            logger.debug(f"LLM scored '{artist_name}': {score:.2f}")
            return score, reasoning

        except Exception as e:
            logger.warning(f"LLM artist scoring failed for {artist_data.get('name')}: {e}, using heuristic fallback")
            # Fallback to heuristic
            from backend.utils.relevance_scoring import score_artist_relevance
            theme_concepts = [c.refined_concept for c in refined_theme.validated_concepts]
            return score_artist_relevance(artist_data, theme_concepts, reference_artists)

    def _calculate_overall_quality(
        self,
        theme: RefinedTheme,
        artists: List[DiscoveredArtist],
        artworks: List[ArtworkCandidate]
    ) -> float:
        """Calculate overall exhibition quality score"""

        # Theme quality (20%)
        theme_score = theme.refinement_confidence * 0.2

        # Artist quality (30%)
        avg_artist_relevance = sum(a.relevance_score for a in artists) / len(artists)
        artist_score = avg_artist_relevance * 0.3

        # Artwork quality (30%)
        avg_artwork_relevance = sum(a.relevance_score for a in artworks) / len(artworks)
        artwork_score = avg_artwork_relevance * 0.3

        # Completeness (20%)
        avg_completeness = sum(a.completeness_score for a in artworks) / len(artworks)
        completeness_score = avg_completeness * 0.2

        overall = theme_score + artist_score + artwork_score + completeness_score
        return round(overall, 2)

    def _generate_loan_requirements(self, artworks: List[ArtworkCandidate]) -> List[str]:
        """Generate list of loan requirements"""
        requirements = []

        # Group by institution
        by_institution = {}
        for artwork in artworks:
            if artwork.institution_name:
                inst = artwork.institution_name
                if inst not in by_institution:
                    by_institution[inst] = []
                by_institution[inst].append(artwork)

        for institution, works in by_institution.items():
            requirements.append(
                f"Contact {institution} for loan of {len(works)} artwork(s)"
            )

        # Add general requirements
        if artworks:
            requirements.append("Insurance coverage required for all loans")
            requirements.append("Climate-controlled transport and handling")
            requirements.append("Security requirements for high-value works")

        return requirements[:10]  # Limit to top 10

    def _generate_feasibility_notes(
        self,
        artists: List[DiscoveredArtist],
        artworks: List[ArtworkCandidate]
    ) -> str:
        """Generate feasibility assessment"""
        notes = []

        # Artist representation
        notes.append(f"Exhibition features {len(artists)} artists spanning diverse backgrounds and periods.")

        # Artwork availability
        available_count = sum(1 for a in artworks if a.loan_available)
        if available_count > 0:
            notes.append(f"{available_count} artworks have confirmed loan availability.")

        # Data quality
        avg_completeness = sum(a.completeness_score for a in artworks) / len(artworks)
        if avg_completeness > 0.7:
            notes.append("High-quality metadata available for most works, facilitating planning.")

        # Digital assets
        with_iiif = sum(1 for a in artworks if a.iiif_manifest)
        if with_iiif > 0:
            notes.append(f"{with_iiif} works have IIIF manifests available for digital displays.")

        return " ".join(notes)

    async def _update_progress(
        self,
        status: PipelineStatus,
        stage: PipelineStage,
        percentage: float,
        message: str
    ):
        """Update pipeline progress"""
        status.current_stage = stage
        status.progress_percentage = percentage
        status.status_message = message
        status.updated_at = datetime.utcnow()
        await self._send_progress(status)

    async def _send_progress(self, status: PipelineStatus):
        """Send progress update via callback"""
        if self.progress_callback:
            try:
                if asyncio.iscoroutinefunction(self.progress_callback):
                    await self.progress_callback(status)
                else:
                    self.progress_callback(status)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")


__all__ = ['OrchestratorAgent', 'PipelineStage', 'PipelineStatus', 'ExhibitionProposal']
