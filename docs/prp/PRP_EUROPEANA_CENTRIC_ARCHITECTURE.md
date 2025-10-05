# Product Requirements Prompt (PRP)
# Europeana-Centric AI Curator Architecture

**Project**: Museum van Bommel van Dam - AI Curator Assistant v2
**Date**: 2025-10-04
**Status**: Ready for Implementation
**Priority**: High
**Estimated Duration**: 3-4 weeks

---

## Executive Summary

Transform the AI Curator Assistant to use **Europeana-first architecture** for discovering artists and artworks. This architectural pivot ensures we find **all available artists** (famous + emerging + regional) based on **actual loanable works** in European collections, making the system perfectly suited for Museum van Bommel van Dam's contemporary/modern art focus.

### Vision Statement

> "Build an AI curator that recommends exhibitions based on what's ACTUALLY available in European museums, not just what's theoretically famous. Discover emerging artists alongside established ones, prioritize contemporary and regional art, and ensure every recommendation is backed by loanable artworks."

### Key Success Metrics

- ✅ 95%+ of recommended artists have available works in Europeana
- ✅ 40%+ of discovered artists are contemporary/regional (not just historically famous)
- ✅ 100% of artworks have complete metadata (institution, location, images)
- ✅ 80%+ of artworks have IIIF manifests for high-quality images
- ✅ Form completion reduces curator workload by 60%

---

## Problem Statement

### Current Issues

1. **Wikipedia-first architecture misses emerging artists**
   - Contemporary Dutch sculptors with 50+ loanable works are never discovered
   - Regional European artists not famous enough for Wikipedia are invisible
   - System biased toward historical/famous artists

2. **Multiple data sources create inconsistency**
   - 5 different APIs (Wikipedia, Yale LUX, Wikidata, Europeana, Brave)
   - Incomplete data pieced together from multiple sources
   - No guarantee of availability

3. **Free-text input produces unpredictable results**
   - Curator enters "dreams and reality" → system searches for abstract concepts
   - Might return 0 results if nothing matches
   - No guidance on what's actually available

4. **Not optimized for Van Bommel van Dam's focus**
   - Museum specializes in: contemporary art, sculpture, installations, modern works
   - Current system optimized for: paintings, historical art, famous artists

### User Impact

- 😞 Curators waste time researching artists not available for loan
- 😞 Emerging regional artists never get discovered
- 😞 Exhibition proposals lack feasibility (based on unavailable works)
- 😞 Manual verification of availability required for every artist/artwork

---

## Solution Overview

### Europeana-First Architecture

**Core Principle**: Start with what EXISTS in European collections, not with what's theoretically famous.

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Structured Input                                   │
│ Form with real categories (not free text)                   │
│ • Time Period: Contemporary (1970-present)                  │
│ • Movements: Minimalism, Contemporary Art, Conceptual       │
│ • Media: Sculpture, Installation, Mixed Media               │
│ • Geography: Netherlands, Germany, Belgium                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Theme Refinement                                   │
│ AI validates & enriches theme using Europeana taxonomy      │
│ • Checks availability (preview query)                       │
│ • Suggests adjustments if too narrow                        │
│ • Validates concepts against actual available works         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Artwork Discovery (EUROPEANA-FIRST!)               │
│ Broad search in Europeana based on criteria                 │
│ Query: "sculpture installation contemporary Netherlands"    │
│ Filters: TYPE:IMAGE, YEAR:[1970 TO 2025]                   │
│ Returns: 500-1000 artworks with complete metadata           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Artist Extraction & Ranking                        │
│ Extract all artists FROM artwork results                    │
│ • Parse dcCreator from each artwork                         │
│ • Group by artist (aggregate works)                         │
│ • Rank by: work count, IIIF %, institutions, period match  │
│ • Filter: minimum 3 works, exclude "Unknown"                │
│ Result: 50-200 ranked artists with availability proof       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: Artist Enrichment (Wikipedia OPTIONAL)             │
│ For top 50 artists, try Wikipedia lookup                    │
│ • Found: Add rich biography ✅                              │
│ • Not found: Use Europeana metadata ✅                      │
│ • Emerging artists: Show with available data                │
│ Result: All artists enriched with best available data       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: Curator Selection                                  │
│ Present ranked artists to curator for final selection       │
│ • Top 20 with rich data (works, images, institutions)       │
│ • All have verified availability                            │
│ • Mix of famous + emerging + regional                       │
│ • Curator selects 15 for exhibition                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: Artwork Selection & Exhibition Generation          │
│ Select artworks from chosen artists                         │
│ • 50-100 artworks across 15 artists                         │
│ • IIIF images for all                                       │
│ • Complete metadata (institution, location, rights)         │
│ • Generate exhibition proposal with quality metrics         │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

