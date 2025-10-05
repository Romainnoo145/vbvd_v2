# Backend Tests

This directory contains test files for validating backend functionality.

---

## Test Files

### Europeana API Tests

**`test_europeana_capabilities.py`** - Comprehensive Europeana API testing
- Tests facet retrieval
- Tests Entity API for artist discovery
- Tests multi-criteria search patterns
- Tests response structure
- Tests IIIF availability
- Tests theme-based queries
- **Status**: ✅ All tests passed
- **Results**: See `/docs/testing/EUROPEANA_TEST_RESULTS.md`

**`test_europeana_topics.py`** - Europeana topics knowledge base testing
- Tests theme mapping retrieval
- Tests search parameter generation
- Tests query building
- **Status**: ✅ All tests passed

---

### Client Tests

**`test_client_direct.py`** - Direct client API testing
- Tests essential data client
- Validates API responses

---

### Theme Refinement Tests

**`test_theme_refinement.py`** - Theme refinement agent testing
- Tests theme generation
- Validates AI-generated exhibition narratives

**`test_websocket_theme.py`** - WebSocket theme streaming testing
- Tests real-time theme refinement
- Validates streaming responses

**`test_ws_manual.html`** - Manual WebSocket testing
- Browser-based WebSocket test interface
- Interactive testing tool

---

### Wikipedia API Tests

**`test_wikipedia_api.py`** - Wikipedia API integration testing
- Tests artist data retrieval from Wikipedia

**`test_wikipedia_debug.py`** - Wikipedia debugging utilities
- Debug tool for Wikipedia API issues

---

## Running Tests

### Run All Europeana Tests
```bash
cd backend
python test_europeana_capabilities.py
```

### Run Topic Tests
```bash
python test_europeana_topics.py
```

### Run Client Tests
```bash
python test_client_direct.py
```

### Run Theme Tests
```bash
python test_theme_refinement.py
```

### Manual WebSocket Test
```bash
# Start backend server first
cd backend && python -m uvicorn api.main:app --reload

# Then open in browser
open tests/test_ws_manual.html
```

---

## Test Results

All test results are documented in `/docs/testing/EUROPEANA_TEST_RESULTS.md`.

Key findings:
- ✅ Europeana API is viable for Van Bommel van Dam
- ✅ IIIF availability: 100% (excellent!)
- ⚠️ Need broad queries with minimal filters (avoid over-filtering)
- ✅ Complete metadata available from Europeana

---

## Important Notes

### Europeana API Patterns Learned

From testing, we learned:
1. **Use broad queries**: `"sculpture Netherlands contemporary"` works better than restrictive filters
2. **Minimal qf filters**: Only use `TYPE:IMAGE` and `YEAR:[start TO end]`
3. **Avoid proxy_dc_type**: Too restrictive, causes 0 results
4. **Post-filter in code**: Filter results after API returns them, not before

### Test Coverage

- ✅ Europeana Search API
- ✅ Europeana Entity API
- ✅ IIIF availability
- ✅ Theme-based searching
- ✅ Wikipedia integration
- ✅ WebSocket streaming
- ✅ Client direct testing

---

## Next Steps

After implementation:
1. Add unit tests for new features
2. Add integration tests for complete workflow
3. Add E2E tests for frontend → backend → Europeana
4. Add performance tests for large result sets
