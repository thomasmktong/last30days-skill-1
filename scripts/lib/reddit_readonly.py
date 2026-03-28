"""Reddit search via reddit-readonly.mjs for /last30days.

Uses the existing reddit-readonly.mjs script that hits Reddit's public JSON API.
This is a free, reliable alternative to ScrapeCreators when API key is not available.

Requires:
- Node.js 18+
- reddit-readonly.mjs at: ~/.openclaw/workspace/skills/reddit-readonly/scripts/reddit-readonly.mjs
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Path to reddit-readonly.mjs script
REDDIT_READONLY_PATH = Path.home() / ".openclaw" / "workspace" / "skills" / "reddit-readonly" / "scripts" / "reddit-readonly.mjs"


def _log(msg: str):
    """Log to stderr."""
    sys.stderr.write(f"[Reddit-Readonly] {msg}\n")
    sys.stderr.flush()


def _parse_date(created_utc) -> Optional[str]:
    """Convert Unix timestamp to YYYY-MM-DD."""
    if not created_utc:
        return None
    try:
        dt = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return None


def _normalize_post(post: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Normalize a reddit-readonly post to last30days internal format.
    
    Args:
        post: Post dict from reddit-readonly.mjs
        idx: Index for ID generation
        
    Returns:
        Normalized post dict matching last30days schema
    """
    permalink = post.get("permalink", "")
    url = post.get("url", "")
    
    # Ensure URL is a proper Reddit thread URL (avoid double URLs)
    if not url:
        url = f"https://www.reddit.com{permalink}" if permalink else ""
    elif url.startswith("https://www.reddit.comhttps://"):
        # Fix malformed URLs from reddit-readonly
        url = url.replace("https://www.reddit.comhttps://", "https://www.reddit.com/")
    
    # Extract date
    date_str = _parse_date(post.get("created_utc"))
    created_iso = post.get("created_iso")
    
    # Build normalized result
    return {
        "id": f"RR{idx}",
        "type": "reddit",
        "source": "reddit_readonly",
        "title": post.get("title", ""),
        "text": post.get("selftext_snippet") or "",
        "url": url,
        "permalink": permalink,
        "author": post.get("author", ""),
        "subreddit": post.get("subreddit", ""),
        "date": date_str,
        "created_iso": created_iso,
        "score": post.get("score", 0),
        "ups": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "engagement": post.get("score", 0) + (post.get("num_comments", 0) * 2),
        "is_self": post.get("is_self", False),
        "flair": post.get("flair", ""),
        "over_18": post.get("over_18", False),
    }


def search_reddit_readonly(
    query: str,
    limit: int = 30,
    sort: str = "relevance",
    timeframe: str = "all",
) -> List[Dict[str, Any]]:
    """Search Reddit using reddit-readonly.mjs script.
    
    Args:
        query: Search query string
        limit: Max results to return (default: 30)
        sort: Sort order (relevance, hot, new, top)
        timeframe: Time filter (hour, day, week, month, year, all)
        
    Returns:
        List of normalized post dicts
    """
    if not REDDIT_READONLY_PATH.exists():
        _log(f"Script not found at {REDDIT_READONLY_PATH}")
        return []
    
    # Build command
    cmd = [
        "node",
        str(REDDIT_READONLY_PATH),
        "search", "all",  # Search scope: all subreddits
        query,
        "--limit", str(limit),
        "--sort", sort,
        "--time", timeframe,
    ]
    
    try:
        _log(f"Searching Reddit for: {query}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            _log(f"Script failed: {result.stderr[:200]}")
            return []
        
        # Parse JSON output
        output = json.loads(result.stdout)
        
        if not output.get("ok"):
            error = output.get("error", {})
            _log(f"API error: {error.get('message', 'Unknown error')}")
            return []
        
        posts = output.get("data", {}).get("posts", [])
        _log(f"Found {len(posts)} posts")
        
        # Normalize each post
        normalized = []
        for idx, post in enumerate(posts):
            try:
                normalized.append(_normalize_post(post, idx))
            except Exception as e:
                _log(f"Error normalizing post {idx}: {e}")
                continue
        
        return normalized
        
    except subprocess.TimeoutExpired:
        _log("Timeout waiting for Reddit search")
        return []
    except json.JSONDecodeError as e:
        _log(f"JSON parse error: {e}")
        return []
    except Exception as e:
        _log(f"Unexpected error: {type(e).__name__}: {e}")
        return []


def search_and_enrich(
    topic: str,
    depth: str = "default",
    mock: bool = False,
) -> Dict[str, Any]:
    """Main entry point matching reddit.py interface.
    
    Args:
        topic: Search topic
        depth: Search depth (quick, default, deep)
        mock: If True, return empty results (for testing)
        
    Returns:
        Dict with items, error, and metadata
    """
    if mock:
        return {"items": [], "source": "reddit_readonly_mock"}
    
    # Configure based on depth
    depth_config = {
        "quick": {"limit": 15, "timeframe": "week"},
        "default": {"limit": 30, "timeframe": "month"},
        "deep": {"limit": 50, "timeframe": "month"},
    }
    
    config = depth_config.get(depth, depth_config["default"])
    
    # Run search
    posts = search_reddit_readonly(
        query=topic,
        limit=config["limit"],
        sort="relevance",
        timeframe=config["timeframe"],
    )
    
    if not posts:
        return {
            "items": [],
            "source": "reddit_readonly",
            "error": "No results found or search failed",
        }
    
    return {
        "items": posts,
        "source": "reddit_readonly",
        "count": len(posts),
    }
