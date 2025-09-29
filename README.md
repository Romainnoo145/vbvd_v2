# AI Curator Assistant - 3-Stage Agent System

Intelligent AI curator assistant with backend-first architecture that transforms curatorial input into exhibition proposals using Linked Art data.

## 🎯 Overview

A multi-agent system that helps curators discover artists and artworks for exhibitions by:
1. **Theme Refinement** - Validates concepts and generates professional exhibition frameworks
2. **Artist Discovery** - Finds relevant artists using Wikidata SPARQL queries
3. **Artwork Discovery** - [Coming Soon] Searches Yale LUX for specific artworks

## 🏗️ Architecture

```
Curator Input (CuratorBrief)
           ↓
    ┌──────────────────────────────────┐
    │   STAGE 1: Theme Refinement     │
    │  • Wikipedia research           │
    │  • Generate statements          │
    └──────────────────────────────────┘
           ↓
    RefinedTheme (validated concepts)
           ↓
    ┌──────────────────────────────────┐
    │   STAGE 2: Artist Discovery      │
    │  • Wikidata SPARQL queries      │
    │  • Wikipedia biographies        │
    │  • Relevance scoring            │
    └──────────────────────────────────┘
           ↓
    List[DiscoveredArtist] (ranked)
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

### API Keys (Optional)

- `ANTHROPIC_API_KEY` - For LLM-based artist relevance scoring (optional, has fallback)
- `BRAVE_API_KEY` - For current research/discourse (optional)
- Getty Vocabularies - **No API key needed** (free SPARQL endpoint, currently disabled)

### Running Tests

```bash
# Test Theme Refinement Agent
python3 tests/test_theme_simple.py

# Test Artist Discovery Agent
python3 tests/test_simple_discovery.py

# Test Full Pipeline (Stage 1 → Stage 2)
python3 tests/test_real_pipeline.py
```

## 🔌 Data Sources

### Primary (Always Used)
- **Wikipedia** - Art historical context and biographical data
- **Wikidata** - Structured artist/artwork data via SPARQL

### Optional
- **Getty Vocabularies (AAT/ULAN)** - Professional art terminology *(currently disabled)*
- **Yale LUX** - Institutional artwork data *(Stage 3, not yet implemented)*
- **Brave Search** - Current discourse research *(optional)*

## ✅ Current Status

### Completed
- ✅ Stage 1: Theme Refinement Agent
- ✅ Stage 2: Artist Discovery Agent
- ✅ Data models (CuratorBrief, RefinedTheme, DiscoveredArtist)
- ✅ Multi-source data integration
- ✅ Graceful error handling

### Tested with Real Data
- ✅ Wikipedia API integration
- ✅ Wikidata SPARQL queries
- ✅ Artist diversity data (gender, nationality)
- ✅ Full 2-stage pipeline

### In Progress
- 🔨 Stage 3: Artwork Discovery Agent
- 🔨 Orchestrator Agent (WebSocket coordination)
- 🔨 Frontend interface

### Known Issues
- ⚠️ Getty Vocabularies SPARQL endpoint unreliable (made optional)
- ⚠️ Wikidata queries may timeout on complex searches
- ⚠️ No comprehensive test suite yet

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

- `docs/IMPLEMENTATION_STATUS.md` - Detailed implementation status
- `docs/PIPELINE_OUTPUT_EXAMPLE.md` - Real-world output example
- `docs/WORKFLOW_ANALYSIS.md` - Workflow and architecture analysis

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