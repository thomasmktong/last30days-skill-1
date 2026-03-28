# PR: Add reddit-readonly.mjs as Free Reddit Backend

**Author:** Thomas Tong (via Lobster AI assistant)  
**Date:** March 28, 2026  
**Issue:** Reddit search broken without ScrapeCreators API key (HTTP 403)

---

## 🎯 Problem

The original `last30days` skill has this Reddit search flow:

1. **ScrapeCreators API** (paid) — Works ✅
2. **OpenAI Responses API** (fallback) — **Blocked by Reddit with HTTP 403** ❌

This means users without a ScrapeCreators API key get **zero Reddit results**.

---

## ✅ Solution

Add `reddit-readonly.mjs` as the free fallback backend:

1. **ScrapeCreators API** (paid) — Works ✅
2. **reddit-readonly.mjs** (free) — Works ✅ (our addition)
3. **OpenAI Responses API** (last resort) — Only if user has key

---

## 📁 Files Changed

### 1. `scripts/lib/reddit_readonly.py` (NEW)

New backend module that wraps the existing `reddit-readonly.mjs` script.

**Key features:**
- Calls `reddit-readonly.mjs` via subprocess
- Normalizes output to match last30days schema
- Free, no API key required
- Uses Reddit's public JSON API (not blocked)

**Location:** `scripts/lib/reddit_readonly.py`

---

### 2. `scripts/last30days.py` (MODIFIED)

**Changes:**
- Added `reddit_readonly` import
- Rewrote `_search_reddit()` function with 3-tier fallback
- Removed broken OpenAI public search as primary fallback

**Before:**
```python
if not config.get("OPENAI_API_KEY"):
    # OpenAI public search → HTTP 403 blocked
    reddit_items = openai_reddit.search_reddit_public(...)
```

**After:**
```python
# Path 2: reddit-readonly.mjs (free fallback)
result = reddit_readonly.search_and_enrich(topic, depth=depth, mock=mock)
reddit_items = result.get("items", [])
```

---

### 3. `scripts/lib/__init__.py` (NO CHANGE NEEDED)

The module is auto-discovered via import in `last30days.py`.

---

## 🧪 Testing

**Test query:** `where winds meet`

| Metric | Before | After |
|--------|--------|-------|
| Reddit results | 0 (403 error) | 28-30 threads ✅ |
| Total time | 27s | 28.8s |
| Cost | $0 (but broken) | $0 (working) |

**Command:**
```bash
python3 last30days.py "where winds meet" --search reddit,x,hn --emit=md
```

---

## 🔍 Why This Works

| Approach | Why It Works/Fails |
|----------|-------------------|
| **ScrapeCreators** | ✅ They handle scraping infrastructure |
| **OpenAI web search** | ❌ Reddit blocks OpenAI crawlers (403) |
| **reddit-readonly.mjs** | ✅ Uses old Reddit JSON API (not blocked yet) |

The `reddit-readonly.mjs` script hits:
```
https://www.reddit.com/r/all/search.json?q=topic
```

This is Reddit's **public JSON API** — same as browsing old.reddit.com in a browser. Reddit doesn't block these (yet) because they're used by legitimate apps.

---

## 📋 Dependencies

**Required:**
- Node.js 18+ (for reddit-readonly.mjs)
- Existing `reddit-readonly.mjs` script at: `~/.openclaw/workspace/skills/reddit-readonly/scripts/reddit-readonly.mjs`

**Optional:**
- ScrapeCreators API key (for full features including TikTok/Instagram)

---

## 🚀 Usage (No Changes for End Users)

**Before (broken without ScrapeCreators):**
```bash
python3 last30days.py "topic"  # Reddit: 0 results
```

**After (working for free):**
```bash
python3 last30days.py "topic"  # Reddit: 20-30 results ✅
```

**No breaking changes** — existing users with ScrapeCreators key see no difference.

---

## 📝 Changelog Entry

```markdown
### v2.9.6 (Unreleased)

**Added:**
- New `reddit_readonly` backend using reddit-readonly.mjs script
- Free Reddit search fallback when ScrapeCreators API key not available
- Fixes HTTP 403 errors from OpenAI web search

**Changed:**
- `_search_reddit()` now uses 3-tier fallback:
  1. ScrapeCreators (paid, full features)
  2. reddit-readonly.mjs (free, Reddit + comments)
  3. OpenAI Responses API (only if user has key)

**Fixed:**
- Reddit search returning 0 results for users without ScrapeCreators key
- HTTP 403 errors from Reddit blocking OpenAI crawlers
```

---

## 🤝 Attribution

This PR builds on:
- Original `last30days-skill` by [@mvanhorn](https://github.com/mvanhorn)
- `reddit-readonly.mjs` script (existing OpenClaw skill)

---

## 📸 Screenshots

**Before:**
```
✓ [Reddit] Found 0 threads
[REDDIT WARNING] No output text found in OpenAI response
```

**After:**
```
✓ [Reddit] Found 30 threads
✓ [Reddit] Enriched with engagement data
```

---

## ✅ Checklist

- [x] Code changes tested with real queries
- [x] No breaking changes for existing users
- [x] Backwards compatible (ScrapeCreators users unaffected)
- [x] Dependencies documented
- [x] Changelog entry prepared
- [ ] Add to SKILL.md requirements section
- [ ] Update README.md with new fallback flow

---

## 🔗 Related Issues

- Original issue: Reddit search returns 0 results without ScrapeCreators key
- Root cause: Reddit blocking OpenAI web search crawlers (HTTP 403)
- This PR provides a free, working alternative
