# Progressive Streaming Test - Manual Instructions

Since background processes are tricky in this environment, here's how to test manually:

## ⚠️ Prerequisites

1. FastAPI and websockets are now installed ✅
2. You need **2 terminal windows**

---

## 🚀 Testing Steps

### Terminal 1: Start API Server

```bash
cd /home/klarifai/.clientprojects/vbvd_agent_v2/backend/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Verify it's working:**
```bash
# In another terminal, run:
curl http://localhost:8000/health

# Expected: {"status":"healthy","timestamp":"2025-10-01T..."}
```

---

### Terminal 2: Run WebSocket Test

```bash
cd /home/klarifai/.clientprojects/vbvd_agent_v2
python3 tests/test_websocket_streaming.py
```

---

## 📊 What You Should See

The test will run for **5-8 minutes** and you'll see progressive results:

### Stage 1: Theme Refinement (1-2 minutes)
```
════════════════════════════════════════════════════════════════════════════════
✨ STAGE COMPLETE: THEME_REFINEMENT (25%)
════════════════════════════════════════════════════════════════════════════════

📋 EXHIBITION THEME:
   Title: Dreams Unchained: Surrealism Awakened
   Subtitle: Delving into the Minds of Dalí, Magritte, and Ernst
   Audience: general
   Complexity: intermediate

📄 Curatorial Statement (320 chars):
   At Museum Van Bommel Van Dam, we believe that the power of modern art...

🎓 Scholarly Rationale (262 chars):
   The proposed exhibition, "Surrealism and the Unconscious Mind," seeks...
```

### Stage 2: Artist Discovery (3-4 minutes)
```
════════════════════════════════════════════════════════════════════════════════
✨ STAGE COMPLETE: ARTIST_DISCOVERY (55%)
════════════════════════════════════════════════════════════════════════════════

👨‍🎨 DISCOVERED ARTISTS (5):

   1. Salvador Dalí
      Score: 0.95
      Life: 1904 - 1989
      Wikidata: Q5682
      Reasoning: Dalí pioneered surrealist automatism...

   2. René Magritte
      Score: 0.92
      ...
```

### Stage 3: Artwork Discovery (5-8 minutes)
```
════════════════════════════════════════════════════════════════════════════════
✨ STAGE COMPLETE: ARTWORK_DISCOVERY (90%)
════════════════════════════════════════════════════════════════════════════════

🎨 DISCOVERED ARTWORKS (15):
   IIIF Manifests: 12/15 (80%)

   1. The Persistence of Memory
      Artist: Salvador Dalí
      Date: 1931
      Medium: Oil on canvas
      Institution: MoMA
      Score: 0.92
      IIIF: ✅
      Size: 24cm × 33cm
```

### Final Summary
```
════════════════════════════════════════════════════════════════════════════════
FINAL SUMMARY
════════════════════════════════════════════════════════════════════════════════
✅ Theme: Dreams Unchained: Surrealism Awakened
✅ Artists: 5 discovered
✅ Artworks: 15 discovered (12 with IIIF)
```

---

## ✅ Success Criteria

If you see all 3 stages complete with data, the progressive streaming is working!

**Key indicators:**
- ✅ Each stage sends `stage_complete` message with data
- ✅ Frontend receives theme, then artists, then artworks
- ✅ IIIF manifests available for 70%+ artworks
- ✅ All relevance scores are reasonable (0.5-1.0)

---

## 🐛 Troubleshooting

### "Connection refused"
- Make sure Terminal 1 (API server) is running
- Check: `curl http://localhost:8000/health`

### "Timeout waiting for message"
- The pipeline takes 5-8 minutes with LLM calls
- This is normal! Watch for progress updates

### Wikipedia/Brave errors in logs
- These are non-blocking warnings
- Pipeline continues with fallbacks
- Already fixed to not crash

---

## 🎯 What This Proves

This test validates:
1. ✅ Progressive WebSocket streaming works
2. ✅ Frontend receives data at 3 checkpoints
3. ✅ LLM generates theme-appropriate content
4. ✅ Real museum APIs return quality data
5. ✅ IIIF manifests available for viewing
6. ✅ Full pipeline completes successfully

After this test passes, your backend is **production-ready** for frontend integration! 🎉
