# AI Curator Assistant - Production-Ready 3-Stage Agent System

Intelligent AI curator assistant that transforms curatorial input into complete exhibition proposals using real museum data and AI-powered analysis.

## 🎯 Overview

A fully functional multi-agent system that generates exhibition proposals in 5-8 minutes:
1. **Theme Refinement** - Validates concepts and generates professional exhibition frameworks with scholarly rationale
2. **Artist Discovery** - Discovers relevant artists with AI-powered relevance scoring
3. **Artwork Discovery** - Searches multiple museum APIs for artworks with IIIF manifests
4. **Progressive Streaming** - Real-time WebSocket updates as each stage completes

## 🏗️ Architecture

```
Curator Input (CuratorBrief)
           ↓
    ┌──────────────────────────────────┐
    │   STAGE 1: Theme Refinement     │  ← 30 seconds
    │  • Wikipedia research           │
    │  • Brave Search context         │
    │  • GPT-4 content generation     │
    └──────────────────────────────────┘
           ↓ WebSocket: Theme complete
    RefinedTheme (title, statement, rationale)
           ↓
    ┌──────────────────────────────────┐
    │   STAGE 2: Artist Discovery      │  ← 1-2 minutes
    │  • Wikipedia article mining     │
    │  • Diversity-aware search       │
    │  • GPT-4 relevance scoring      │
    └──────────────────────────────────┘
           ↓ WebSocket: Artists complete
    List[DiscoveredArtist] (5-15 artists)
           ↓
    ┌──────────────────────────────────┐
    │   STAGE 3: Artwork Discovery     │  ← 3-5 minutes
    │  • Europeana API (58M items)    │
    │  • Yale LUX Linked Art          │
    │  • Wikidata SPARQL              │
    │  • IIIF manifest parsing        │
    │  • GPT-4 relevance scoring      │
    └──────────────────────────────────┘
           ↓ WebSocket: Artworks complete
    ExhibitionProposal (15-50 artworks with IIIF)
```

## 📁 Project Structure

```
├── backend/              # Core application code
│   ├── agents/          # Theme and Artist discovery agents
│   ├── clients/         # API clients (Wikipedia, Wikidata, Yale LUX)
│   ├── config/          # Data source configurations
│   ├── models/          # Pydantic data models
│   ├── utils/           # Database and utility functions
│   └── validators/      # Input validation logic
├── docs/                # Documentation
├── tests/               # Test files and demos
├── scripts/             # Utility scripts
├── infrastructure/      # Database/Redis configs
└── examples/            # Example implementations

```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Internet connection (for API access)

### Installation

```bash
# Clone the repository
git clone https://github.com/Romainnoo145/vbvd_v2.git
cd vbvd_v2

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys (optional)
nano .env
```

### API Keys (Required)

```bash
# Required
export OPENAI_API_KEY="sk-..."        # For GPT-4 theme generation and scoring

# Optional (enhances results)
export BRAVE_API_KEY="BSA..."         # For contemporary discourse research
```

### Running the Backend

```bash
# Start FastAPI server
cd backend/api
python3 main.py

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Running Tests

```bash
# Quick validation test (Stage 1 only, ~30 seconds)
python3 tests/test_surrealism_quick.py

# Full pipeline test with WebSocket streaming (~5-8 minutes)
./run_streaming_test.sh

# Or manually
python3 tests/test_full_workflow_auto.py
```

### API Endpoints

```bash
# Submit curator brief
POST /api/curator/submit
Body: {"curator_brief": {...}, "config": {"auto_select": false}}

# Connect to WebSocket for real-time updates
WS /ws/{session_id}

# Get session status (for human-in-the-loop checkpoints)
GET /api/sessions/{session_id}/status

# Submit artist selection
POST /api/sessions/{session_id}/select-artists
Body: {"selected_indices": [0, 2, 5, 7]}

# Submit artwork selection
POST /api/sessions/{session_id}/select-artworks
Body: {"selected_indices": [1, 3, 4, 8, 10]}