### Data Sources (Simplified)

| Source | Purpose | Priority |
|--------|---------|----------|
| **Europeana API** | Artworks & artist discovery | PRIMARY |
| **Wikipedia API** | Artist biographies (enrichment) | SUPPLEMENTARY |
| ~~Yale LUX~~ | ~~US collections~~ | REMOVED |
| ~~Wikidata~~ | ~~Structured data~~ | REMOVED |
| ~~Brave Search~~ | ~~Web search~~ | REMOVED |

**Rationale**: Europeana provides complete metadata (institution, location, images, rights) for European collections. Wikipedia adds biographies where available but isn't required.

### API Integration Details

#### Europeana Search API

**Endpoint**: `https://api.europeana.eu/record/v2/search.json`

**Query Strategy** (Broad queries, minimal filters):
```python
# ✅ CORRECT (Broad query, minimal filters)
params = {
    'wskey': api_key,
    'query': 'sculpture installation contemporary Netherlands',
    'qf': [
        'TYPE:IMAGE',
        'YEAR:[1970 TO 2025]'
    ],
    'rows': 100,
    'profile': 'rich',
    'media': 'true',
    'thumbnail': 'true'
}

# ❌ WRONG (Over-filtered, returns 0 results)
params = {
    'query': 'sculpture',
    'qf': [
        'COUNTRY:Netherlands',           # Too restrictive!
        'proxy_dc_type:sculpture',       # Too restrictive!
        'YEAR:[1970 TO 2025]'
    ]
}
```

**Key Learning from Tests**:
- Broad queries work better than restrictive filters
- Use main query for content matching
- Use qf filters minimally (TYPE, YEAR only)
- Post-filter results in application code

**Response Structure** (verified from tests):
```json
{
  "items": [
    {
      "id": "/180/10622_E6EBF995_C8FE_458E_8492_AF8AEB2105C9_cho",
      "title": ["Sculpture au Panthéon"],
      "dcCreator": ["Artist Name"],
      "dcDescription": ["Description..."],
      "year": ["1990"],
      "type": "IMAGE",
      "dataProvider": ["Museum Name"],
      "country": ["Netherlands"],
      "edmPreview": ["https://api.europeana.eu/thumbnail/v2/..."],
      "edmIsShownBy": ["http://hdl.handle.net/..."],
      "edmIsShownAt": ["http://institution.url/..."],
      "rights": ["http://rightsstatements.org/vocab/InC/1.0/"],
      "dcSubject": {"en": ["Sculpture", "Contemporary Art"]},
      "dcType": {"en": ["Sculpture", "Installation"]},
      "edmPlace": "http://data.europeana.eu/place/85",
      "edmTimespan": "1970/2025"
    }
  ],
  "totalResults": 1500
}
```

**IIIF Manifest Construction**:
```python
def construct_iiif_manifest(europeana_id: str) -> str:
    record_id = europeana_id.lstrip('/')
    return f"https://iiif.europeana.eu/presentation/{record_id}/manifest"

# Test result: 100% IIIF availability confirmed!
```

#### Wikipedia API

**Endpoint**: `https://en.wikipedia.org/w/api.php`

**Purpose**: Artist biography enrichment (OPTIONAL)

