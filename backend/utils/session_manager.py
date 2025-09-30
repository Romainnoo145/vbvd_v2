"""
Session State Manager for Interactive Curator Workflow
Manages session state for curator selection points in the pipeline
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from backend.models import DiscoveredArtist, ArtworkCandidate
from backend.agents.theme_refinement_agent import RefinedTheme

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Pipeline execution states"""
    STARTING = "starting"
    THEME_REFINEMENT = "theme_refinement"
    DISCOVERING_ARTISTS = "discovering_artists"
    AWAITING_ARTIST_SELECTION = "awaiting_artist_selection"
    DISCOVERING_ARTWORKS = "discovering_artworks"
    AWAITING_ARTWORK_SELECTION = "awaiting_artwork_selection"
    ENRICHING = "enriching"
    GENERATING_PROPOSAL = "generating_proposal"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class CuratorSession:
    """
    Session data for a curator workflow
    Stores intermediate results and selection state
    """
    session_id: str
    state: SessionState
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Progress tracking
    progress_percentage: float = 0.0
    status_message: str = ""
    error_message: Optional[str] = None

    # Pipeline data
    refined_theme: Optional[RefinedTheme] = None
    artist_candidates: List[DiscoveredArtist] = field(default_factory=list)
    selected_artists: List[DiscoveredArtist] = field(default_factory=list)
    artwork_candidates: List[ArtworkCandidate] = field(default_factory=list)
    selected_artworks: List[ArtworkCandidate] = field(default_factory=list)

    # Final output
    proposal: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[Dict[str, Any]] = None

    # Selection events
    artist_selection_event: Optional[asyncio.Event] = field(default=None)
    artwork_selection_event: Optional[asyncio.Event] = field(default=None)

    def __post_init__(self):
        """Initialize async events"""
        if self.artist_selection_event is None:
            self.artist_selection_event = asyncio.Event()
        if self.artwork_selection_event is None:
            self.artwork_selection_event = asyncio.Event()

    def update(
        self,
        state: Optional[SessionState] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None
    ):
        """Update session state"""
        if state:
            self.state = state
        if progress is not None:
            self.progress_percentage = progress
        if message:
            self.status_message = message
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to API-friendly dict"""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "progress": self.progress_percentage,
            "message": self.status_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error_message,

            # Include candidates if awaiting selection
            "artist_candidates": [
                {
                    "name": a.name,
                    "birth_year": a.birth_year,
                    "death_year": a.death_year,
                    "relevance_score": a.relevance_score,
                    "relevance_reasoning": a.relevance_reasoning,
                    "biography": a.biography[:200] if a.biography else None,
                    "is_diverse": a.raw_data.get('is_diverse', False) if hasattr(a, 'raw_data') else False,
                    "gender": a.raw_data.get('gender', 'unknown') if hasattr(a, 'raw_data') else 'unknown'
                }
                for a in self.artist_candidates
            ] if self.state == SessionState.AWAITING_ARTIST_SELECTION else [],

            "artwork_candidates": [
                {
                    "title": a.title,
                    "artist_name": a.artist_name,
                    "date_created_earliest": a.date_created_earliest,
                    "relevance_score": a.relevance_score,
                    "completeness_score": a.completeness_score,
                    "iiif_manifest": a.iiif_manifest,
                    "thumbnail_url": a.thumbnail_url,
                    "medium": a.medium,
                    "institution_name": a.institution_name
                }
                for a in self.artwork_candidates
            ] if self.state == SessionState.AWAITING_ARTWORK_SELECTION else [],

            # Include final results if complete
            "proposal": self.proposal if self.state == SessionState.COMPLETE else None,
            "quality_metrics": self.quality_metrics if self.state == SessionState.COMPLETE else None
        }


class SessionManager:
    """
    Manages curator sessions
    In-memory storage for now (can migrate to Redis later)
    """

    def __init__(self):
        self.sessions: Dict[str, CuratorSession] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, session_id: str) -> CuratorSession:
        """Create a new curator session"""
        async with self._lock:
            session = CuratorSession(
                session_id=session_id,
                state=SessionState.STARTING
            )
            self.sessions[session_id] = session
            logger.info(f"Created session {session_id}")
            return session

    async def get_session(self, session_id: str) -> Optional[CuratorSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    async def update_session(
        self,
        session_id: str,
        state: Optional[SessionState] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        **kwargs
    ) -> Optional[CuratorSession]:
        """Update session state"""
        async with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return None

            session.update(state, progress, message)

            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            logger.debug(f"Updated session {session_id}: {state} - {message}")
            return session

    async def set_artist_candidates(
        self,
        session_id: str,
        candidates: List[DiscoveredArtist]
    ):
        """Set artist candidates and wait for selection"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.artist_candidates = candidates
        session.update(
            state=SessionState.AWAITING_ARTIST_SELECTION,
            progress=35.0,
            message=f"Found {len(candidates)} artist candidates. Please review and select."
        )

        logger.info(f"Session {session_id}: Awaiting artist selection ({len(candidates)} candidates)")

        # Wait for curator selection
        await session.artist_selection_event.wait()

        logger.info(f"Session {session_id}: Artist selection received ({len(session.selected_artists)} selected)")
        return session.selected_artists

    async def select_artists(
        self,
        session_id: str,
        selected_indices: List[int]
    ) -> List[DiscoveredArtist]:
        """Curator selects artists"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.state != SessionState.AWAITING_ARTIST_SELECTION:
            raise ValueError(f"Session {session_id} not awaiting artist selection (state: {session.state})")

        # Validate indices
        if not selected_indices:
            raise ValueError("No artists selected")

        if max(selected_indices) >= len(session.artist_candidates):
            raise ValueError(f"Invalid index: max index {max(selected_indices)} >= {len(session.artist_candidates)}")

        # Store selected artists
        session.selected_artists = [
            session.artist_candidates[i] for i in selected_indices
        ]

        # Signal the pipeline to continue
        session.artist_selection_event.set()

        logger.info(f"Session {session_id}: {len(session.selected_artists)} artists selected")
        return session.selected_artists

    async def set_artwork_candidates(
        self,
        session_id: str,
        candidates: List[ArtworkCandidate]
    ):
        """Set artwork candidates and wait for selection"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.artwork_candidates = candidates
        session.update(
            state=SessionState.AWAITING_ARTWORK_SELECTION,
            progress=70.0,
            message=f"Found {len(candidates)} artwork candidates. Please review and select."
        )

        logger.info(f"Session {session_id}: Awaiting artwork selection ({len(candidates)} candidates)")

        # Wait for curator selection
        await session.artwork_selection_event.wait()

        logger.info(f"Session {session_id}: Artwork selection received ({len(session.selected_artworks)} selected)")
        return session.selected_artworks

    async def select_artworks(
        self,
        session_id: str,
        selected_indices: List[int]
    ) -> List[ArtworkCandidate]:
        """Curator selects artworks"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.state != SessionState.AWAITING_ARTWORK_SELECTION:
            raise ValueError(f"Session {session_id} not awaiting artwork selection (state: {session.state})")

        # Validate indices
        if not selected_indices:
            raise ValueError("No artworks selected")

        if max(selected_indices) >= len(session.artwork_candidates):
            raise ValueError(f"Invalid index: max index {max(selected_indices)} >= {len(session.artwork_candidates)}")

        # Store selected artworks
        session.selected_artworks = [
            session.artwork_candidates[i] for i in selected_indices
        ]

        # Signal the pipeline to continue
        session.artwork_selection_event.set()

        logger.info(f"Session {session_id}: {len(session.selected_artworks)} artworks selected")
        return session.selected_artworks

    async def set_complete(
        self,
        session_id: str,
        proposal: Dict[str, Any],
        quality_metrics: Dict[str, Any]
    ):
        """Mark session as complete"""
        session = await self.update_session(
            session_id,
            state=SessionState.COMPLETE,
            progress=100.0,
            message="Exhibition proposal complete",
            proposal=proposal,
            quality_metrics=quality_metrics
        )
        logger.info(f"Session {session_id}: Completed with quality score {quality_metrics.get('overall_quality_score', 0):.2f}")
        return session

    async def set_failed(self, session_id: str, error: str):
        """Mark session as failed"""
        session = await self.update_session(
            session_id,
            state=SessionState.FAILED,
            message="Pipeline failed",
            error_message=error
        )
        logger.error(f"Session {session_id}: Failed - {error}")
        return session

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours"""
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        to_remove = [
            sid for sid, session in self.sessions.items()
            if session.created_at.timestamp() < cutoff
        ]

        for sid in to_remove:
            del self.sessions[sid]
            logger.info(f"Cleaned up old session {sid}")

        return len(to_remove)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


__all__ = ['SessionManager', 'SessionState', 'CuratorSession', 'get_session_manager']
