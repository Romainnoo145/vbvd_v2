# Workflow Analyse: Optimale Artist Discovery Strategie

## Curator Input (Minimaal)
```
Thema: "Dutch Golden Age domestic life"
Concepten: ["still life", "genre painting", "chiaroscuro"]
Diversiteit: min 3 female, min 2 non-Western
```

## Vraag: Wat is de BESTE volgorde?

### OPTIE 1: Huidige Aanpak (Concept-First)
```
Curator Input
    ↓
Getty AAT: Valideer concepten
    ↓
Wikidata SPARQL: Zoek artists via concept-links
    - ?artist wdt:P135 ?movement (movement = concept)
    - ?artist wdt:P136 ?genre (genre = concept)
    ↓
Probleem: Te specifiek, weinig matches
```

**Probleem gevonden:**
- "Dutch Golden Age" is geen Wikidata movement
- "Contemporary art" is te breed als movement
- Concept-based search werkt alleen voor ZEER specifieke termen (Impressionism, Cubism)

---

### OPTIE 2: Movement-First (Slimmer)
```
Curator Input
    ↓
LLM: Vertaal thema → bekende art movements
    Input: "Dutch Golden Age domestic life"
    Output: ["Dutch Golden Age painting", "Baroque", "Genre painting"]
    ↓
Wikidata: Haal ALLE artists op per movement
    ↓
Post-filter: Relevance scoring + diversity
    ↓
Top N artists
```

**Voordelen:**
- Werkt met bestaande Wikidata taxonomie
- Veel meer matches
- Kan diversity al in SPARQL filteren

---

### OPTIE 3: Hybrid (BESTE - Gebruik meerdere bronnen)
```
Curator Input
    ↓
Parallel zoeken:

    PATH 1: Getty AAT → Wikidata (Concept-based)
    PATH 2: Reference artists → Related artists via Wikidata
    PATH 3: LLM suggests movements → Wikidata movement search
    PATH 4: Wikipedia categories → Extract artist names
    PATH 5: Yale LUX direct search op keywords
    ↓
Merge & deduplicate
    ↓
Enrich with biographical data
    ↓
Score: Relevance (60%) + Diversity (20%) + Data completeness (20%)
    ↓
Diversity-aware ranking
    ↓
Top N artists
```

---

## Waarom Wikidata First?

### ✅ Goede Redenen:
1. **Gestructureerde data** - Properties (birth, death, gender, movement)
2. **Link naar andere bronnen** - Getty ULAN, VIAF, Wikipedia
3. **Gratis & open** - Geen API keys nodig
4. **Meest complete** - 100M+ entities
5. **SPARQL power** - Complexe queries mogelijk

### ❌ Maar ook nadelen:
1. **Te gedetailleerd** - Taxonomie matcht niet altijd met curatorial language
2. **Incomplete voor moderne kunst** - Vooral historische data
3. **Query complexity** - Moeilijk om "fuzzy" concepten te vangen
4. **Slow** - SPARQL kan timeout bij complexe queries

---

## Aanbevolen: VERBETERDE WORKFLOW

### Stage 1: Theme Intelligence (NEW)
```python
Input: "Dutch Golden Age domestic life"

Step 1.1: LLM Concept Expansion
    → Extract: periods, styles, movements, themes, geographies
    → "17th century Dutch painting, genre painting, still life,
       domestic interiors, Baroque, Dutch Golden Age"

Step 1.2: Multi-source Concept Validation
    - Getty AAT: "genre painting" → aat:300139140
    - Wikidata: "Dutch Golden Age" → Q661566
    - Wikipedia: Extract categories and related terms

Step 1.3: Build Search Strategy
    Decision tree:
    - IF reference_artists exist → Use related artists
    - IF time period known → Use temporal + geographic filters
    - IF movement known → Use movement-based search
    - ELSE → Use hybrid keyword + category search
```

### Stage 2: Multi-Path Artist Discovery (IMPROVED)
```python
Parallel Paths:

PATH A: Wikidata Movement Search (Fast, high precision)
    Query: Get all artists with movement = "Dutch Golden Age"
    Filter: Add gender/nationality in SPARQL
    Limit: 100 per movement

PATH B: Wikidata Related Artists (High relevance)
    IF reference_artists:
        Query: Get influenced_by, student_of, contemporary_of
        Expand: 2 degrees of separation

PATH C: Wikidata Keyword Search (Broad coverage)
    Query: Text search in artist descriptions
    Filter: Time period, nationality constraints

PATH D: Wikipedia Category Mining (Backup)
    Extract: "Category:Dutch Golden Age painters"
    Match: To Wikidata entities

PATH E: Yale LUX Direct (For institutional presence)
    Search: Theme keywords in collection
    Extract: Artist names from results

→ Merge results (weight by source quality)
→ Deduplicate by Wikidata ID
→ Enrich: Getty ULAN, Wikipedia biographies
```