**Query Pattern**:
```python
params = {
    'action': 'query',
    'format': 'json',
    'titles': artist_name,
    'prop': 'extracts|pageimages',
    'exintro': True,
    'explaintext': True
}
```

**Fallback Strategy** (if Wikipedia not found):
```python
# Use Europeana metadata
artist_data = {
    'name': dcCreator_value,
    'estimated_active_period': f"{min_year}-{max_year}",  # From artworks
    'nationality': infer_from_institutions(),  # From dataProvider countries
    'media_expertise': extract_from_dcType(),  # From artwork types
    'works_count': len(artworks),
    'institutions': list(unique_institutions),
    'biography': "Limited biographical data available. Known for works in European collections."
}
```

---

## Data Models

### Exhibition Input Form

```typescript
interface ExhibitionInput {
  // Basic Information
  title: string;                    // "Sculpting Time: Dutch Contemporary Forms"
  audience: string;                 // "Art enthusiasts, students"
  startDate?: Date;
  endDate?: Date;

  // Structured Categories (from europeana_topics.py)
  timePeriod: TimePeriod;          // Required
  artMovements: ArtMovement[];     // Required, max 5
  mediaTypes: MediaType[];         // Required, max 5
  geographicFocus?: Country[];     // Optional

  // Free Text (guided by above)
  thematicKeywords?: string;       // "time, transformation, materiality"
}

enum TimePeriod {
  CONTEMPORARY_1970 = "contemporary_1970_present",
  POSTWAR_1945 = "postwar_1945_1970",
  EARLY_MODERN_1900 = "early_modern_1900_1945",
  NINETEENTH_1800 = "nineteenth_century_1800_1900",
  EARLIER = "earlier_periods"
}

enum ArtMovement {
  CONTEMPORARY_ART = "contemporary_art",
  MINIMALISM = "minimalism",
  CONCEPTUAL_ART = "conceptual_art",
  INSTALLATION_ART = "installation_art",
  DE_STIJL = "de_stijl",
  ABSTRACT_EXPRESSIONISM = "abstract_expressionism",
  POP_ART = "pop_art",
  SURREALISM = "surrealism",
  // ... (30+ movements from europeana_topics.py)
}

enum MediaType {
  SCULPTURE = "sculpture",
  INSTALLATION = "installation",
  MIXED_MEDIA = "mixed_media",
  PAINTING = "painting",
  PHOTOGRAPHY = "photography",
  PRINT = "print",
  DRAWING = "drawing",
  VIDEO_ART = "video_art",
  PERFORMANCE = "performance_art",
  TEXTILE = "textile",
  CERAMIC = "ceramic"
}

enum Country {
  NETHERLANDS = "Netherlands",
  GERMANY = "Germany",
  BELGIUM = "Belgium",
  FRANCE = "France",
  UNITED_KINGDOM = "United Kingdom",
  // ... all European countries
}
```

### Artist Model (Europeana-First)

```typescript
interface Artist {
  // Core Identity
  name: string;                          // From dcCreator

  // Availability Data (PRIMARY - from Europeana)
  availability: {
    totalWorks: number;                  // Count of artworks in Europeana
    artworks: EuropeanaArtwork[];        // Array of available works
    institutions: Institution[];         // Museums holding works
    iiifAvailability: number;            // Percentage (0-100)
    geographicDistribution: {            // Where works are located
      [country: string]: number;
    };
    mediaTypes: string[];                // sculpture, installation, etc.
    timePeriodCoverage: {
      earliest: number;                  // 1985
      latest: number;                    // 2023
    };
  };

  // Quality Score (calculated)
  qualityScore: {
    total: number;                       // 0-100
    breakdown: {
      availabilityScore: number;         // Based on works count
      iiifScore: number;                 // Based on IIIF %
      institutionDiversityScore: number; // Based on # institutions
      timePeriodMatchScore: number;      // Based on theme match
    };
  };

  // Enrichment Data (OPTIONAL - from Wikipedia if available)
  enrichment?: {
    source: 'wikipedia' | 'europeana_metadata';
    biography?: string;                  // Full bio if Wikipedia found
    birthYear?: number;
    deathYear?: number;
    nationality?: string;
    movements?: string[];
    majorWorks?: string[];
    wikipediaUrl?: string;
    portraitUrl?: string;
  };

  // Fallback Metadata (from Europeana if no Wikipedia)
  metadata: {
    estimatedActivePeriod: string;       // "1985-2023"
    inferredNationality?: string;        // From institution countries
    mediaExpertise: string[];            // From dcType analysis
  };

  // Selection Status
  selected: boolean;
  selectionReason?: string;              // AI-generated explanation
}
```

