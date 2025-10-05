# Europeana Topics Knowledge Base

## Overview

This knowledge base provides **prior knowledge** about Europeana's topic taxonomy and search categories to improve search relevance when querying the Europeana API for exhibition curation.

Europeana aggregates **58M+ cultural heritage items** from **3,000+ European institutions**, with strong coverage of:
- Modern and contemporary art (1900-present)
- Sculptures and 3D objects
- European regional museums (including Dutch collections)
- Installation art and mixed media

## Why This Matters for Museum van Bommel van Dam

The Museum van Bommel van Dam focuses primarily on:
- **Sculptures** and 3D installations
- **Modern/contemporary art** (post-1945)
- **European regional art** (especially Dutch)

This makes **Europeana the ideal primary data source** (not Yale LUX, which is US-focused and historical).

## How It Works

### Automatic Theme Detection

When a curator inputs an exhibition theme, the system automatically:

1. **Analyzes the theme description** for art movements, media types, and time periods
2. **Maps to Europeana topics** using predefined categories
3. **Enhances API queries** with relevant filters and search terms
4. **Returns more relevant results** tailored to the museum's focus

### Example: Surrealism Exhibition

**Input**: "Dreams & Reality: The Surrealist Revolution"

**Automatic Enhancement**:
```python
# System detects "surrealist" keyword
# Maps to surrealism theme with:
- Art movements: ["Surrealism", "Surrealist"]
- Media types: ["painting", "sculpture", "drawing", "photography", "print"]
- Time periods: ["1920-1945", "1945-1970"]
- Query filters:
  - proxy_dc_type.en: "painting", "sculpture", "drawing"
  - YEAR: [1920 TO 1945]
```

**Result**: API returns surrealist artworks from 1920-1970 in relevant media, from European museums.

## Supported Exhibition Themes

The system has predefined mappings for common themes:

| Theme | Description | Time Period | Media Types |
|-------|-------------|-------------|-------------|
| **Surrealism** | Surrealist movement | 1920-1970 | Painting, sculpture, drawing, photography |
| **Dutch Modernism** | De Stijl, Neo-Plasticism | 1910-1940 | Painting, sculpture, mixed media |
| **Contemporary Sculpture** | Modern 3D art | 1970-2025 | Sculpture, installation, ceramic |
| **Abstract Expressionism** | American/European abstraction | 1945-1970 | Painting, drawing, print |
| **Installation Art** | Spatial and environment art | 1960-2025 | Installation, assemblage, mixed media |
| **Photography Modern** | Photographic art | 1920-2025 | Photography |
| **European Modern Art** | General modernism | 1900-1970 | All media |

## Art Movements Database

The system recognizes **30+ art movements** organized by period:

### Historical (1400-1800)
- Mannerism, Baroque, Rococo, Neoclassicism

### 19th Century
- Romanticism, Impressionism, Post-Impressionism, Symbolism, Art Nouveau

### Early 20th Century (1900-1945)
- Expressionism, Cubism, Futurism, Dadaism, **Surrealism**, De Stijl, Bauhaus

### Mid-Late 20th Century (1945-2000)
- Art Deco, Abstract Expressionism, Pop Art, Minimalism, Conceptual Art

### Contemporary (1970-present)
- Contemporary Art, Installation Art, Performance Art

## Media Types

Supports filtering by **11 media types**:

| Media Type | Europeana Terms |
|------------|-----------------|
| **Painting** | painting, oil painting, watercolor, acrylic |
| **Sculpture** | sculpture, statue, carved, sculpted |
| **Drawing** | drawing, sketch |
| **Print** | print, etching, lithograph, woodcut |
| **Photography** | photography, photograph, photo |
| **Installation** | installation art, assemblage |
| **Mixed Media** | mixed media, multimedia, collage |
| **Textile** | tapestry, fabric art, fiber art |
| **Ceramic** | ceramic, pottery, porcelain |
| **Video Art** | video art, video installation |
| **Performance** | performance art, happening |

## API Integration

### Automatic Usage

The enhanced Europeana search is **automatically used** when:
- Searching for artists based on exhibition theme
- Discovering artworks for specific themes
- Filtering by time period or media type

### Example API Call Enhancement

**Original query**:
```python
query = "Salvador Dalí"
context = "Surrealist artist for Dreams & Reality exhibition"
```

