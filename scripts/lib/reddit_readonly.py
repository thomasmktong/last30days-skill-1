"""Reddit search via Reddit's public JSON API for /last30days.

Pure Python implementation - no external Node.js dependencies.
Uses Reddit's old.reddit.com JSON endpoints which don't require authentication.

Fallback when ScrapeCreators API key is not available.
"""

import json
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

# Configuration
REDDIT_BASE_URL = "https://old.reddit.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 1.0  # seconds


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


def _fetch_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[Dict[str, Any]]:
    """Fetch JSON from URL with retry logic.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Parsed JSON dict or None on failure
    """
    headers = {"User-Agent": USER_AGENT}
    
    for attempt in range(DEFAULT_RETRIES):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=timeout) as response:
                data = response.read().decode("utf-8")
                return json.loads(data)
        except HTTPError as e:
            if e.code == 429:  # Rate limited
                backoff = DEFAULT_BACKOFF * (2 ** attempt)
                _log(f"Rate limited, waiting {backoff}s...")
                time.sleep(backoff)
                continue
            elif e.code >= 500:  # Server error, retry
                backoff = DEFAULT_BACKOFF * (2 ** attempt)
                _log(f"Server error {e.code}, retrying in {backoff}s...")
                time.sleep(backoff)
                continue
            else:
                _log(f"HTTP error {e.code}: {e.reason}")
                return None
        except URLError as e:
            _log(f"URL error: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            _log(f"JSON parse error: {e}")
            return None
        except Exception as e:
            _log(f"Unexpected error: {type(e).__name__}: {e}")
            return None
    
    return None


def search_reddit(
    query: str,
    sort: str = "relevance",
    time_filter: str = "month",
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """Search Reddit using public JSON API.
    
    Args:
        query: Search query string
        sort: Sort order (relevance, hot, new, top)
        time_filter: Time filter (hour, day, week, month, year, all)
        limit: Max results to return (Reddit max: 100)
        
    Returns:
        List of post dicts
    """
    # Build search URL
    params = {
        "q": query,
        "sort": sort,
        "t": time_filter,
        "limit": min(limit, 100),  # Reddit max per page
        "raw_json": "1",
    }
    
    url = f"{REDDIT_BASE_URL}/r/all/search.json?{urlencode(params)}"
    _log(f"Searching Reddit for: {query}")
    
    data = _fetch_json(url)
    
    if not data:
        return []
    
    # Extract posts from Reddit's nested structure
    children = data.get("data", {}).get("children", [])
    
    posts = []
    for child in children:
        try:
            post_data = child.get("data", {})
            
            # Skip if not a post (could be ad, promoted, etc.)
            if post_data.get("is_self") is None and "reddit.com" not in post_data.get("url", ""):
                continue
            
            posts.append(post_data)
        except Exception as e:
            _log(f"Error parsing post: {e}")
            continue
    
    _log(f"Found {len(posts)} posts")
    return posts


def _normalize_post(post: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Normalize a Reddit post to last30days internal format.
    
    Args:
        post: Post dict from Reddit API
        idx: Index for ID generation
        
    Returns:
        Normalized post dict matching last30days schema
    """
    permalink = post.get("permalink", "")
    url = post.get("url", "")
    
    # Ensure URL is a proper Reddit thread URL
    if not url:
        url = f"https://www.reddit.com{permalink}" if permalink else ""
    elif url.startswith("/r/"):
        url = f"https://www.reddit.com{url}"
    
    # Extract date
    date_str = _parse_date(post.get("created_utc"))
    created_iso = post.get("created_utc")
    if created_iso and isinstance(created_iso, (int, float)):
        try:
            created_iso = datetime.fromtimestamp(float(created_iso), tz=timezone.utc).isoformat()
        except:
            created_iso = None
    
    # Build normalized result
    return {
        "id": f"RR{idx}",
        "type": "reddit",
        "source": "reddit_readonly",
        "title": post.get("title", ""),
        "text": post.get("selftext", "") or post.get("selftext_snippet", ""),
        "url": url,
        "permalink": permalink,
        "author": post.get("author", "[deleted]"),
        "subreddit": post.get("subreddit", ""),
        "date": date_str,
        "created_iso": created_iso,
        "score": post.get("score", 0),
        "ups": post.get("ups", post.get("score", 0)),
        "downs": post.get("downs", 0),
        "num_comments": post.get("num_comments", 0),
        "engagement": post.get("score", 0) + (post.get("num_comments", 0) * 2),
        "is_self": post.get("is_self", False),
        "flair": post.get("link_flair_text", "") or post.get("flair", ""),
        "over_18": post.get("over_18", False),
        "thumbnail": post.get("thumbnail", ""),
    }


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
    posts = search_reddit(
        query=topic,
        sort="relevance",
        time_filter=config["timeframe"],
        limit=config["limit"],
    )
    
    if not posts:
        return {
            "items": [],
            "source": "reddit_readonly",
            "error": "No results found or search failed",
        }
    
    # Normalize posts
    normalized = []
    for idx, post in enumerate(posts):
        try:
            normalized.append(_normalize_post(post, idx))
        except Exception as e:
            _log(f"Error normalizing post {idx}: {e}")
            continue
    
    return {
        "items": normalized,
        "source": "reddit_readonly",
        "count": len(normalized),
    }