### Artwork Model (Complete Europeana Data)

```typescript
interface EuropeanaArtwork {
  // Europeana IDs
  id: string;                            // "/180/10622_..."
  europeanaUrl: string;                  // "https://www.europeana.eu/item/..."

  // Core Metadata
  title: string;
  artist: string;                        // From dcCreator
  dateCreated: string;                   // "1990" or "1985-1990"
  year?: number;                         // Parsed year

  // Object Information
  objectType: string[];                  // From dcType: ["Sculpture", "Installation"]
  medium?: string[];                     // From dcFormat
  description?: string;                  // From dcDescription
  subjects: string[];                    // From dcSubject

  // Institution & Location
  institution: string;                   // From dataProvider
  institutionUrl?: string;               // From edmIsShownAt
  country: string;
  city?: string;                         // From edmPlace if available

  // Images
  thumbnailUrl: string;                  // From edmPreview
  imageUrl?: string;                     // From edmIsShownBy
  iiifManifest?: string;                 // Constructed from ID

  // Rights
  rights: string;                        // "http://rightsstatements.org/..."
  rightsLabel?: string;                  // Human-readable

  // Quality Metrics
  completenessScore: number;             // 0-100 based on metadata fields
  iiifAvailable: boolean;

  // Relevance
  relevanceScore?: number;               // Match to exhibition theme
  relevanceReasoning?: string;           // AI explanation

  // Selection
  selected: boolean;
}
```

---

## Implementation Tasks

### Task Breakdown (for Archon)

#### EPIC 1: Input Form Redesign (Frontend)
**Estimated**: 4-5 days

**Task 1.1**: Create structured form components
- Time period dropdown (single select)
- Art movements multi-select (max 5, searchable)
- Media types multi-select (max 5, searchable)
- Geographic focus multi-select (optional, searchable)
- Thematic keywords text area (optional)
- Remove old free-text fields

**Task 1.2**: Populate form options from europeana_topics.py
- Create API endpoint to serve categories
- Map backend enums to frontend options
- Add helpful descriptions for each category
- Implement category icons/visual aids

**Task 1.3**: Add form validation & UX
- Require: time period, movements (min 1), media types (min 1)
- Limit: movements (max 5), media types (max 5)
- Show character count for keywords
- Preview query builder (show what will be searched)

**Task 1.4**: Update demo pages
- Update `/demo/theme` to use new form structure
- Maintain museum branding (Van Bommel colors)
- Ensure responsive design

---

#### EPIC 2: Europeana-First Artist Discovery (Backend)
**Estimated**: 6-7 days

**Task 2.1**: Implement broad artwork search
- Create `search_artworks_by_theme()` function
- Build query from structured input
- Use broad query strategy (minimal filters)
- Request 500-1000 results
- Handle pagination if needed

**Task 2.2**: Implement artist extraction & aggregation
- Parse dcCreator from all artworks
- Handle different name formats (Last, First / First Last / URI)
- Filter out "Unknown", "Various", URIs without names
- Group artworks by normalized artist name
- Count works per artist

**Task 2.3**: Implement artist quality scoring
- Calculate availability score (works count weighted)
- Calculate IIIF score (percentage with IIIF)
- Calculate institution diversity score
- Calculate time period match score
- Combine into total score (0-100)