### Stage 3: Intelligent Ranking (IMPROVED)
```python
For each artist, calculate:

Relevance Score (60%):
    - Temporal match: Birth/death aligns with theme period
    - Geographic match: Nationality matches theme geography
    - Movement match: Artist's movements align with concepts
    - Keyword match: Biography contains theme keywords
    - LLM semantic: Claude scores thematic alignment

Diversity Score (20%):
    - Gender diversity (female = +0.4, male = +0.1)
    - Geographic diversity (non-Western = +0.4)
    - Temporal diversity (underrepresented period = +0.2)

Data Quality Score (20%):
    - Has Getty ULAN: +0.2
    - Has Wikipedia: +0.2
    - Has Yale LUX: +0.3
    - Has IIIF images: +0.3

Combined = (R × 0.6) + (D × 0.2) + (Q × 0.2)
```

### Stage 4: Diversity-Aware Selection (GOOD AS-IS)
```python
Greedy algorithm:
1. Sort by combined score
2. Select top artist
3. IF diversity targets not met:
    - Boost underrepresented groups
    - Select highest scoring from target group
4. Repeat until N artists or targets met
5. Fill remaining with highest scores
```

---

## CONCRETE IMPROVEMENTS

### 🔥 Critical Fixes:

1. **Add Movement Fallback**
   ```python
   # In _build_artist_queries()
   if concept.confidence_score < 0.6:
       # Low confidence - use broader search
       queries.append(self._build_wikidata_broad_search(concept))
   ```

2. **Add Reference Artist Expansion**
   ```python
   # NEW method
   async def _discover_related_artists(self, reference_artists):
       # Get influenced_by, student_of, contemporary_of
       # Much higher relevance than concept search
   ```

3. **Add Time Period Filtering**
   ```python
   # In SPARQL queries
   FILTER(?birth >= 1580 && ?birth <= 1720)  # Dutch Golden Age
   ```

4. **Pre-filter in SPARQL for Diversity**
   ```python
   # Option to get only female artists first
   ?artist wdt:P21 wd:Q6581072 .  # gender = female
   ```

5. **Add Wikipedia Category Mining**
   ```python
   # Extract from: "Category:17th-century Dutch painters"
   # Cross-reference with Wikidata
   ```

### 💡 Nice-to-Haves:

6. **Cache Known Movements**
   ```python
   MOVEMENT_CACHE = {
       "impressionism": "wd:Q40415",
       "baroque": "wd:Q37853",
       "abstract expressionism": "wd:Q11374"
   }
   ```

7. **Add Confidence Thresholds**
   ```python
   # Don't even query if concept confidence < 0.3
   # Prevents bad queries that timeout
   ```

8. **Smart Query Ordering**
   ```python
   # Try narrow query first (fast)
   # If < 5 results, try broader query
   # Progressive broadening
   ```

---

## ANSWER: Is de huidige workflow optimaal?

### ❌ NEE, kan beter:

**Probleem 1: Te afhankelijk van exacte concept matches**
- Fix: Add movement fallback + keyword search

**Probleem 2: Geen gebruik van reference artists**
- Fix: Add related artist expansion

**Probleem 3: Queries kunnen timeout**
- Fix: Add time limits + progressive broadening

**Probleem 4: Diversiteit pas achteraf**
- Fix: Pre-filter in SPARQL waar mogelijk

### ✅ WAT WEL GOED IS:

1. Multi-source enrichment (Wikidata → Getty → Wikipedia → Yale)
2. Diversity scoring systeem
3. Greedy selection voor targets
4. Data model (DiscoveredArtist) is uitgebreid genoeg

---

## RECOMMENDED IMPLEMENTATION ORDER

### Phase 1: Quick Wins (30 min)
```python
1. Add movement fallback queries
2. Add time period filtering
3. Add broader keyword search for low-confidence concepts
```

### Phase 2: Related Artists (1 hour)
```python
4. Implement reference artist expansion
5. Add influenced_by, student_of queries
6. Weight related artists higher in scoring
```

### Phase 3: Multi-Path Discovery (2 hours)
```python
7. Implement parallel search paths
8. Add Wikipedia category mining
9. Merge and deduplicate across sources
10. Weight by source quality
```

### Phase 4: Smart Querying (1 hour)
```python
11. Progressive query broadening
12. Confidence-based query selection
13. Timeout handling and fallbacks
```

---

## CONCLUSION

**Huidige workflow:**
- Conceptueel correct (multi-source, enrichment, diversity)
- Maar te rigide (concept-only search faalt vaak)

**Optimale workflow:**
- **Start breed** (movement, time period, geography)
- **Gebruik reference artists** als beschikbaar (hoogste relevance)
- **Parallel zoeken** (meerdere paths)
- **Filter afterward** (relevance + diversity + quality)
- **Pre-filter in SPARQL** waar mogelijk (performance)

**Volgorde moet zijn:**
1. LLM: Interpreteer curator input → structured search parameters
2. Multi-path search: Movement + Related + Keyword + Categories
3. Merge & enrich: Combine sources, add biographical data
4. Intelligent scoring: Relevance + Diversity + Quality
5. Diversity-aware selection: Ensure targets met

Dit geeft **betere recall** (meer artists gevonden) EN **betere precision** (relevantere artists) EN **betere diversity** (targets eerder gehaald).

Wil je dat ik Phase 1 (Quick Wins) nu implementeer?