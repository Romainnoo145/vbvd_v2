# Human-in-the-Loop Validation - Already Implemented! ✅

## Overview

The AI Curator pipeline **already includes** human-in-the-loop validation checkpoints! Curators can review and approve/edit results after each stage before proceeding.

## Implementation Status: ✅ COMPLETE

Located in: `backend/agents/orchestrator_agent.py` lines 272-283 and 313-323

## How It Works

### Activation

Human-in-the-loop mode activates when `session_manager` is provided to the orchestrator:

```python
orchestrator = OrchestratorAgent(
    data_client=data_client,
    progress_callback=progress_callback,
    session_manager=session_manager  # Enable interactive mode
)
```

### Workflow

```
Stage 1: Theme Refinement
  ↓
  ✅ COMPLETE (title, statement, rationale)
  ↓
Stage 2: Artist Discovery
  ↓
  ✅ COMPLETE (10-15 artists with scores)
  ↓
  ⏸️  CHECKPOINT 1: Curator Artist Selection
      - Pipeline pauses
      - Frontend displays discovered artists with scores
      - Curator selects which artists to include
      - API: POST /api/sessions/{session_id}/select-artists
      - Payload: {"selected_indices": [0, 2, 5, 7]}
  ↓
  ✅ RESUME with curator-selected artists
  ↓
Stage 3: Artwork Discovery
  ↓
  ✅ COMPLETE (30-50 artworks with IIIF)
  ↓
  ⏸️  CHECKPOINT 2: Curator Artwork Selection
      - Pipeline pauses
      - Frontend displays discovered artworks with IIIF viewers
      - Curator selects final artworks for exhibition
      - API: POST /api/sessions/{session_id}/select-artworks
      - Payload: {"selected_indices": [0, 1, 3, 5, 8, 12]}
  ↓
  ✅ RESUME with curator-selected artworks
  ↓
Final Proposal Generation
  ↓
  ✅ COMPLETE
```

## API Endpoints (Already Implemented)

### 1. Get Session Status (Check if Awaiting Selection)

```bash
GET /api/sessions/{session_id}/status
```

**Response when awaiting artist selection:**
```json
{
  "session_id": "session-123",
  "state": "awaiting_artist_selection",
  "artist_candidates": [
    {
      "name": "Salvador Dalí",
      "wikidata_id": "Q5682",
      "relevance_score": 0.95,
      "biography": "...",
      "index": 0
    },
    ...
  ]
}
```

**Response when awaiting artwork selection:**
```json
{
  "session_id": "session-123",
  "state": "awaiting_artwork_selection",
  "artwork_candidates": [
    {
      "title": "The Persistence of Memory",
      "artist_name": "Salvador Dalí",
      "iiif_manifest": "https://...",
      "relevance_score": 0.92,
      "index": 0
    },
    ...
  ]
}
```

### 2. Submit Artist Selection

```bash
POST /api/sessions/{session_id}/select-artists
Content-Type: application/json

{
  "selected_indices": [0, 2, 5, 7, 9]
}
```

**Response:**
```json
{
  "session_id": "session-123",
  "message": "Selected 5 artists. Proceeding to artwork discovery.",
  "selected_count": 5
}
```

### 3. Submit Artwork Selection

```bash
POST /api/sessions/{session_id}/select-artworks
Content-Type: application/json

{
  "selected_indices": [0, 1, 3, 5, 8, 12, 15, 18]
}
```

**Response:**
```json
{
  "session_id": "session-123",
  "message": "Selected 8 artworks. Generating exhibition proposal.",
  "selected_count": 8
}
```

## Session Manager (backend/utils/session_manager.py)

The session manager handles state persistence:

```python
class SessionState(str, Enum):
    PROCESSING = "processing"
    AWAITING_ARTIST_SELECTION = "awaiting_artist_selection"
    AWAITING_ARTWORK_SELECTION = "awaiting_artwork_selection"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Key Methods:

- `create_session(session_id)` - Initialize new session
- `set_artist_candidates(session_id, candidates)` - Pause for artist selection
- `select_artists(session_id, indices)` - Resume with selection
- `set_artwork_candidates(session_id, candidates)` - Pause for artwork selection
- `select_artworks(session_id, indices)` - Resume with selection

## Frontend Integration Example

### 1. Poll for Session Status

```javascript
async function pollSessionStatus(sessionId) {
  const response = await fetch(`/api/sessions/${sessionId}/status`);
  const session = await response.json();

  switch (session.state) {
    case 'awaiting_artist_selection':
      // Show artist selection UI
      displayArtistSelectionModal(session.artist_candidates);
      break;

    case 'awaiting_artwork_selection':
      // Show artwork selection UI
      displayArtworkSelectionModal(session.artwork_candidates);
      break;

    case 'completed':
      // Fetch final proposal
      fetchProposal(sessionId);
      break;
  }
}
```

### 2. Submit Artist Selection

```javascript
async function submitArtistSelection(sessionId, selectedIndices) {
  const response = await fetch(`/api/sessions/${sessionId}/select-artists`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_indices: selectedIndices })
  });

  const result = await response.json();
  console.log(result.message); // "Selected 5 artists..."

  // Continue polling for next checkpoint
  pollSessionStatus(sessionId);
}
```

### 3. Submit Artwork Selection

```javascript
async function submitArtworkSelection(sessionId, selectedIndices) {
  const response = await fetch(`/api/sessions/${sessionId}/select-artworks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selected_indices: selectedIndices })
  });

  const result = await response.json();
  console.log(result.message); // "Selected 8 artworks..."

  // Proposal generation will complete automatically
  pollSessionStatus(sessionId);
}
```

## Automatic Mode (No Human Validation)

If session_manager is NOT provided, the pipeline runs fully automatically:

```python
orchestrator = OrchestratorAgent(
    data_client=data_client,
    progress_callback=progress_callback
    # No session_manager = automatic mode
)
```

In automatic mode:
- All discovered artists are used
- Top N artworks (by relevance score) are selected automatically
- No pauses for human review

## Testing

See `tests/test_full_workflow_auto.py` for a complete example of human-in-the-loop workflow:

```bash
# Run interactive workflow test
python3 tests/test_full_workflow_auto.py
```

This test demonstrates:
1. Pipeline pauses after artist discovery
2. Simulated curator selects 5 artists
3. Pipeline resumes to artwork discovery
4. Pipeline pauses after artwork discovery
5. Simulated curator selects 8 artworks
6. Final proposal generation completes

## Benefits

✅ **Quality Control**: Curator reviews AI recommendations before proceeding
✅ **Flexibility**: Can override AI scores and add manual selections
✅ **Transparency**: All candidates shown with relevance scores and reasoning
✅ **Efficiency**: AI does heavy lifting, curator makes final decisions
✅ **Already Built**: No additional implementation needed!

## Next Steps

For your frontend:
1. Implement artist selection modal/page
2. Implement artwork selection modal/page with IIIF viewers
3. Poll session status endpoint during processing
4. Submit selections via API endpoints

The backend is **ready to go** for full human-in-the-loop workflows!
