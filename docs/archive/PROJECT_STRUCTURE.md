# Project Structure

**Last Updated:** October 2, 2025
**Status:** Production Ready

## Root Directory
```
vbvd_agent_v2/
├── README.md                       # Main project documentation
├── FRONTEND_READINESS.md           # Frontend integration guide ⭐
├── API_TESTING_GUIDE.md            # API usage and testing
├── AGENT_ARCHITECTURE.md           # Agent design documentation
├── PROGRESSIVE_STREAMING_PLAN.md   # WebSocket streaming guide
├── HUMAN_IN_THE_LOOP.md            # Curator review workflow
├── TEST_RESULTS.md                 # Latest test results
├── PROJECT_STRUCTURE.md            # This file
├── TESTING_INSTRUCTIONS.md         # How to run tests
├── requirements.txt                # Python dependencies
├── .env                           # Local config (not in git)
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── run_streaming_test.sh          # WebSocket test script ⭐
└── memories.json                  # Memory storage
```

## Main Directories

### 📦 backend/ - Core Application Code

```
backend/
├── agents/                          # AI agents (5 total) ✅
│   ├── __init__.py
│   ├── theme_refinement_agent.py    # Stage 1: Theme refinement (30s)
│   ├── artist_discovery_simple.py   # Stage 2: Artist discovery (1-2min) ⭐
│   ├── artist_discovery_agent.py    # Alternative SPARQL-based (deprecated)
│   ├── artwork_discovery_agent.py   # Stage 3: Artwork discovery (3-5min) ✅
│   ├── enrichment_agent.py          # Stage 3.5: Metadata enrichment ✅
│   └── orchestrator_agent.py        # Pipeline coordinator ✅
│
├── api/                             # FastAPI REST + WebSocket ✅
│   ├── __init__.py
│   └── main.py                      # FastAPI application ⭐
│
├── clients/                         # External API clients ✅
│   ├── __init__.py
│   ├── essential_data_client.py     # Wikipedia, Wikidata, Yale LUX
│   ├── artic_client.py              # Art Institute of Chicago API
│   └── (Europeana integrated in essential_data_client)
│
├── config/                          # Configuration
│   ├── __init__.py
│   └── data_sources.py              # API endpoints and settings
│
├── models/                          # Pydantic data models ✅
│   ├── __init__.py                  # Exports all models
│   ├── curator_brief.py             # Input: CuratorBrief
│   ├── discovery.py                 # Output: DiscoveredArtist, ArtworkCandidate
│   └── exhibition.py                # Output: ExhibitionProposal
│
├── utils/                           # Utilities ✅
│   ├── __init__.py
│   ├── database.py                  # Database utilities
│   ├── iiif_utils.py                # IIIF manifest parsing ✅
│   └── session_manager.py           # Session state management ✅
│
├── validators/                      # Input validation
│   ├── __init__.py
│   └── curator_input_validator.py
│
└── services/                        # Business logic (reserved)
```

### 🧪 tests/ - All Test Files

```
tests/
├── __init__.py
│
├── test_surrealism_quick.py         # ⭐ Quick validation (Stage 1 only, ~30s)
├── test_full_workflow_auto.py       # ⭐ Full pipeline test (all stages, ~5-8min)
├── test_websocket_streaming.py      # ⭐ WebSocket progressive streaming test
│
├── test_theme_agent.py              # Theme agent unit tests
├── test_theme_simple.py             # Simple theme test
├── test_artist_discovery_agent.py   # Artist discovery tests (SPARQL-based)
├── test_simple_discovery.py         # Artist discovery tests (Wikipedia-based)
├── test_real_pipeline.py            # Stage 1 → Stage 2 test
├── test_diversity_pipeline.py       # Diversity metrics tests
│
├── test_validation.py               # Input validation tests
├── test_validation_simple.py        # Simple validation test
├── test_api_connectivity.py         # API connectivity tests
├── test_getty_direct.py             # Getty debugging
├── test_client.py                   # Client tests
├── test_config.py                   # Config tests
├── test_models.py                   # Model tests
├── test_optie_a_b_combined.py       # Combined options test
│
├── demo_current_capabilities.py     # Capability demo
├── simple_demo.py                   # Simple demo
└── verify_real_data.py              # Data verification
```

