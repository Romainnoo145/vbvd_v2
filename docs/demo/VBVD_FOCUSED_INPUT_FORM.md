# Van Bommel van Dam Focused Input Form

**Date**: 2025-10-04
**Purpose**: Tailor input form specifically for Van Bommel van Dam's contemporary art focus

---

## Summary of Changes

The input form has been **refined from generic Europeana categories to Van Bommel van Dam-specific categories**, reflecting the museum's actual curatorial needs for contemporary and modern art.

---

## Key Refinements

### 1. ✅ Time Periods (Narrowed from 9 → 5)

**Removed Historical Periods**:
- ❌ Renaissance (1400-1600)
- ❌ Baroque (1600-1750)
- ❌ Enlightenment (1685-1815)
- ❌ 19th Century (1800-1900)

**Kept Contemporary/Modern Only**:
- ✅ Early Modernism (1920-1945)
- ✅ Post-War (1945-1970)
- ✅ Contemporary (1970-2000)
- ✅ 21st Century Contemporary (2000-2025)
- ✅ All Contemporary (1945-2025)

**Rationale**: Van Bommel van Dam is a contemporary art museum. Curators would never search for Renaissance or Baroque artworks.

---

### 2. ✅ Art Movements (Contemporary Focus)

**Removed Historical Movements**:
- ❌ Romanticism
- ❌ Art Nouveau
- ❌ Impressionism

**Added Contemporary Movements**:
- ✅ Neo-Expressionism
- ✅ Fluxus
- ✅ Arte Povera
- ✅ Land Art / Earth Art
- ✅ Installation Art Movement

**Kept Relevant Modern Movements**:
- ✅ De Stijl (Dutch!)
- ✅ Surrealism
- ✅ Abstract Expressionism
- ✅ Minimalism
- ✅ Conceptual Art
- ✅ Pop Art
- ✅ Contemporary Art

**Selection Limit**: Max 3 movements (down from 5) for more focused searches.

**Rationale**: Focus on movements from 1900s onwards that align with Van Bommel van Dam's collection.

---

### 3. ✅ Media Types (Core + Additional)

**CORE Media Types (Always Selected)**:
- ✅ Installation Art
- ✅ Sculpture
- ✅ Photography
- ✅ Mixed Media

**Additional Media Types (Optional)**:
- Painting
- Video Art
- Performance Art
- Drawing
- Print / Graphics
- Textile Art
- New Media / Digital Art

**UI Design**:
- Core types shown in highlighted box (gold accent background)
- Core types have checkboxes disabled (always checked)
- Additional types shown separately below
- Counter shows: "4 core types + X additional = Y total"

**Rationale**: Per user feedback - "always installation art and photography and sculpture" for Van Bommel van Dam exhibitions.

---

### 4. ✅ Geographic Focus (Priority Regions)

**Priority Regions** (Netherlands & Neighbors):
- 🇳🇱 Netherlands (default selected)
- 🇧🇪 Belgium
- 🇩🇪 Germany

**Other European Regions**:
- 🇫🇷 France
- 🇬🇧 United Kingdom
- 🇪🇸 Spain
- 🇮🇹 Italy
- 🇸🇪 Sweden
- 🇩🇰 Denmark
- 🇵🇱 Poland

**UI Design**:
- Priority regions shown in separate highlighted section
- Netherlands pre-selected by default
- Other regions shown below as optional

**Rationale**: Van Bommel van Dam focuses on Dutch and regional European art. Netherlands should be default.

---

### 5. ✅ Updated Banner

**Old Banner**:
> "This structured form searches available artworks first..."

**New Banner**:
> "This form is optimized for Van Bommel van Dam's focus: contemporary and modern art (1920-2025), with core media types (installation, sculpture, photography, mixed media) always included. Searches available artworks first, discovering both established and emerging artists."

**Rationale**: Explicitly states Van Bommel van Dam's focus and explains the tailored defaults.

---

## Default Values

```typescript
{
  theme_title: "",
  theme_description: "",
  time_period: "",
  art_movements: [],

  // Core media types ALWAYS included
  media_types: ["installation", "sculpture", "photography", "mixed_media"],

  // Netherlands default
  geographic_focus: ["Netherlands"],

  thematic_keywords: "",
  target_audience: "",
  duration_weeks: 12
}
```

---

## Demo Data (Updated)

```typescript
{
  theme_title: "Surrealism and the Unconscious Mind",
  theme_description: "Exploring surrealist artists...",

  time_period: "early_modern_1920",  // 1920-1945 (not generic "early_modern")
  art_movements: ["surrealism"],     // Just 1 movement (focused)

  // Core 4 + painting for surrealism
  media_types: ["installation", "sculpture", "photography", "mixed_media", "painting"],

  // Netherlands + surrealism regions
  geographic_focus: ["Netherlands", "France", "Spain", "Belgium"],

  thematic_keywords: "dreams, automatism, psychoanalysis, biomorphism, unconscious mind",
  target_audience: "general",
  duration_weeks: 12
}
```

---

## Validation Rules

| Field | Old Rule | New Rule | Reason |
|-------|----------|----------|--------|
| **time_period** | Required | Required | No change |
| **art_movements** | 1-5 movements | 1-3 movements | More focused search |
| **media_types** | 1-5 types | Min 4 (core types) | Core types always included |
| **geographic_focus** | Optional | Optional (default: Netherlands) | Regional focus |

