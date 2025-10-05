# Architecture Pivot: Europeana-Centric Approach

## Strategic Insight

**User's breakthrough observation:**
> "Europeana has all the data we need when it comes to artworks. We want to know where the artwork is stalled, which type of object it is, we also get the images we need. It has everything. It's a complete app on itself, we only make it better."

## Current Architecture vs. Proposed Architecture

### ❌ Current Approach (Problem)

```
Free Text Input
    ↓
AI Generates Abstract Concepts (e.g., "dreams", "subconscious")
    ↓
Search 5 Data Sources (Wikipedia, Yale LUX, Wikidata, Europeana, Brave)
    ↓
Try to piece together: artist bio + artwork data + images + location
    ↓
Problem: Searching for what MIGHT exist, not what DOES exist
```

**Issues:**
- ❌ User might request theme with no available artworks
- ❌ 5 APIs = complexity, inconsistency, missing data
- ❌ Wikipedia finds "famous artists" but their work might not be loanable
- ❌ Free text = unpredictable results

### ✅ Proposed Approach (Europeana-Centric)

```
Structured Input with REAL Europeana Categories
    ↓
AI Refines Theme Using Europeana Taxonomy
    ↓
Artist Discovery via Europeana Entity API (shows AVAILABLE artists)
    ↓
Artwork Discovery via Europeana Search API (complete metadata)
    ↓
AI Adds Value: Quality scoring, narrative, logistics analysis
```

**Benefits:**
- ✅ Search what EXISTS in European collections
- ✅ Single source of truth = consistency
- ✅ Complete metadata: institution, location, object type, images, dimensions
- ✅ Europeana = 58M items from 3,000+ European museums
- ✅ Perfect for Van Bommel van Dam's modern/sculpture focus

## What Europeana Provides (Complete Package)

From EDM (Europeana Data Model):

| Data Type | EDM Field | What We Get |
|-----------|-----------|-------------|
| **Title** | dc:title | Artwork title (multi-lingual) |
| **Artist** | dc:creator, who: | Artist name + Entity API link |
| **Date** | dcterms:created, year: | Creation date/period |
| **Object Type** | proxy_dc_type | Sculpture, painting, installation, etc. |
| **Medium** | proxy_dc_format | Materials, technique |
| **Dimensions** | ebucoreWidth, ebucoreHeight | Pixel dimensions (images) |
| **Institution** | edm:dataProvider | Museum/collection name |
| **Location** | edm:Place | Geographic location |
| **Images** | edm:isShownBy, edm:object | High-res images + IIIF |
| **Thumbnail** | edmPreview | Thumbnail URL |
| **Rights** | edm:rights | Usage rights/license |
| **Description** | dc:description | Artwork description |
| **Country** | edm:country | Country of institution |
| **View URL** | edm:isShownAt | Link to institution page |

**Plus IIIF support:**
```
https://iiif.europeana.eu/presentation/{record-id}/manifest
```

## Redesigned Input Form (Structured with Europeana Categories)

### Phase 1: Exhibition Basics (Unchanged)
- Exhibition Title
- Target Audience
- Start/End Dates

### Phase 2: Structured Category Selection (NEW)

#### 1. Time Period (Single Select - Required)
Fetch from Europeana facets, prioritize for Van Bommel van Dam:
- ⭐ **Contemporary (1970-present)** ← Museum focus!
- Post-War Modern (1945-1970)
- Early Modern (1900-1945)
- 19th Century (1800-1900)
- Earlier periods...

#### 2. Art Movements (Multi-Select, Max 5)
From our Europeana topics knowledge base:
- ⭐ **Contemporary Art** ← Museum focus!
- ⭐ **Minimalism** ← Museum focus!
- ⭐ **Conceptual Art** ← Museum focus!
- ⭐ **Installation Art** ← Museum focus!
- Abstract Expressionism
- De Stijl (Dutch relevance)
- Pop Art
- Surrealism
- Expressionism
- Cubism
- etc.

#### 3. Media Types (Multi-Select, Max 5 - Required)
From Europeana proxy_dc_type facets:
- ⭐ **Sculpture** ← Museum focus!
- ⭐ **Installation** ← Museum focus!
- ⭐ **Mixed Media** ← Museum focus!
- Painting
- Photography
- Print/Etching
- Drawing
- Video Art
- Performance Documentation
- Textile/Fiber Art
- Ceramic

#### 4. Geographic Preference (Multi-Select, Optional)
From Europeana country facets:
- ⭐ **Netherlands** ← Museum location!
- Germany
- France
- Belgium
- United Kingdom
- Italy
- Spain
- Europe-wide

#### 5. Thematic Keywords (Free Text, Optional)
Now GUIDED by categories above:
- Example: "dreams", "reality", "perception"
- These enhance search but don't replace structured categories

### Phase 3: Theme Refinement (Enhanced)
AI validates theme against:
- ✅ Selected Europeana categories
- ✅ Available artworks count estimate
- ✅ Artist availability
- ✅ Geographic distribution

## New Data Flow

### Step 1: Form Submission
```json
{
  "exhibition_title": "Sculpting Time: Contemporary Dutch Forms",
  "time_period": "contemporary_1970_present",
  "art_movements": ["contemporary_art", "minimalism", "conceptual_art"],
  "media_types": ["sculpture", "installation", "mixed_media"],
  "geographic_preference": ["Netherlands", "Germany", "Belgium"],
  "thematic_keywords": "time, space, materiality, transformation"
}
```