### 📚 docs/ - Documentation
```
docs/
├── IMPLEMENTATION_STATUS.md      # Current implementation status
├── PIPELINE_OUTPUT_EXAMPLE.md    # Example pipeline output
└── WORKFLOW_ANALYSIS.md          # Workflow analysis
```

### 🛠️ scripts/ - Utility Scripts
```
scripts/
└── init_database.py              # Database initialization
```

### 🏗️ infrastructure/ - Infrastructure Config
```
infrastructure/
├── init_db.sql                   # Database schema
└── redis.conf                    # Redis configuration
```

### 💡 examples/ - Example Implementations
```
examples/
└── (empty - for future use)
```

### 📖 full-ai-coding-workflow/ - Reference Material
```
full-ai-coding-workflow/
├── PRPs/                         # Prompt Reference Patterns
├── FullExample/                  # Example implementation
└── PromptProgression/            # Prompt engineering examples
```

## Key Files

### 🚀 Application Entry Points

**Backend API:**
- `backend/api/main.py` - FastAPI application with REST + WebSocket ⭐

**Testing:**
- `run_streaming_test.sh` - WebSocket streaming test script ⭐
- `tests/test_surrealism_quick.py` - Quick validation (~30s)
- `tests/test_full_workflow_auto.py` - Full pipeline (~5-8min)

### 🤖 Core Agents (Production Pipeline)

1. `backend/agents/theme_refinement_agent.py` - Stage 1: Theme refinement (30s)
2. `backend/agents/artist_discovery_simple.py` - Stage 2: Artist discovery (1-2min) ⭐
3. `backend/agents/artwork_discovery_agent.py` - Stage 3: Artwork discovery (3-5min) ✅
4. `backend/agents/enrichment_agent.py` - Stage 3.5: Metadata enrichment ✅
5. `backend/agents/orchestrator_agent.py` - Pipeline coordinator ✅

**Alternative/Deprecated:**
- `backend/agents/artist_discovery_agent.py` - SPARQL-based (slower, kept for testing)

### 📊 Data Models

**Input:**
- `backend/models/curator_brief.py` - CuratorBrief (user input)

**Stage Outputs:**
- `backend/models/discovery.py` - RefinedTheme, DiscoveredArtist, ArtworkCandidate
- `backend/models/exhibition.py` - ExhibitionProposal (final output)

**Internal:**
- `backend/agents/orchestrator_agent.py` - PipelineStatus, PipelineStage

### 🔌 API Clients

- `backend/clients/essential_data_client.py` - Europeana, Wikipedia, Wikidata, Yale LUX
- `backend/clients/artic_client.py` - Art Institute of Chicago

### 🛠️ Utilities

- `backend/utils/iiif_utils.py` - IIIF manifest parsing ✅
- `backend/utils/session_manager.py` - Session state management ✅
- `backend/utils/database.py` - Database utilities

## Testing Strategy

### Recommended Tests (Production Validation)

```bash
# Quick validation (~30 seconds)
python3 tests/test_surrealism_quick.py

# Full pipeline with WebSocket (~5-8 minutes)
./run_streaming_test.sh

# Or run full workflow manually
python3 tests/test_full_workflow_auto.py
```

### Unit Tests (Agent-Specific)

```bash
# Stage 1: Theme refinement
python3 tests/test_theme_simple.py

# Stage 2: Artist discovery (Wikipedia-based)
python3 tests/test_simple_discovery.py

# Stage 2: Artist discovery (SPARQL-based, deprecated)
python3 tests/test_artist_discovery_agent.py
```

### Integration Tests

```bash
# Stage 1 → Stage 2 flow
python3 tests/test_real_pipeline.py

# Diversity metrics
python3 tests/test_diversity_pipeline.py

# Input validation
python3 tests/test_validation.py
```

### Verification Tests

```bash
# API connectivity
python3 tests/test_api_connectivity.py

# Real data integration
python3 tests/verify_real_data.py
```

