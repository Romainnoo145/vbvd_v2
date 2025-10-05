# Backend Tests

This directory contains all test files for validating backend functionality, organized by category.

---

## Directory Structure

```
backend/tests/
├── agents/          # Agent-specific tests (theme refinement, etc.)
├── clients/         # API client tests (Europeana, Wikipedia, etc.)
├── integration/     # Integration and end-to-end tests
├── query/           # Query building and execution tests
├── utils/           # Utility and helper function tests
└── validation/      # Validation and taxonomy tests
```

---

## Test Categories

### 🤖 Agents (`agents/`)
Tests for AI agents and their functionality:
- `test_theme_refinement.py` - Theme refinement agent testing

### 🌐 Clients (`clients/`)
Tests for external API clients:
- `test_client_direct.py` - Direct client API testing
- `test_europeana_capabilities.py` - Comprehensive Europeana API testing ✅
- `test_europeana_fields.py` - Europeana field structure tests
- `test_europeana_topics.py` - Europeana topics knowledge base testing ✅
- `test_wikipedia_api.py` - Wikipedia API integration testing
- `test_wikipedia_debug.py` - Wikipedia debugging utilities

### 🔗 Integration (`integration/`)
End-to-end and integration tests:
- `test_diagnostic.py` - System diagnostic tests
- `test_europeana_api_integration.py` - Full Europeana integration tests
- `test_europeana_simple.py` - Basic Europeana integration tests
- `test_football_exhibition.py` - Football exhibition case study
- `test_theme_refinement_integration.py` - Full theme refinement workflow
- `test_websocket_theme.py` - WebSocket theme streaming testing

### 🔍 Query (`query/`)
Query building and execution tests:
- `test_actual_query.py` - Real query execution tests
- `test_and_operator.py` - Boolean AND operator tests
- `test_country_filter.py` - Country filtering tests
- `test_media_filter.py` - Media type filtering tests
- `test_per_country.py` - Per-country query tests
- `test_query_builder.py` - Query builder functionality
- `test_query_executor.py` - Query execution tests

### 🛠️ Utils (`utils/`)
Utility and helper function tests:
- `test_artist_extraction.py` - Artist name extraction tests
- `test_relevance_scorer.py` - Relevance scoring algorithm tests

### ✅ Validation (`validation/`)
Validation and taxonomy tests:
- `test_europeana_taxonomy_validation.py` - Europeana taxonomy validation
- `test_query_validation.py` - Query validation tests

---

## Running Tests

### Run Specific Test Files
```bash
cd backend

# Client tests
python tests/clients/test_europeana_capabilities.py
python tests/clients/test_europeana_topics.py

# Query tests
python tests/query/test_query_builder.py

# Integration tests
python tests/integration/test_theme_refinement_integration.py

# Agent tests
python tests/agents/test_theme_refinement.py
```

### Run All Tests in a Category
```bash
# Run all query tests
python -m pytest tests/query/

# Run all client tests
python -m pytest tests/clients/

# Run all integration tests
python -m pytest tests/integration/
```

### Run All Tests
```bash
python -m pytest tests/
```

---

## Test Results

### ✅ Passing Tests
- **Europeana API**: Fully functional and viable for Van Bommel van Dam
- **IIIF Availability**: 100% coverage (excellent!)
- **Topics Knowledge Base**: Working as expected
- **Theme Refinement**: AI generation working

### 📊 Key Findings

**Europeana API Patterns Learned:**
1. **Use broad queries**: `"sculpture Netherlands contemporary"` works better than restrictive filters
2. **Minimal qf filters**: Only use `TYPE:IMAGE` and `YEAR:[start TO end]`
3. **Avoid proxy_dc_type**: Too restrictive, causes 0 results
4. **Post-filter in code**: Filter results after API returns them, not before

**Test Coverage:**
- ✅ Europeana Search API
- ✅ Europeana Entity API
- ✅ IIIF availability
- ✅ Theme-based searching
- ✅ Wikipedia integration
- ✅ WebSocket streaming
- ✅ Client direct testing
- ✅ Query validation
- ✅ Taxonomy validation

---

## Adding New Tests

When adding new tests, place them in the appropriate category:

1. **Agent tests** → `agents/`
2. **API client tests** → `clients/`
3. **End-to-end tests** → `integration/`
4. **Query tests** → `query/`
5. **Utility tests** → `utils/`
6. **Validation tests** → `validation/`

All test files should follow the naming convention: `test_*.py`

---

## Manual Testing Tools

### WebSocket Manual Test
```bash
# Start backend server first
cd backend && python -m uvicorn api.main:app --reload

# Then open in browser
open tests/test_ws_manual.html
```

---

## Documentation

Detailed test results and findings are documented in:
- `/docs/testing/EUROPEANA_TEST_RESULTS.md` - Europeana API test results
- Individual test files contain inline documentation

---

## Next Steps

Future testing improvements:
1. Add performance tests for large result sets
2. Add load testing for concurrent requests
3. Add regression tests for bug fixes
4. Increase test coverage to 80%+
