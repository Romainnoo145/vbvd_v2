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
        """Send progress update to connected client"""
        if session_id in self.active_connections:
            try:
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


@app.post("/api/curator/submit", response_model=SubmitResponse)
async def submit_curator_brief(request: CuratorBriefRequest):
    """
    Submit a curator brief for processing

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

        # Initialize session manager
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
                session_manager=session_manager  # Enable interactive mode
            )

            # Execute pipeline
            proposal = await orchestrator.execute_pipeline(
                curator_brief=curator_brief,
                session_id=session_id,
                config=config
            )

            # Store result
            proposals[session_id] = proposal

            # Send completion message
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