**Enhanced query sent to Europeana**:
```python
{
  "query": '(who:"Salvador Dalí" AND TYPE:IMAGE) OR ("Surrealism" OR "Surrealist")',
  "rows": 30,
  "profile": "rich",
  "qf": [
    'proxy_dc_type.en:"painting"',
    'proxy_dc_type.en:"sculpture"',
    'YEAR:[1920 TO 1945]'
  ]
}
```

**Benefits**:
- ✅ Finds Dalí's work
- ✅ Also surfaces related surrealist works
- ✅ Filters to relevant media and time period
- ✅ Returns European museum collections

## Technical Details

### Query Facet (qf) Parameters

The system uses Europeana's `qf` parameter for precise filtering:

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `proxy_dc_type.en` | Media type filtering | `"sculpture"` |
| `proxy_dc_format.en` | Format filtering | `"photograph"` |
| `YEAR` | Date range filtering | `[1920 TO 1945]` |
| `COUNTRY` | Geographic filtering | `"Netherlands"` |
| `DATA_PROVIDER` | Institution filtering | `"Stedelijk Museum"` |

### IIIF Support

Europeana provides **IIIF manifests** for high-quality image access:
```python
# Automatically constructed from Europeana ID
iiif_manifest = f"https://iiif.europeana.eu/presentation/{record_id}/manifest"
```

## Adding New Themes

To add support for a new exhibition theme:

1. **Edit** `/backend/config/europeana_topics.py`
2. **Add mapping** to `EXHIBITION_THEME_MAPPINGS`:

```python
'new_theme': EuropeanaTopicMapping(
    topic_id=190,  # or 97 for contemporary
    search_terms=['keyword1', 'keyword2'],
    art_movements=['Movement Name'],
    media_types=['media1', 'media2'],
    time_periods=['start_year-end_year'],
    qf_filters={
        'proxy_dc_type': ['type1', 'type2'],
        'YEAR': ['start', 'end'],
    }
),
```

3. **Restart backend** - changes are loaded automatically

## Usage in Code

### Find Theme Mapping
```python
from backend.config.europeana_topics import find_best_theme_match

mapping = find_best_theme_match("Exhibition about Dutch abstract art")
# Returns: dutch_modernism mapping
```

### Get Specific Theme
```python
from backend.config.europeana_topics import get_europeana_search_params

mapping = get_europeana_search_params('surrealism')
# Returns: surrealism mapping with all parameters
```

### Build Enhanced Query
```python
from backend.config.europeana_topics import build_europeana_query

params = build_europeana_query(
    base_query="Joan Miró",
    theme="surrealism",
    media_type="painting",
    time_period="1920-1945"
)
# Returns: Enhanced query parameters for API
```

## Coverage Statistics

**Europeana Collections**:
- 58M+ items from 3,000+ European institutions
- Strong coverage: Netherlands, Germany, France, UK, Italy, Spain
- Art types: Painting (12M+), Sculpture (3M+), Photography (8M+)
- Time periods: Medieval to Contemporary
- **Best for**: European modern/contemporary art (1900-present)

## Comparison with Other APIs

| Feature | Europeana | Yale LUX | Wikipedia |
|---------|-----------|----------|-----------|
| **Geographic Focus** | Europe ✅ | USA | Global |
| **Time Period** | All periods ✅ | Strong in historical | All |
| **Modern Art** | Excellent ✅ | Limited | Good |
| **3D Objects** | Excellent ✅ | Good | Limited |
| **Dutch Museums** | Excellent ✅ | None | Limited |
| **IIIF Support** | Yes ✅ | Yes ✅ | No |
| **API Quality** | Rich metadata ✅ | Rich metadata ✅ | Basic |

**Recommendation**: Use Europeana as **primary source** for Van Bommel van Dam, with Yale LUX as **secondary** for international loans.

## References

- [Europeana API Documentation](https://pro.europeana.eu/page/apis)
- [Search API Docs](https://europeana.atlassian.net/wiki/spaces/EF/pages/2385739812/Search+API+Documentation)
- [Europeana Collections](https://www.europeana.eu/en/collections)
- [IIIF Specifications](https://iiif.io/)

## Support

For questions about extending the topic taxonomy or adding new themes, consult:
- `/backend/config/europeana_topics.py` - Main configuration
- `/backend/clients/essential_data_client.py` - API integration (line 578+)