## Production Data Flow

```
User/Frontend
    ↓
POST /api/curator/submit (CuratorBrief)
    ↓
backend/api/main.py
    ↓
backend/agents/orchestrator_agent.py (Pipeline Coordinator)
    ├─> WebSocket progress updates (real-time)
    ├─> Session state management
    └─> Coordinates all stages:
        │
        ├─> STAGE 1 (30 seconds)
        │   backend/agents/theme_refinement_agent.py
        │   └─> RefinedTheme
        │       └─> WebSocket: stage_complete (25%)
        │
        ├─> STAGE 2 (1-2 minutes)
        │   backend/agents/artist_discovery_simple.py
        │   └─> List[DiscoveredArtist]
        │       └─> WebSocket: stage_complete (55%)
        │       └─> [OPTIONAL: Human review checkpoint]
        │
        └─> STAGE 3 (3-5 minutes)
            backend/agents/artwork_discovery_agent.py
            ├─> Europeana, Yale LUX, Wikidata queries
            ├─> IIIF manifest parsing (backend/utils/iiif_utils.py)
            └─> List[ArtworkCandidate]
                └─> backend/agents/enrichment_agent.py
                    └─> Enriched artworks
                        └─> WebSocket: stage_complete (90%)
                        └─> [OPTIONAL: Human review checkpoint]
                        └─> ExhibitionProposal
                            └─> WebSocket: completed (100%)
                            └─> GET /api/proposals/{session_id}
```

## External Dependencies

### Museum & Cultural Heritage APIs
- **Europeana** - 58M cultural heritage items, IIIF manifests ✅
- **Yale LUX** - Linked Art institutional collections ✅
- **Wikidata** - SPARQL queries for structured data ✅
- **Wikipedia** - REST API for research and biographies ✅
- **Art Institute of Chicago** - ARTIC API (optional)

### AI & Search APIs
- **OpenAI GPT-4** - Content generation and relevance scoring (required) ✅
- **Brave Search** - Contemporary discourse research (optional)

### Python Packages (requirements.txt)
```bash
# Core framework
fastapi           # REST + WebSocket API
uvicorn           # ASGI server
pydantic          # Data validation
httpx             # Async HTTP client

# AI integration
openai            # GPT-4 API

# Environment
python-dotenv     # .env file support

# Utilities
asyncio           # Async runtime
websockets        # WebSocket support
```

## API Endpoints Reference

### REST Endpoints
```
POST   /api/curator/submit              # Submit curator brief
GET    /api/sessions/{session_id}/status # Get session status
POST   /api/sessions/{session_id}/select-artists  # Submit artist selection
POST   /api/sessions/{session_id}/select-artworks # Submit artwork selection
GET    /api/proposals/{session_id}      # Retrieve final proposal
GET    /health                          # Health check
GET    /                                # API info
```

### WebSocket Endpoints
```
WS     /ws/{session_id}                 # Real-time progress updates
```

### WebSocket Message Types
1. `connected` - Connection established
2. `progress` - Regular progress updates (percentage + message)
3. `stage_complete` - Stage finished with full data payload
4. `completed` - Pipeline finished, proposal ready
5. `error` - Error occurred

## Configuration

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
BRAVE_API_KEY=BSA...
```

### Runtime Configuration (config parameter)
```python
config = {
    "max_artists": 5,              # Number of artists to discover
    "max_artworks": 15,            # Number of artworks to discover
    "min_artist_relevance": 0.6,   # Minimum relevance score for artists
    "min_artwork_relevance": 0.5,  # Minimum relevance score for artworks
    "auto_select": False           # Skip human review (testing mode)
}
```

## Notes

- ⭐ = Recommended starting point for new developers
- ✅ = Production ready and tested
- All agents fully implemented and tested with real museum APIs
- WebSocket progressive streaming implemented and working
- IIIF manifest support with 78% coverage
- Human-in-the-loop workflow supported (optional)
- Automatic mode available for testing/batch processing
- See `FRONTEND_READINESS.md` for integration guide
