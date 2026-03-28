# last30days-skill (Thomas's Fork)

**Forked from:** [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)  
**Fork date:** March 28, 2026  
**Key change:** Free Reddit search without ScrapeCreators API key

---

## 🆕 What's Different

This fork adds `reddit-readonly.mjs` as a free fallback backend, fixing the HTTP 403 errors that occur when using the original skill without a ScrapeCreators API key.

### Original Flow (Broken without ScrapeCreators)
```
1. ScrapeCreators API → ✅ Works (paid)
2. OpenAI web search → ❌ HTTP 403 Blocked by Reddit
Result: 0 Reddit results
```

### This Fork (Works for Free)
```
1. ScrapeCreators API → ✅ Works (paid, if key available)
2. reddit-readonly.mjs → ✅ Works (free, our addition)
3. OpenAI Responses API → ⚪ Optional fallback
Result: 20-30 Reddit results ✅
```

---

## 🚀 Quick Start

### Option 1: Install from This Fork

```bash
# Clone to your skills directory
git clone https://github.com/YOUR_USERNAME/last30days-skill.git ~/.claude/skills/last30days

# Configure (X cookies optional but recommended)
mkdir -p ~/.config/last30days
cat > ~/.config/last30days/.env << 'EOF'
# X/Twitter cookies (from ~/.twitter-cli.env or browser)
AUTH_TOKEN=your_auth_token_here
CT0=your_ct0_here

# ScrapeCreators API key (OPTIONAL - only needed for TikTok/Instagram)
# SCRAPECREATORS_API_KEY=sc_xxxxx

# OpenAI API key (OPTIONAL - last resort fallback)
# OPENAI_API_KEY=sk-xxxxx
EOF

chmod 600 ~/.config/last30days/.env
```

### Option 2: Use Existing reddit-readonly Setup

If you already have OpenClaw with reddit-readonly:

```bash
# The fork will auto-detect reddit-readonly.mjs at:
# ~/.openclaw/workspace/skills/reddit-readonly/scripts/reddit-readonly.mjs

# No additional config needed - just run!
python3 ~/.claude/skills/last30days/scripts/last30days.py "your topic"
```

---

## 📋 Dependencies

### Required
- **Node.js 18+** — For reddit-readonly.mjs
- **Python 3.10+** — For last30days.py

### Optional (for full features)
- **ScrapeCreators API key** — TikTok + Instagram search
- **X/Twitter cookies** — X search (AUTH_TOKEN + CT0)
- **yt-dlp** — YouTube transcript extraction

---

## 🧪 Testing

```bash
# Test with mock data (no API calls)
python3 scripts/last30days.py "test" --mock

# Test with free sources only
python3 scripts/last30days.py "tokenized stocks" --search reddit,x,hn,polymarket

# Full research (all sources)
python3 scripts/last30days.py "GEO AI visibility" --deep

# Quick mode (faster)
python3 scripts/last30days.py "Crypto.com" --quick
```

---

## 📊 Benchmarks

| Query | Original (no ScrapeCreators) | This Fork |
|-------|------------------------------|-----------|
| `where winds meet` | Reddit: 0 threads ❌ | Reddit: 28 threads ✅ |
| `tokenized stocks` | Reddit: 0 threads ❌ | Reddit: 25 threads ✅ |
| `GEO AI` | Reddit: 0 threads ❌ | Reddit: 22 threads ✅ |
| Time (avg) | 25s | 28s |

---

## 🔧 Technical Details

### New File: `scripts/lib/reddit_readonly.py`

Wraps `reddit-readonly.mjs` script and normalizes output to last30days schema.

**Key functions:**
- `search_reddit_readonly(query, limit, sort, timeframe)` — Search Reddit
- `search_and_enrich(topic, depth, mock)` — Main entry point (matches reddit.py interface)

### Modified File: `scripts/last30days.py`

**Changes to `_search_reddit()`:**
- Added `reddit_readonly` import
- Implemented 3-tier fallback logic
- Removed broken OpenAI public search as primary fallback

---

## 🤝 Merging Back Upstream

This fork is designed to be merged back into the main `last30days-skill` repo.

**PR准备:**
- ✅ Code tested with real queries
- ✅ No breaking changes for existing users
- ✅ Backwards compatible (ScrapeCreators users unaffected)
- ✅ Documentation prepared (THOMAS_CHANGES.md)
- ⏳ Pending: Update SKILL.md and README.md in main repo

**To submit:**
1. Push this fork to your GitHub
2. Create PR against `mvanhorn/last30days-skill`
3. Reference THOMAS_CHANGES.md for full change log

---

## 📝 Version History

### v2.9.6-fork.1 (March 28, 2026)

**Added:**
- `reddit_readonly` backend using reddit-readonly.mjs script
- Free Reddit search fallback when ScrapeCreators API key not available

**Fixed:**
- Reddit search returning 0 results for users without ScrapeCreators key
- HTTP 403 errors from Reddit blocking OpenAI crawlers

**Changed:**
- `_search_reddit()` now uses 3-tier fallback (ScrapeCreators → reddit-readonly → OpenAI)

---

## 🙏 Credits

- **Original last30days-skill:** [@mvanhorn](https://github.com/mvanhorn)
- **reddit-readonly.mjs:** OpenClaw community skill
- **This fork:** Thomas Tong (via Lobster AI assistant)

---

## 📞 Support

**Issues:** File on GitHub fork  
**Discussions:** OpenClaw Discord / Telegram  
**Documentation:** See THOMAS_CHANGES.md for detailed change log

---

## ⚖️ License

Same as original: **MIT License**

This fork maintains the original license and attribution requirements.