**Task 2.4**: Implement ranking & filtering
- Sort artists by quality score
- Filter: minimum 3 works required
- Filter: exclude artists with >80% "Unknown" works
- Return top 50-100 artists

**Task 2.5**: Add logging & metrics
- Log artist extraction results
- Track parsing failures
- Monitor quality score distribution
- Alert if <10 artists found

---

#### EPIC 3: Wikipedia Enrichment (Backend)
**Estimated**: 3-4 days

**Task 3.1**: Implement Wikipedia lookup
- Search Wikipedia by artist name
- Handle disambiguation pages
- Extract biography, dates, movements
- Extract portrait image if available
- Cache results to avoid re-fetching

**Task 3.2**: Implement enrichment fallback
- If Wikipedia not found, use Europeana metadata
- Calculate estimated active period from artwork dates
- Infer nationality from institution countries
- Extract media expertise from dcType analysis
- Create basic biography text

**Task 3.3**: Batch processing optimization
- Enrich top 50 artists in parallel
- Set timeout per artist (5 seconds max)
- Continue if some fail (don't block on errors)
- Track success rate (target: 30-50% Wikipedia found)

---

#### EPIC 4: Theme Refinement Update (Backend)
**Estimated**: 3-4 days

**Task 4.1**: Update theme refinement agent
- Accept structured input (not free text)
- Use Europeana taxonomy for validation
- Check availability with preview query
- Suggest adjustments if too narrow (<20 artworks)

**Task 4.2**: Implement availability preview
- Query Europeana with theme criteria
- Get total count (don't fetch all items)
- Return: "~1,200 artworks available from 45 museums"
- Warn if <50 artworks (too narrow)

**Task 4.3**: Update concept validation
- Validate art movements against Europeana taxonomy
- Validate media types against available data
- Validate time periods for consistency

---

#### EPIC 5: Updated Data Flow Integration (Backend)
**Estimated**: 4-5 days

**Task 5.1**: Update session manager
- Store structured input (not free text)
- Track Europeana-first workflow state
- Handle artist extraction progress
- Store enrichment results

**Task 5.2**: Update WebSocket messages
- Send artist extraction progress
- Send enrichment progress
- Send quality scores as calculated
- Update frontend in real-time

**Task 5.3**: Update orchestrator agent
- Coordinate new workflow phases
- Handle Europeana-first discovery
- Manage Wikipedia enrichment
- Generate final exhibition proposal

**Task 5.4**: Error handling & recovery
- Handle Europeana API failures
- Handle Wikipedia API failures
- Graceful degradation (show what we have)
- Retry logic for transient failures

---

#### EPIC 6: Artist Presentation (Frontend)
**Estimated**: 3-4 days

**Task 6.1**: Update artists page UI
- Show quality scores prominently
- Display availability metrics (works count, institutions)
- Show enrichment source (Wikipedia vs. Europeana)
- Indicate emerging vs. established artists

**Task 6.2**: Implement artist filtering
- Filter by quality score
- Filter by works count
- Filter by Wikipedia availability
- Filter by nationality

**Task 6.3**: Add "Why this artist?" explanations
- AI-generated relevance reasoning
- Show theme match
- Show availability proof
- Highlight unique contributions

---

#### EPIC 7: Testing & Validation
**Estimated**: 3-4 days

**Task 7.1**: Unit tests for artist extraction
- Test dcCreator parsing (various formats)
- Test artist aggregation
- Test quality scoring
- Test filtering logic

**Task 7.2**: Integration tests for workflow
- Test full Europeana-first flow
- Test Wikipedia enrichment
- Test fallback scenarios
- Test error handling

**Task 7.3**: E2E tests for user scenarios
- Test: Contemporary Dutch sculpture
- Test: Installation art
- Test: Surrealism theme
- Verify: >0 results for all scenarios

**Task 7.4**: Performance testing
- Test with 1000 artworks
- Test with 200 artists
- Test parallel Wikipedia enrichment
- Target: <30 seconds total workflow

---

#### EPIC 8: Documentation & Deployment
**Estimated**: 2-3 days

**Task 8.1**: Update API documentation
- Document new endpoints
- Document data models
- Document query strategies
- Add examples

**Task 8.2**: Update user guide
- Document new form structure
- Explain Europeana-first approach
- Explain quality scores
- Add troubleshooting

**Task 8.3**: Deployment & monitoring
- Deploy to production
- Set up monitoring
- Track error rates
- Monitor API usage

---

## Success Criteria

### Functional Requirements

✅ **FR1**: Form accepts structured input (time period, movements, media, geography)
✅ **FR2**: System discovers 50-200 artists from Europeana artworks
✅ **FR3**: 100% of recommended artists have available works
✅ **FR4**: Wikipedia enrichment works for 30-50% of artists
✅ **FR5**: Fallback metadata works for artists without Wikipedia
✅ **FR6**: Quality scoring ranks artists by availability
✅ **FR7**: IIIF manifests available for 80%+ artworks
✅ **FR8**: Complete metadata for all artworks (institution, location, rights)

### Non-Functional Requirements

✅ **NFR1**: Artist discovery completes in <30 seconds
✅ **NFR2**: Wikipedia enrichment completes in <20 seconds (50 artists)
✅ **NFR3**: System handles Europeana API failures gracefully
✅ **NFR4**: Real-time progress updates via WebSocket
✅ **NFR5**: Mobile-responsive form design

### User Experience Goals

✅ **UX1**: Curator completes form in <5 minutes
✅ **UX2**: System explains "why this artist?" for each recommendation
✅ **UX3**: Curator can filter/sort by quality metrics
✅ **UX4**: Clear indication of emerging vs. established artists
✅ **UX5**: Availability proof shown (works count, institutions)

---

## Testing Strategy

### Test Scenarios (Van Bommel van Dam Focus)

**Scenario 1: Contemporary Dutch Sculpture**
```
Input:
  - Time Period: Contemporary (1970-present)
  - Movements: Contemporary Art, Minimalism
  - Media: Sculpture, Installation
  - Geography: Netherlands

Expected:
  - 50+ artists discovered
  - Mix of established + emerging
  - 200+ artworks available
  - Quality scores distributed 40-100
```

**Scenario 2: Installation Art (European)**
```
Input:
  - Time Period: Contemporary (1970-present)
  - Movements: Installation Art, Conceptual Art
  - Media: Installation, Mixed Media
  - Geography: Netherlands, Germany, Belgium

Expected:
  - 100+ artists discovered
  - Strong representation from regional museums
  - 500+ artworks available
  - High IIIF availability (>90%)
```

**Scenario 3: Surrealism (Historical)**
```
Input:
  - Time Period: Early Modern (1900-1945)
  - Movements: Surrealism
  - Media: Painting, Sculpture, Photography
  - Geography: Europe-wide

Expected:
  - 30+ artists discovered
  - Higher Wikipedia coverage (>60%)
  - 150+ artworks available
  - Famous artists ranked high (Dalí, Magritte, etc.)
```

### Acceptance Criteria

For each test scenario, verify:
1. ✅ System returns >0 artists
2. ✅ All artists have ≥3 available works
3. ✅ Quality scores calculated correctly
4. ✅ Wikipedia enrichment attempted for top 50
5. ✅ Fallback metadata populated for non-Wikipedia artists
6. ✅ IIIF manifests available for ≥80% artworks
7. ✅ Institution/location data present for all artworks
8. ✅ Workflow completes in <60 seconds

---

## Risks & Mitigation

### Risk 1: dcCreator Parsing Failures
**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Comprehensive name parsing logic
- Handle multiple formats (Last, First / First Last / URI)
- Track parsing failures for analysis
- Manual curator override for edge cases

### Risk 2: Low Wikipedia Coverage
**Impact**: Low (expected)
**Probability**: High (60-70% won't have Wikipedia)
**Mitigation**:
- This is EXPECTED and acceptable
- Fallback to Europeana metadata works well
- Focus on availability, not biography richness
- Clearly indicate enrichment source to curator

### Risk 3: Europeana API Rate Limits
**Impact**: High
**Probability**: Low
**Mitigation**:
- Implement exponential backoff
- Cache results aggressively
- Use pagination efficiently
- Monitor API usage

### Risk 4: Over-Broad Queries Return Too Many Artists
**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Limit to top 100 artists by quality score
- Allow curator to filter/refine
- Implement smart ranking
- Set minimum works threshold (3+)

---

## Dependencies

### External APIs
- ✅ Europeana API (key already configured)
- ✅ Wikipedia API (public, no key required)

### Internal Components
- ✅ `europeana_topics.py` (knowledge base exists)
- ✅ `essential_data_client.py` (Europeana integration exists)
- ⚠️ Theme refinement agent (needs update)
- ⚠️ Orchestrator agent (needs update)
- ⚠️ Input form (needs redesign)

### Infrastructure
- ✅ WebSocket server (exists)
- ✅ Session manager (exists)
- ✅ Frontend (Next.js, exists)
- ✅ Backend (FastAPI, exists)

---

## Timeline & Milestones

### Week 1: Foundation
- ✅ Input form redesign (Epic 1)
- ✅ Europeana-first artist discovery (Epic 2, Tasks 2.1-2.3)

**Milestone 1**: Form can submit structured input, basic artist extraction works

### Week 2: Core Functionality
- ✅ Complete artist discovery (Epic 2, Tasks 2.4-2.5)
- ✅ Wikipedia enrichment (Epic 3)
- ✅ Theme refinement update (Epic 4)

**Milestone 2**: Full artist discovery with enrichment working end-to-end

### Week 3: Integration & Polish
- ✅ Data flow integration (Epic 5)
- ✅ Artist presentation UI (Epic 6)
- ✅ Testing (Epic 7, Tasks 7.1-7.3)

**Milestone 3**: Complete workflow functional, tested with real scenarios

### Week 4: Finalization
- ✅ Performance testing (Epic 7, Task 7.4)
- ✅ Documentation (Epic 8)
- ✅ Deployment & monitoring
- ✅ Final validation

**Milestone 4**: Production ready, deployed, monitored

---

## Open Questions

1. **Should we cache artist enrichment data?**
   - Pro: Faster repeat queries
   - Con: Wikipedia data might be outdated
   - **Decision needed**: Cache duration (7 days? 30 days?)

2. **How to handle artists with works in multiple countries?**
   - Should we prioritize Dutch museums for Dutch exhibition?
   - Or show all available works regardless of location?
   - **Decision needed**: Geographic preference weight in scoring

3. **Minimum works threshold**
   - Current: 3 works minimum
   - Should we make this configurable by curator?
   - **Decision needed**: Hardcode vs. configurable

4. **Wikipedia disambiguation handling**
   - If "Jan de Moderne" has multiple Wikipedia pages
   - How to choose correct one?
   - **Decision needed**: Use artist dates from artworks to disambiguate

---

## Appendix

### A. Tested Europeana Query Examples

```python
# Contemporary Dutch Sculpture (ISSUE: 0 results with strict filters)
# ❌ Over-filtered:
{
    'query': 'sculpture',
    'qf': ['COUNTRY:Netherlands', 'proxy_dc_type:sculpture', 'YEAR:[1970 TO 2025]']
}

# ✅ Better approach:
{
    'query': 'sculpture contemporary Netherlands',
    'qf': ['TYPE:IMAGE', 'YEAR:[1970 TO 2025]'],
    'rows': 100
}

# Installation Art (SUCCESS: 3,521 results)
{
    'query': 'installation',
    'qf': ['YEAR:[1960 TO 2025]', 'TYPE:IMAGE'],
    'rows': 100
}

# Surrealism (SUCCESS: 150 results)
{
    'query': 'surrealism OR surrealist',
    'qf': ['TYPE:IMAGE', 'YEAR:[1920 TO 1970]'],
    'rows': 100
}
```

### B. Artist Extraction Examples

```python
# Example dcCreator values encountered:
dcCreator_examples = [
    "Mondrian, Piet",                              # Last, First format
    "Salvador Dalí",                               # First Last format
    "http://data.europeana.eu/agent/56309",       # URI only (need to skip)
    "Unknown",                                     # Skip
    "Various artists",                             # Skip
    "van Doesburg, Theo",                         # With prefix
]

# Parsing strategy:
def normalize_artist_name(dcCreator):
    if dcCreator.startswith('http://'):
        return None  # Skip URIs
    if dcCreator.lower() in ['unknown', 'various', 'various artists']:
        return None  # Skip unknowns

    # Handle "Last, First" format
    if ',' in dcCreator:
        parts = dcCreator.split(',')
        return f"{parts[1].strip()} {parts[0].strip()}"

    return dcCreator.strip()
```

### C. Quality Score Calculation

```python
def calculate_quality_score(artist_data):
    """
    Calculate 0-100 quality score for artist

    Components:
    - Availability: 40% weight (based on works count)
    - IIIF: 30% weight (based on IIIF percentage)
    - Institution diversity: 20% weight
    - Time period match: 10% weight
    """

    # Availability score (0-40 points)
    works_count = len(artist_data['artworks'])
    availability_score = min(40, works_count * 2)  # Cap at 40

    # IIIF score (0-30 points)
    iiif_percentage = artist_data['iiif_availability']
    iiif_score = iiif_percentage * 0.3

    # Institution diversity (0-20 points)
    num_institutions = len(artist_data['institutions'])
    institution_score = min(20, num_institutions * 4)  # Cap at 20

    # Time period match (0-10 points)
    period_match = calculate_period_match(artist_data, theme_period)

    total = availability_score + iiif_score + institution_score + period_match
    return round(total, 1)
```

### D. Wikipedia Enrichment Flow

```python
async def enrich_artist_with_wikipedia(artist_name):
    """
    Try to enrich artist with Wikipedia data
    Falls back to Europeana metadata if not found
    """

    # Step 1: Try Wikipedia search
    wikipedia_data = await search_wikipedia(artist_name)

    if wikipedia_data:
        return {
            'source': 'wikipedia',
            'biography': wikipedia_data['extract'],
            'birthYear': wikipedia_data.get('birth_year'),
            'deathYear': wikipedia_data.get('death_year'),
            'nationality': wikipedia_data.get('nationality'),
            'movements': wikipedia_data.get('movements', []),
            'wikipediaUrl': wikipedia_data['url'],
            'portraitUrl': wikipedia_data.get('image_url')
        }

    # Step 2: Fallback to Europeana metadata
    artworks = artist_data['artworks']
    years = [a['year'] for a in artworks if a.get('year')]

    return {
        'source': 'europeana_metadata',
        'estimatedActivePeriod': f"{min(years)}-{max(years)}",
        'inferredNationality': infer_nationality(artworks),
        'mediaExpertise': extract_media_types(artworks),
        'biography': f"Artist active {min(years)}-{max(years)}. Known for works in {len(set([a['dataProvider'] for a in artworks]))} European institutions."
    }
```

---

## Conclusion

This PRP outlines a comprehensive transformation to **Europeana-first architecture** that will:

✅ Discover emerging & regional artists (not just famous ones)
✅ Ensure 100% availability (all recommended works are loanable)
✅ Optimize for Van Bommel van Dam's contemporary/sculpture focus
✅ Simplify architecture (reduce from 5 APIs to effectively 2)
✅ Improve curator experience (structured input, proven availability)
✅ Maintain quality (IIIF images, complete metadata, rich enrichment)

**Next Steps**: Load this PRP into Archon, create tasks from epics, and begin implementation starting with Epic 1 (Input Form Redesign).

**Estimated Delivery**: 3-4 weeks for full implementation and testing.

---

**Prepared by**: AI Curator Development Team
**Reviewed by**: [Pending]
**Approved by**: [Pending]
**Version**: 1.0
**Last Updated**: 2025-10-04