---

## Visual Changes

### Time Period Dropdown
```
Before: 9 options (Renaissance → 21st Century)
After:  5 options (Early Modernism 1920 → 21st Century 2025)
```

### Art Movements Grid
```
Before: 15 movements (all eras)
After:  12 movements (modern/contemporary only)
Limit:  Max 3 selections (was 5)
```

### Media Types Section
```
CORE FOCUS (always included):
┌─────────────────────────────────┐
│ ☑ Installation Art              │
│ ☑ Sculpture                     │
│ ☑ Photography                   │
│ ☑ Mixed Media                   │
└─────────────────────────────────┘

Additional media types (optional):
┌─────────────────────────────────┐
│ ☐ Painting                      │
│ ☐ Video Art                     │
│ ☐ Performance Art               │
│ ☐ Drawing                       │
│ ☐ Print / Graphics              │
│ ☐ Textile Art                   │
│ ☐ New Media / Digital Art       │
└─────────────────────────────────┘
```

### Geographic Focus Section
```
PRIORITY REGIONS (Netherlands & neighbors):
┌─────────────────────────────────┐
│ ☑ 🇳🇱 Netherlands               │
│ ☐ 🇧🇪 Belgium                   │
│ ☐ 🇩🇪 Germany                   │
└─────────────────────────────────┘

Other European regions (optional):
┌─────────────────────────────────┐
│ ☐ 🇫🇷 France                    │
│ ☐ 🇬🇧 United Kingdom            │
│ ☐ 🇪🇸 Spain                     │
│ ...                             │
└─────────────────────────────────┘
```

---

## User Experience Improvements

### For a Van Bommel van Dam Curator:

1. **No irrelevant options**: No Renaissance, Baroque, Rococo
2. **Sensible defaults**: Installation, sculpture, photography, mixed media always included
3. **Regional focus**: Netherlands pre-selected
4. **Contemporary movements**: Neo-Expressionism, Fluxus, Land Art added
5. **Focused search**: Max 3 movements prevents over-filtering
6. **Clear labeling**: "Early Modernism (1920-1945)" instead of generic "Early Modern"

---

## Comparison: Generic vs Van Bommel van Dam

| Aspect | Generic Europeana Form | Van Bommel van Dam Form |
|--------|------------------------|-------------------------|
| **Time Periods** | Renaissance → 21st Century (9 options) | Early Modernism 1920 → Contemporary (5 options) |
| **Art Movements** | All eras (15 movements) | Modern/Contemporary (12 movements) |
| **Movement Limit** | Max 5 | Max 3 (focused) |
| **Media Types** | All optional (11 types) | 4 core always + 7 optional |
| **Geographic Default** | None | Netherlands |
| **Core Media** | None | Installation, Sculpture, Photography, Mixed Media |
| **Banner Message** | Generic Europeana | Van Bommel van Dam specific |

---

## API Impact

When a curator submits this form, the backend will receive:

```json
{
  "theme_title": "Surrealism and the Unconscious Mind",
  "theme_description": "...",
  "time_period": "early_modern_1920",
  "art_movements": ["surrealism"],
  "media_types": ["installation", "sculpture", "photography", "mixed_media", "painting"],
  "geographic_focus": ["Netherlands", "France", "Spain", "Belgium"],
  "thematic_keywords": "dreams, automatism, psychoanalysis"
}
```

**Backend Query Construction**:
1. Time period → `YEAR:[1920 TO 1945]` (not `YEAR:[1900 TO 1945]`)
2. Media types → Broad query including all 5 types
3. Geographic focus → Post-filter by dataProvider country
4. Movements → OR query: "Surrealism"

---

## Testing the Van Bommel van Dam Form

1. **Navigate to**: `http://localhost:3005/`

2. **Observe defaults**:
   - Media Types: 4 core types already checked (disabled)
   - Geographic Focus: Netherlands already selected
   - Time Periods: Only contemporary options (1920-2025)

3. **Click "Load Demo"**:
   - See surrealism example with appropriate settings
   - Notice only 1 movement selected (focused search)
   - See 5 total media types (4 core + painting)

4. **Try to uncheck core media**:
   - Installation, Sculpture, Photography, Mixed Media are disabled
   - Cannot be unchecked

5. **Try selecting 4 movements**:
   - After selecting 3, remaining options become disabled
   - Forces focused search

---

## Next Steps

After user approval:

1. **Backend Integration**: Update API to handle Van Bommel van Dam focused categories
2. **Europeana Query Mapping**: Map "early_modern_1920" → `YEAR:[1920 TO 1945]`
3. **Core Media Enforcement**: Ensure backend always includes 4 core types
4. **Geographic Post-Filtering**: Filter results by selected regions

---

## Conclusion

This form is now **tailored specifically for Van Bommel van Dam curators**, not generic art historians. It:

✅ **Removes irrelevant historical periods** (Renaissance, Baroque, etc.)
✅ **Defaults to contemporary media types** (installation, sculpture, photography, mixed media)
✅ **Prioritizes regional focus** (Netherlands default)
✅ **Enforces focused searches** (max 3 movements instead of 5)
✅ **Uses museum-appropriate language** (Early Modernism 1920, not just Early Modern)

The form now reflects **how a Van Bommel van Dam curator actually works**: contemporary art focus, installation/sculpture primary, Dutch/regional emphasis.
