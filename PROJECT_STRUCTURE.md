# Project Structure

## Root Directory
```
vbvd_agent_v2/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── .env                        # Local config (not in git)
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── memories.json               # Memory storage
```

## Main Directories

### 📦 backend/ - Core Application Code
```
backend/
├── agents/                     # AI agents
│   ├── theme_refinement_agent.py
│   └── artist_discovery_agent.py
├── api/                       # API endpoints (empty)
├── clients/                   # External API clients
│   └── essential_data_client.py
├── config/                    # Configuration
│   └── data_sources.py
├── models/                    # Pydantic data models
│   ├── curator_brief.py
│   ├── discovery.py
│   └── exhibition.py
├── services/                  # Business logic (empty)
├── utils/                     # Utilities
│   └── database.py
└── validators/                # Input validation
    └── curator_input_validator.py
```

### 🧪 tests/ - All Test Files
```
tests/
├── test_theme_agent.py           # Theme agent tests
├── test_theme_simple.py          # Simple theme test
├── test_artist_discovery_agent.py # Artist discovery tests
├── test_simple_discovery.py      # Simple discovery test
├── test_real_pipeline.py         # Full pipeline test
├── test_validation.py            # Validation tests
├── test_validation_simple.py     # Simple validation test
├── test_api_connectivity.py      # API connectivity tests
├── test_diversity_pipeline.py    # Diversity metrics tests
├── test_getty_direct.py          # Getty debugging
├── test_client.py                # Client tests
├── test_config.py                # Config tests
├── test_models.py                # Model tests
├── test_optie_a_b_combined.py    # Combined options test
├── demo_current_capabilities.py  # Capability demo
├── simple_demo.py                # Simple demo
└── verify_real_data.py           # Data verification
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

### Application Entry Points
- `tests/demo_current_capabilities.py` - Full system demo
- `tests/simple_demo.py` - Quick demo
- `tests/test_real_pipeline.py` - Real pipeline test

### Core Agents
- `backend/agents/theme_refinement_agent.py` - Stage 1: Theme refinement
- `backend/agents/artist_discovery_agent.py` - Stage 2: Artist discovery

### Data Models
- `backend/models/curator_brief.py` - Input model
- `backend/models/discovery.py` - Discovery models
- `backend/models/exhibition.py` - Exhibition models

### API Clients
- `backend/clients/essential_data_client.py` - Wikipedia, Wikidata, Getty, Yale LUX

## Testing Strategy

### Quick Tests (Fast)
```bash
python3 tests/test_theme_simple.py        # Test theme agent
python3 tests/test_simple_discovery.py    # Test artist discovery
```

### Comprehensive Tests
```bash
python3 tests/test_real_pipeline.py       # Full Stage 1 → Stage 2
python3 tests/test_diversity_pipeline.py  # Diversity metrics
python3 tests/test_validation.py          # Input validation
```

### Verification
```bash
python3 tests/verify_real_data.py         # Verify real data integration
python3 tests/test_api_connectivity.py    # Check API connections
```

## Data Flow

```
User Input (CuratorBrief)
    ↓
backend/validators/curator_input_validator.py
    ↓
backend/agents/theme_refinement_agent.py (Stage 1)
    ↓
RefinedTheme
    ↓
backend/agents/artist_discovery_agent.py (Stage 2)
    ↓
List[DiscoveredArtist]
    ↓
[Stage 3 - Not yet implemented]
```

## External Dependencies

### Data Sources (via backend/clients/)
- **Wikipedia API** - Art historical context
- **Wikidata SPARQL** - Structured artist data
- **Getty Vocabularies** - Art terminology (optional/disabled)
- **Yale LUX** - Institutional artwork data (planned)
- **Brave Search** - Current research (optional)

### Python Packages (requirements.txt)
- httpx - Async HTTP client
- pydantic - Data validation
- asyncio - Async runtime

## Notes

- `backend/tests/` was removed (duplicate)
- All tests are in root `tests/` directory
- `full-ai-coding-workflow/` contains reference material (external)
- `examples/` reserved for future example implementations
- Getty Vocabularies marked as optional due to SPARQL issues
