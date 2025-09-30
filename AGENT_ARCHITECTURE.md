# Agent Architecture - Van Bommel van Dam Curator System

## Active Agents (Used in Production Pipeline)

### 1. **ThemeRefinementAgent** (`theme_refinement_agent.py`)
**Purpose:** Refines raw curator input into professional exhibition themes
**Used:** ✅ Stage 1 of pipeline (line 181 in orchestrator)
**Data Sources:**
- Wikipedia API for art historical context
- Getty AAT for concept validation
- Returns `RefinedTheme` with validated concepts

**Key Methods:**
- `refine_theme(curator_brief, session_id)` → `RefinedTheme`

---

### 2. **SimpleArtistDiscovery** (`artist_discovery_simple.py`)
**Purpose:** Fast, Wikipedia-first artist discovery
**Used:** ✅ Stage 2 of pipeline (line 196 in orchestrator)
**Why This One:**
- Much faster than Wikidata SPARQL queries
- More reliable for modern art artists
- Better coverage for Van Bommel van Dam focus area

**Data Sources:**
- Wikipedia API for artist names and bio
- Direct name lookup approach

**Key Methods:**
- `discover_artists(refined_theme, reference_artists, max_artists)` → `List[Dict]`

---

### 3. **ArtworkDiscoveryAgent** (`artwork_discovery_agent.py`)
**Purpose:** Discovers artworks by selected artists
**Used:** ✅ Stage 3 of pipeline (line 274 in orchestrator)
**Data Sources:**
- Yale LUX API (Linked Art)
- Wikidata SPARQL queries
- IIIF manifest discovery

**Key Methods:**
- `discover_artworks(refined_theme, selected_artists, session_id, ...)` → `List[ArtworkCandidate]`

---

### 4. **ArtworkEnrichmentAgent** (`enrichment_agent.py`)
**Purpose:** Enriches artwork metadata using web search
**Used:** ✅ Stage 3.5 of pipeline (line 315 in orchestrator)
**Data Sources:**
- Brave Search API for missing metadata
- Finds: dimensions, dates, medium, images, IIIF manifests

**Key Methods:**
- `enrich_artworks(artworks, max_concurrent)` → `List[ArtworkCandidate]`

---

### 5. **OrchestratorAgent** (`orchestrator_agent.py`)
**Purpose:** Coordinates the entire pipeline
**Used:** ✅ Main entry point
**Features:**
- Session state management
- Progress tracking
- Curator selection pause points
- Quality metrics calculation

**Key Methods:**
- `execute_pipeline(curator_brief, session_id, config)` → `ExhibitionProposal`

---

## Deprecated/Alternative Agents

### ❌ **ArtistDiscoveryAgent** (`artist_discovery_agent.py`)
**Status:** NOT USED in production pipeline
**Why Not:**
- Uses Wikidata SPARQL queries
- Slower and less reliable than SimpleArtistDiscovery
- Was replaced but kept for backwards compatibility with old tests

**When to Use:**
- Only for testing/comparison
- If you need SPARQL-based discovery
- Currently used in: `test_artist_discovery_agent.py`, `test_real_pipeline.py`, etc.

**Key Difference:**
```python
# OLD WAY (ArtistDiscoveryAgent):
# 1. Query Wikidata SPARQL for artists by movement/concept
# 2. Complex SPARQL queries, slower, less reliable

# NEW WAY (SimpleArtistDiscovery):
# 1. Query Wikipedia for artist names by concept
# 2. Look up each artist individually
# 3. Faster, more reliable, better coverage
```

---

## Pipeline Flow

```
1. Curator Brief Input
   ↓
2. ThemeRefinementAgent → RefinedTheme
   ↓
3. SimpleArtistDiscovery → 30 artist candidates
   ↓
4. [CURATOR SELECTION POINT 1] → 15 selected artists
   ↓
5. ArtworkDiscoveryAgent → 100+ artwork candidates
   ↓
6. [CURATOR SELECTION POINT 2] → 50 selected artworks
   ↓
7. ArtworkEnrichmentAgent → Enriched metadata via Brave Search
   ↓
8. OrchestratorAgent → ExhibitionProposal with quality metrics
```

---

## Data Flow

```
CuratorBrief
  └─> ThemeRefinementAgent
      └─> RefinedTheme (validated concepts, Getty AAT URIs)
          └─> SimpleArtistDiscovery
              └─> List[Dict] raw artist data
                  └─> score_artist_relevance()
                      └─> List[DiscoveredArtist]
                          └─> [CURATOR SELECTS]
                              └─> ArtworkDiscoveryAgent
                                  └─> List[ArtworkCandidate]
                                      └─> [CURATOR SELECTS]
                                          └─> ArtworkEnrichmentAgent
                                              └─> Enriched List[ArtworkCandidate]
                                                  └─> ExhibitionProposal
```

---

## Agent Instantiation

**In OrchestratorAgent.__init__():**
```python
self.theme_agent = ThemeRefinementAgent(data_client)
self.artwork_agent = ArtworkDiscoveryAgent(data_client, anthropic_api_key)
self.enrichment_agent = ArtworkEnrichmentAgent()
# Note: SimpleArtistDiscovery created per-pipeline (not persistent)
```

**Why SimpleArtistDiscovery is not persistent:**
- Created fresh each pipeline run for better isolation
- Doesn't maintain state between runs
- Lighter weight than the SPARQL-based alternative

---

## API Dependencies

| Agent | Wikipedia | Wikidata | Yale LUX | Getty | Brave |
|-------|-----------|----------|----------|-------|-------|
| ThemeRefinement | ✓ | - | - | ✓ | - |
| SimpleArtist | ✓ | - | - | - | - |
| Artwork | - | ✓ | ✓ | - | - |
| Enrichment | - | - | - | - | ✓ |

---

## Summary

**Production Pipeline Uses:**
1. ✅ ThemeRefinementAgent
2. ✅ SimpleArtistDiscovery (NOT ArtistDiscoveryAgent!)
3. ✅ ArtworkDiscoveryAgent
4. ✅ ArtworkEnrichmentAgent
5. ✅ OrchestratorAgent

**Total: 4 specialized agents + 1 orchestrator = 5 active components**

Clean, focused, and efficient! 🎨
