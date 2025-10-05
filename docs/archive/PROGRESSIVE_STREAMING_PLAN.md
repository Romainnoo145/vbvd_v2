# Progressive WebSocket Streaming Implementation Plan

## Current State
✅ WebSocket infrastructure exists in `backend/api/main.py`
✅ Progress callbacks send percentage + message
❌ Stage results (artists, artworks) not streamed progressively

## Desired Flow

```
Frontend connects to WS at: ws://localhost:8000/ws/{session_id}

Stage 1 Complete (1-2 min):
  ← {
    "type": "stage_complete",
    "stage": "theme_refinement",
    "progress": 25,
    "data": {
      "exhibition_title": "Dreams Unchained",
      "subtitle": "Surrealism Awakened",
      "curatorial_statement": "...",
      "scholarly_rationale": "..."
    }
  }

Stage 2 Complete (3-4 min):
  ← {
    "type": "stage_complete",
    "stage": "artist_discovery",
    "progress": 55,
    "data": {
      "artists": [
        {"name": "Salvador Dalí", "score": 0.95, "reasoning": "..."},
        {"name": "René Magritte", "score": 0.92, "reasoning": "..."}
      ]
    }
  }

Stage 3 Complete (5-8 min):
  ← {
    "type": "stage_complete",
    "stage": "artwork_discovery",
    "progress": 90,
    "data": {
      "artworks": [
        {
          "title": "The Persistence of Memory",
          "artist_name": "Salvador Dalí",
          "iiif_manifest": "https://...",
          "score": 0.92
        }
      ]
    }
  }

Complete:
  ← {
    "type": "completed",
    "session_id": "...",
    "proposal_url": "/api/proposals/{session_id}"
  }
```

## Implementation Steps

### 1. Enhance PipelineStatus Model
**File:** `backend/agents/orchestrator_agent.py`

Add optional stage_data field:
```python
class PipelineStatus(BaseModel):
    session_id: str
    current_stage: PipelineStage
    progress_percentage: int
    status_message: str
    started_at: datetime
    updated_at: datetime

    # NEW: Optional stage completion data
    stage_data: Optional[Dict[str, Any]] = None
    stage_completed: Optional[PipelineStage] = None
```

### 2. Modify Orchestrator to Send Stage Results
**File:** `backend/agents/orchestrator_agent.py`

After each stage, call progress callback with data:
```python
# After Stage 1
await self._update_progress(
    status,
    PipelineStage.THEME_REFINEMENT,
    25,
    "Theme refinement complete",
    stage_completed=PipelineStage.THEME_REFINEMENT,
    stage_data={
        "exhibition_title": refined_theme.exhibition_title,
        "subtitle": refined_theme.subtitle,
        "curatorial_statement": refined_theme.curatorial_statement,
        "scholarly_rationale": refined_theme.scholarly_rationale
    }
)

# After Stage 2
await self._update_progress(
    status,
    PipelineStage.ARTIST_DISCOVERY,
    55,
    "Artist discovery complete",
    stage_completed=PipelineStage.ARTIST_DISCOVERY,
    stage_data={
        "artists": [a.model_dump(mode='json') for a in discovered_artists]
    }
)

# After Stage 3
await self._update_progress(
    status,
    PipelineStage.ARTWORK_DISCOVERY,
    90,
    "Artwork discovery complete",
    stage_completed=PipelineStage.ARTWORK_DISCOVERY,
    stage_data={
        "artworks": [a.model_dump(mode='json') for a in selected_artworks]
    }
)
```

### 3. Update WebSocket Manager
**File:** `backend/api/main.py`

Modify `send_progress` to handle stage_data:
```python
async def send_progress(self, session_id: str, status: PipelineStatus):
    if session_id in self.active_connections:
        try:
            message = {
                "type": "progress",
                "session_id": status.session_id,
                "stage": status.current_stage.value,
                "progress": status.progress_percentage,
                "message": status.status_message,
                "updated_at": status.updated_at.isoformat()
            }

            # Add stage completion data if available
            if status.stage_completed and status.stage_data:
                message["type"] = "stage_complete"
                message["completed_stage"] = status.stage_completed.value
                message["data"] = status.stage_data

            await self.active_connections[session_id].send_json(message)
        except Exception as e:
            logger.error(f"Failed to send progress to {session_id}: {e}")
            self.disconnect(session_id)
```

### 4. Frontend Integration Example

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'connected':
      console.log('WebSocket connected');
      break;

    case 'progress':
      // Update progress bar
      updateProgress(message.progress, message.message);
      break;

    case 'stage_complete':
      // Handle stage completion
      switch (message.completed_stage) {
        case 'theme_refinement':
          displayTheme(message.data);
          break;
        case 'artist_discovery':
          displayArtists(message.data.artists);
          break;
        case 'artwork_discovery':
          displayArtworks(message.data.artworks);
          break;
      }
      break;

    case 'completed':
      // Fetch full proposal
      fetchProposal(message.proposal_url);
      break;

    case 'error':
      displayError(message.error);
      break;
  }
};

// Display functions
function displayTheme(data) {
  document.getElementById('exhibition-title').textContent = data.exhibition_title;
  document.getElementById('subtitle').textContent = data.subtitle;
  document.getElementById('statement').textContent = data.curatorial_statement;
  // Show theme section
  document.getElementById('theme-section').classList.remove('hidden');
}

function displayArtists(artists) {
  const container = document.getElementById('artists-grid');
  artists.forEach(artist => {
    const card = createArtistCard(artist);
    container.appendChild(card);
  });
  // Show artists section
  document.getElementById('artists-section').classList.remove('hidden');
}

function displayArtworks(artworks) {
  const gallery = document.getElementById('artwork-gallery');
  artworks.forEach(artwork => {
    const card = createArtworkCard(artwork);
    gallery.appendChild(card);
  });
  // Show artworks section
  document.getElementById('artworks-section').classList.remove('hidden');
}
```

## Benefits

1. **Better UX**: Users see results as they arrive (1-2-3 min intervals)
2. **Engagement**: User can start reading theme while waiting for artworks
3. **Transparency**: Clear visual progress through stages
4. **Interruption Recovery**: If connection drops, user still has partial results
5. **Perceived Performance**: Feels faster even with same backend time

## Testing

```bash
# Start API server
cd backend/api
uvicorn main:app --reload

# Test with WebSocket client
python3 tests/test_websocket_streaming.py
```

Test should verify:
- ✅ Stage 1 data received after ~1-2 min
- ✅ Stage 2 data received after ~3-4 min
- ✅ Stage 3 data received after ~5-8 min
- ✅ All data is valid JSON
- ✅ Progress percentages match stages