# Retrieve final proposal
GET /api/proposals/{session_id}
```

## 🔌 Data Sources

### Museum & Cultural Heritage APIs
- **Europeana** - 58 million cultural heritage items, IIIF manifest support
- **Yale LUX** - Linked Art institutional collections
- **Wikidata** - Structured artist/artwork data via SPARQL
- **Wikipedia** - Art historical context and biographical research

### AI & Search
- **OpenAI GPT-4** - Theme generation, relevance scoring, curatorial content
- **Brave Search** - Contemporary art discourse research *(optional)*

### Standards Supported
- **IIIF** (International Image Interoperability Framework) - 78% artwork coverage
- **Linked Art** - Semantic artwork metadata
- **SPARQL** - Structured cultural data queries

## ✅ Current Status: Production Ready

### Fully Implemented & Tested ✅
- ✅ **Stage 1**: Theme Refinement with scholarly rationale (30 seconds)
- ✅ **Stage 2**: Artist Discovery with diversity metrics (1-2 minutes)
- ✅ **Stage 3**: Artwork Discovery with IIIF manifests (3-5 minutes)
- ✅ **Orchestrator Agent**: Full pipeline coordination
- ✅ **Enrichment Agent**: Metadata augmentation via web search
- ✅ **WebSocket Streaming**: Progressive stage completion updates
- ✅ **REST API**: FastAPI backend with session management
- ✅ **Human-in-the-Loop**: Curator review points for artist/artwork selection
- ✅ **Automatic Mode**: Skip review for testing (`auto_select: true`)

### Verified Integrations ✅
- ✅ Europeana API (58M items, IIIF manifests working)
- ✅ Yale LUX Linked Art API (institutional collections)
- ✅ Wikidata SPARQL (140+ artworks per theme)
- ✅ Wikipedia REST API (research & biographies)
- ✅ OpenAI GPT-4 (theme generation, scoring)
- ✅ IIIF manifest parsing (dimensions, images)
- ✅ Brave Search API (contemporary discourse)

### Performance Metrics 📊
- **Total Time**: 5-8 minutes for complete proposal
- **IIIF Coverage**: 78% of artworks
- **Image Coverage**: 100% of artworks
- **Diversity Tracking**: Gender, nationality, period
- **Quality**: Museum-grade curatorial content

### Ready For Frontend Integration ✅
See `FRONTEND_READINESS.md` for API documentation and integration guide.

## 📊 Example Output

See `docs/PIPELINE_OUTPUT_EXAMPLE.md` for complete example showing:
- Curator input for Dutch Golden Age exhibition
- Stage 1 refined theme with validated concepts
- Stage 2 discovered 24 artists with full details
- Relevance reasoning and statistics

## 🧪 Testing Strategy

Test files are organized in `tests/`:
- `test_theme_simple.py` - Quick Theme Agent test
- `test_simple_discovery.py` - Artist Discovery with real data
- `test_real_pipeline.py` - Full Stage 1 → Stage 2 flow
- `test_diversity_pipeline.py` - Diversity metrics testing

## 📚 Documentation

- `FRONTEND_READINESS.md` - **Frontend integration guide** (start here!)
- `API_TESTING_GUIDE.md` - API usage examples and testing
- `AGENT_ARCHITECTURE.md` - Agent design and data flow
- `PROGRESSIVE_STREAMING_PLAN.md` - WebSocket streaming implementation
- `HUMAN_IN_THE_LOOP.md` - Curator review workflow
- `TEST_RESULTS.md` - Latest test results with performance metrics
- `docs/PIPELINE_OUTPUT_EXAMPLE.md` - Complete example output
- `docs/IMPLEMENTATION_STATUS.md` - Implementation timeline
- `docs/WORKFLOW_ANALYSIS.md` - Architecture analysis

## 🤝 Contributing

This is a research project. For questions or contributions, please open an issue.

## 📄 License

[Add your license here]

## 🔗 Links

- GitHub: https://github.com/Romainnoo145/vbvd_v2
- Getty Vocabularies: http://vocab.getty.edu/
- Wikidata SPARQL: https://query.wikidata.org/
- Yale LUX: https://lux.collections.yale.edu/

## 🙏 Acknowledgments

Built with:
- Pydantic for data validation
- httpx for async HTTP requests
- Wikipedia API, Wikidata SPARQL, Getty Vocabularies