"""
FastAPI Backend - Main Application
Provides REST and WebSocket endpoints for the AI Curator Assistant
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from backend.agents.orchestrator_agent import (
    OrchestratorAgent,
    PipelineStatus,
    ExhibitionProposal
)
from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief
from backend.utils.session_manager import get_session_manager, SessionState

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# WebSocket Connection Manager
class WebSocketManager:
    """Manages WebSocket connections for real-time progress updates"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")

    async def send_progress(self, session_id: str, status: PipelineStatus):
        """
        Send progress update to connected client

        Supports progressive streaming: sends stage completion data when available
        """
        if session_id in self.active_connections:
            try:
                # Check if this is a stage completion event
                if status.stage_completed:
                    # Progressive streaming: send stage completion with data
                    message = {
                        "type": "stage_complete",
                        "session_id": status.session_id,
                        "completed_stage": status.stage_completed.value,
                        "stage": status.current_stage.value,
                        "progress": status.progress_percentage,
                        "message": status.status_message,
                        "updated_at": status.updated_at.isoformat()
                    }

                    # Add stage-specific data
                    if status.stage_completed == "theme_refinement" and status.refined_theme:
                        message["data"] = {
                            "exhibition_title": status.refined_theme.exhibition_title,
                            "subtitle": status.refined_theme.subtitle,
                            "curatorial_statement": status.refined_theme.curatorial_statement,
                            "scholarly_rationale": status.refined_theme.scholarly_rationale,
                            "target_audience_refined": status.refined_theme.target_audience_refined,
                            "complexity_level": status.refined_theme.complexity_level
                        }
                    elif status.stage_completed == "artist_discovery" and status.discovered_artists:
                        message["data"] = {
                            "artists": [
                                {
                                    "name": a.name,
                                    "wikidata_id": a.wikidata_id,
                                    "birth_year": a.birth_year,
                                    "death_year": a.death_year,
                                    "relevance_score": a.relevance_score,
                                    "relevance_reasoning": a.relevance_reasoning
                                }
                                for a in status.discovered_artists
                            ]
                        }
                    elif status.stage_completed == "artwork_discovery" and status.discovered_artworks:
                        message["data"] = {
                            "artworks": [
                                {
                                    "uri": a.uri,
                                    "title": a.title,
                                    "artist_name": a.artist_name,
                                    "date_created": a.date_created,
                                    "medium": a.medium,
                                    "institution_name": a.institution_name,
                                    "iiif_manifest": a.iiif_manifest,
                                    "thumbnail_url": a.thumbnail_url,
                                    "relevance_score": a.relevance_score,
                                    "relevance_reasoning": a.relevance_reasoning,
                                    "height_cm": a.height_cm,
                                    "width_cm": a.width_cm
                                }
                                for a in status.discovered_artworks
                            ]
                        }

                    await self.active_connections[session_id].send_json(message)
                else:
                    # Regular progress update
                    await self.active_connections[session_id].send_json({
                        "type": "progress",
                        "session_id": status.session_id,
                        "stage": status.current_stage.value,
                        "progress": status.progress_percentage,
                        "message": status.status_message,
                        "updated_at": status.updated_at.isoformat()
                    })
            except Exception as e:
                logger.error(f"Failed to send progress to {session_id}: {e}")
                self.disconnect(session_id)


# Global state
websocket_manager = WebSocketManager()
processing_tasks: Dict[str, asyncio.Task] = {}
proposals: Dict[str, ExhibitionProposal] = {}


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    logger.info("AI Curator Assistant API starting up")
    yield
    logger.info("AI Curator Assistant API shutting down")