### Step 2: Europeana Search Preview
Before full theme refinement, query Europeana to check availability:
```python
query = build_europeana_preview_query(form_data)
# Returns: "~1,200 artworks available from 45 museums"
```

### Step 3: Theme Refinement
AI generates:
- Central argument (using Europeana taxonomy terms)
- Exhibition sections (mapped to available artworks)
- Validated concepts (checked against Europeana Entity API)

### Step 4: Artist Discovery (Europeana Entity API)
```python
# Search artists by movement + availability
artists = search_europeana_entities(
    type="agent",  # Artist entities
    query="contemporary sculpture Netherlands",
    filters={
        "proxy_dc_type": "sculpture",
        "country": "Netherlands",
        "year": "[1970 TO 2025]"
    }
)
# Returns artists that have ACTUAL WORKS in European museums
```

### Step 5: Artwork Discovery (Europeana Search API)
```python
artworks = search_europeana_artworks(
    artists=selected_artists,
    media_types=["sculpture", "installation"],
    time_period="1970-2025",
    countries=["Netherlands", "Germany"]
)
# Returns complete metadata: institution, location, images, dimensions
```

## What AI Still Does (Adding Value)

Europeana provides the DATA. AI provides the INTELLIGENCE:

1. **Theme Coherence Analysis**
   - Does this combination of categories make curatorial sense?
   - Are there enough diverse artworks?

2. **Artist Selection Intelligence**
   - Which artists best represent the theme?
   - Balance between well-known and emerging
   - Geographic and gender diversity

3. **Quality Scoring**
   - Metadata completeness (from Europeana fields)
   - Image quality (IIIF availability)
   - Institution reputation

4. **Narrative Generation**
   - Opening wall text
   - Exhibition sections
   - Educational angles

5. **Logistical Feasibility**
   - Loan difficulty estimation
   - Geographic clustering for transport
   - Insurance value estimates

## Implementation Plan

### Phase 1: Fetch Europeana Facets ⬅️ START HERE
Create script to fetch ACTUAL available categories:
```python
# Get all available facets from Europeana
facets = fetch_europeana_facets([
    "proxy_dc_type",      # Media types
    "YEAR",               # Time periods
    "COUNTRY",            # Countries
    "DATA_PROVIDER",      # Museums
    "proxy_dc_format"     # Materials/formats
])

# Save as structured options for frontend form
```

### Phase 2: Redesign Frontend Form
Replace free text with structured selects:
- Time period dropdown
- Art movements multi-select (from our knowledge base)
- Media types multi-select (from Europeana facets)
- Geographic preference multi-select (from Europeana facets)
- Thematic keywords (still free text, but optional)

### Phase 3: Update Theme Refinement Agent
- Validate against Europeana taxonomy
- Check artwork availability via preview query
- Use Europeana Entity API for concept validation

### Phase 4: Update Artist Discovery
- Use Europeana Entity API as PRIMARY
- Wikipedia as SUPPLEMENTARY for biographies
- Filter by availability (must have works in Europeana)

### Phase 5: Update Artwork Discovery
- Use Europeana Search API as PRIMARY (possibly ONLY)
- Remove Yale LUX, Wikidata, Brave from artwork search
- Keep Wikipedia for artist context only

## Technical Benefits

### Simplified Architecture
```
BEFORE: 5 API clients, complex merging logic, inconsistent data
AFTER: 1 primary API (Europeana), consistent EDM data model
```

### Better User Experience
```
BEFORE: User inputs "dreams" → AI guesses → might find nothing
AFTER: User selects "Contemporary + Sculpture + Netherlands" → AI searches what EXISTS
```

### Perfect for Van Bommel van Dam
```
- Contemporary focus (1970+) ✅
- Sculpture emphasis ✅
- Installation art ✅
- European/Dutch collections ✅
- Modern materials & techniques ✅
```

## Success Metrics

After implementation:
- ✅ 95%+ search queries return viable results (vs. current ~60%?)
- ✅ 100% artworks have complete metadata (institution, location, images)
- ✅ 80%+ artworks have IIIF manifests for high-quality images
- ✅ Geographic concentration matches user preferences
- ✅ Form completion time reduced (structured vs. free text)

## Questions to Resolve

1. **Should we completely remove other APIs?**
   - Keep Wikipedia for artist biographies only?
   - Keep Yale LUX for international loans only?
   - Or go 100% Europeana?

2. **How to handle non-Europeana artworks?**
   - If curator wants MoMA artwork not in Europeana?
   - Manual addition option?

3. **Europeana Entity API usage**
   - How well does it work for artist discovery?
   - Need to test retrieval quality

## Next Steps

1. ✅ Completed: Europeana topics knowledge base
2. 🔄 **Fetch actual Europeana facets** (CRITICAL)
3. 🔄 **Test Europeana Entity API** for artist discovery
4. 🔄 **Redesign input form** with structured selects
5. 🔄 **Update theme refinement** to validate against Europeana
6. 🔄 **Simplify data sources** (Europeana-primary)

---

**Bottom Line:** We're not building a generic art database. We're building a **curated exhibition assistant for a specific modern art museum**. Europeana's data matches Van Bommel van Dam's needs perfectly. Let's build around what EXISTS, not what's theoretically possible.