# Create FastAPI app
app = FastAPI(
    title="AI Curator Assistant API",
    description="Backend API for AI-powered exhibition curation",
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class CuratorBriefRequest(BaseModel):
    """Request model for submitting curator brief"""
    curator_brief: CuratorBrief
    config: Optional[Dict] = Field(default=None)


class SessionStatusResponse(BaseModel):
    """Response model for session status"""
    session_id: str
    status: str
    progress: float
    message: str
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class SubmitResponse(BaseModel):
    """Response model for brief submission"""
    session_id: str
    message: str
    websocket_url: str


class SelectionRequest(BaseModel):
    """Request model for artist/artwork selection"""
    selected_indices: List[int] = Field(
        description="List of selected item indices (0-based)"
    )


class SelectionResponse(BaseModel):
    """Response model for selection"""
    session_id: str
    message: str
    selected_count: int


class RefineRequest(BaseModel):
    """Request model for re-refining theme"""
    feedback: str = Field(description="User's feedback for theme refinement")


class RefineResponse(BaseModel):
    """Response model for theme refinement"""
    session_id: str
    message: str
    iteration_count: int
    theme: Dict


class ContinueRequest(BaseModel):
    """Request model for continuing to next phase"""
    phase: str = Field(description="Next phase: 'artist_discovery' or 'artwork_discovery'")


class ContinueResponse(BaseModel):
    """Response model for phase continuation"""
    session_id: str
    message: str
    next_phase: str
    websocket_url: str


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Curator Assistant API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/categories")
async def get_categories():
    """
    Get all available categories for the exhibition form

    Returns structured data for time periods, art movements, and media types
    that match the europeana_topics.py backend configuration.
    """
    from backend.config.europeana_topics import TIME_PERIODS, ART_MOVEMENTS, MEDIA_TYPES

    def make_label(key: str) -> str:
        """Convert snake_case key to Title Case label"""
        return key.replace('_', ' ').title()

    # Van Bommel focus media types (contemporary art museum)
    priority_media = {'sculpture', 'installation', 'mixed_media', 'photography', 'video_art', 'performance_art'}

    # Transform TIME_PERIODS dict into frontend-friendly format
    time_periods = [
        {
            "value": key,
            "label": make_label(key),
            "years": {"start": value["start"], "end": value["end"]}
        }
        for key, value in TIME_PERIODS.items()
    ]

    # Transform ART_MOVEMENTS dict into frontend-friendly format
    art_movements = [
        {
            "value": key,
            "label": make_label(key),
            "search_terms": value  # value is already a list
        }
        for key, value in ART_MOVEMENTS.items()
    ]

    # Transform MEDIA_TYPES dict into frontend-friendly format
    media_types = [
        {
            "value": key,
            "label": make_label(key),
            "search_terms": value,  # value is already a list
            "priority": key in priority_media
        }
        for key, value in MEDIA_TYPES.items()
    ]

    return {
        "time_periods": time_periods,
        "art_movements": art_movements,
        "media_types": media_types
    }


@app.post("/api/curator/submit", response_model=SubmitResponse)
async def submit_curator_brief(request: CuratorBriefRequest):
    """
    Submit a curator brief for processing

    Supports phase-specific execution via config.phase:
    - "theme_only": Only refine theme and stop (fast, 15-30s)
    - "full": Execute complete pipeline (default)

    Returns session ID and WebSocket URL for progress tracking
    """
    try:
        # Generate session ID
        session_id = f"session-{datetime.utcnow().timestamp()}"

        logger.info(f"Received curator brief for session {session_id}")

        # Start background processing task
        task = asyncio.create_task(
            process_curator_brief(session_id, request.curator_brief, request.config)
        )
        processing_tasks[session_id] = task

        return SubmitResponse(
            session_id=session_id,
            message="Processing started",
            websocket_url=f"/ws/{session_id}"
        )

    except Exception as e:
        logger.error(f"Failed to submit curator brief: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Get current status of a processing session
    Returns full session data including candidates when awaiting selection
    """
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()


@app.post("/api/sessions/{session_id}/select-artists", response_model=SelectionResponse)
async def select_artists(session_id: str, request: SelectionRequest):
    """
    Submit artist selection for curator review
    """
    try:
        session_manager = get_session_manager()
        selected = await session_manager.select_artists(session_id, request.selected_indices)

        return SelectionResponse(
            session_id=session_id,
            message=f"Selected {len(selected)} artists. Proceeding to artwork discovery.",
            selected_count=len(selected)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to select artists for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/select-artworks", response_model=SelectionResponse)
async def select_artworks(session_id: str, request: SelectionRequest):
    """
    Submit artwork selection for curator review
    """
    try:
        session_manager = get_session_manager()
        selected = await session_manager.select_artworks(session_id, request.selected_indices)

        return SelectionResponse(
            session_id=session_id,
            message=f"Selected {len(selected)} artworks. Generating exhibition proposal.",
            selected_count=len(selected)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to select artworks for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/refine", response_model=RefineResponse)
async def refine_theme(session_id: str, request: RefineRequest):
    """
    Re-refine theme based on user feedback

    This endpoint allows iterative refinement of the exhibition theme.
    It reuses research data and only regenerates LLM content for fast responses (5-10 seconds).
    """
    try:
        session_manager = get_session_manager()

        # Get current theme from session
        current_theme = await session_manager.get_refined_theme(session_id)
        if not current_theme:
            raise HTTPException(status_code=404, detail=f"Session {session_id}: No refined theme found")

        # Get original brief from session (we need this for re-refinement)
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # We need the original brief - for now, create a minimal one
        # TODO: Store original brief in session for proper re-refinement
        from backend.models import CuratorBrief
        original_brief = CuratorBrief(
            theme_title=current_theme.theme_description or "Theme",
            theme_description=current_theme.theme_description,
            theme_concepts=[c.original_concept for c in current_theme.validated_concepts[:5]],
            target_audience="general",
            duration_weeks=12
        )

        # Initialize agents
        data_client = EssentialDataClient()
        from backend.agents.theme_refinement_agent import ThemeRefinementAgent
        theme_agent = ThemeRefinementAgent(data_client)

        # Re-refine theme with feedback
        updated_theme = await theme_agent.re_refine_theme(
            previous_theme=current_theme,
            feedback=request.feedback,
            original_brief=original_brief
        )

        # Store updated theme in session
        await session_manager.store_refined_theme(session_id, updated_theme)

        # Return updated theme
        return RefineResponse(
            session_id=session_id,
            message=f"Theme refined successfully (iteration {updated_theme.iteration_count})",
            iteration_count=updated_theme.iteration_count,
            theme=updated_theme.model_dump(mode='json')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refine theme for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/continue", response_model=ContinueResponse)
async def continue_to_next_phase(session_id: str, request: ContinueRequest):
    """
    Approve theme and continue to next phase

    Validates that prerequisites are met and starts background task for the next phase.
    Returns WebSocket URL for progress tracking.
    """
    try:
        session_manager = get_session_manager()

        # Get session
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Validate phase parameter
        if request.phase not in ['artist_discovery', 'artwork_discovery']:
            raise HTTPException(status_code=400, detail="Phase must be 'artist_discovery' or 'artwork_discovery'")

        # Mark theme as approved if starting artist discovery (BEFORE checking prerequisites)
        if request.phase == 'artist_discovery':
            await session_manager.approve_theme(session_id)

        # Check if we can start this phase
        can_proceed = await session_manager.can_start_phase(session_id, request.phase)
        if not can_proceed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start {request.phase} - prerequisites not met"
            )

        # Start background task for the phase
        # TODO: Implement background task execution for phase continuation
        # For now, just return success response

        logger.info(f"Session {session_id}: Starting {request.phase} phase")

        return ContinueResponse(
            session_id=session_id,
            message=f"Starting {request.phase}",
            next_phase=request.phase,
            websocket_url=f"/ws/{session_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to continue to next phase for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proposals/{session_id}")
async def get_proposal(session_id: str):
    """
    Retrieve the completed exhibition proposal
    """
    if session_id not in proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal = proposals[session_id]

    return {
        "session_id": session_id,
        "proposal": proposal.model_dump(mode='json'),
        "retrieved_at": datetime.utcnow().isoformat()
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time progress updates
    """
    await websocket_manager.connect(session_id, websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connected"
        })

        # Send any pending messages that were generated before this connection
        if hasattr(websocket_manager, 'pending_messages') and session_id in websocket_manager.pending_messages:
            logger.info(f"Sending pending message to newly connected WebSocket for session {session_id}")
            try:
                await websocket.send_json(websocket_manager.pending_messages[session_id])
                logger.info(f"Successfully sent pending message for session {session_id}")
                del websocket_manager.pending_messages[session_id]
            except Exception as e:
                logger.error(f"Failed to send pending message for session {session_id}: {e}")

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (ping/pong)
                data = await websocket.receive_text()

                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error for session {session_id}: {e}")
                break

    finally:
        websocket_manager.disconnect(session_id)


# Background Processing

async def process_curator_brief(
    session_id: str,
    curator_brief: CuratorBrief,
    config: Optional[Dict] = None
):
    """
    Background task to process curator brief through the pipeline
    with interactive curator selection support
    """
    try:
        logger.info(f"Starting pipeline processing for session {session_id}")

        # Check if automatic mode is requested (for testing)
        auto_select = config.get("auto_select", False) if config else False

        # Initialize session manager (only if not in auto mode)
        session_manager = None
        if not auto_select:
            session_manager = get_session_manager()
            await session_manager.create_session(session_id)

        # Create progress callback
        async def progress_callback(status: PipelineStatus):
            await websocket_manager.send_progress(session_id, status)

        # Initialize data client and orchestrator
        async with EssentialDataClient() as client:
            orchestrator = OrchestratorAgent(
                data_client=client,
                progress_callback=progress_callback,
                session_manager=session_manager  # None = automatic mode, not None = interactive mode
            )

            # Execute pipeline
            result = await orchestrator.execute_pipeline(
                curator_brief=curator_brief,
                session_id=session_id,
                config=config
            )

            # Check if theme-only execution or full pipeline
            phase = config.get('phase', 'full') if config else 'full'

            if phase == 'theme_only':
                # Result is a RefinedTheme - send theme_complete message
                logger.info(f"Preparing to send theme_complete message for session {session_id}")

                theme_data = result.model_dump(mode='json')
                logger.info(f"Serialized theme data successfully for session {session_id}")

                # Store theme data temporarily for late-connecting WebSockets
                if not hasattr(websocket_manager, 'pending_messages'):
                    websocket_manager.pending_messages = {}

                websocket_manager.pending_messages[session_id] = {
                    "type": "theme_complete",
                    "session_id": session_id,
                    "message": "Theme refinement complete",
                    "theme": theme_data
                }

                # Try to send immediately if connection exists
                if session_id in websocket_manager.active_connections:
                    try:
                        await websocket_manager.active_connections[session_id].send_json(
                            websocket_manager.pending_messages[session_id]
                        )
                        logger.info(f"Successfully sent theme_complete message for session {session_id}")
                        del websocket_manager.pending_messages[session_id]
                    except Exception as e:
                        logger.warning(f"Failed to send theme_complete message for session {session_id}: {e}. Will retry when WebSocket reconnects.")
                else:
                    logger.info(f"No active WebSocket for session {session_id}. Message will be sent when client connects.")

                logger.info(f"Theme-only processing completed for session {session_id}")
            else:
                # Result is an ExhibitionProposal - store and send completed message
                proposals[session_id] = result

                if session_id in websocket_manager.active_connections:
                    await websocket_manager.active_connections[session_id].send_json({
                        "type": "completed",
                        "session_id": session_id,
                        "message": "Exhibition proposal complete",
                        "proposal_url": f"/api/proposals/{session_id}"
                    })
                logger.info(f"Pipeline processing completed for session {session_id}")

    except Exception as e:
        logger.error(f"Pipeline processing failed for session {session_id}: {e}", exc_info=True)

        # Send error message
        if session_id in websocket_manager.active_connections:
            await websocket_manager.active_connections[session_id].send_json({
                "type": "error",
                "session_id": session_id,
                "message": "Processing failed",
                "error": str(e)
            })

        raise


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
