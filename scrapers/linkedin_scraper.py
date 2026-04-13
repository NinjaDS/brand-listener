"""
LinkedIn scraper powered by LinkdAPI.
Function signature preserved: scrape_linkedin(brand, max_results, country)
"""

import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def scrape_linkedin(brand: str, max_results: int = 10, country: str = "UK") -> list:
    """
    Scrape LinkedIn posts for a brand using LinkdAPI.

    Args:
        brand: Brand name (used as fallback search keyword)
        max_results: Maximum number of results to return
        country: Country filter (not used by LinkdAPI directly but kept for compat)

    Returns:
        List of post dicts with keys: source, type, title, text, url, score,
        date, subreddit, likes, comments_count, engagements
    """
    api_key = os.environ.get("LINKDAPI_KEY", "")
    if not api_key:
        logger.warning("LINKDAPI_KEY not set — skipping LinkedIn scrape")
        return []

    try:
        from linkdapi import Linkdapi  # type: ignore
    except ImportError:
        logger.warning("linkdapi package not installed — skipping LinkedIn scrape")
        return []

    client = Linkdapi(api_key)
    posts = []

    # Search posts
    try:
        search_keyword = brand
        logger.info(f"Searching LinkedIn posts for: {search_keyword}")
        raw_posts = client.search_posts(keyword=search_keyword, sort_by="date_posted")
        time.sleep(3)

        for post in (raw_posts or [])[:max_results]:
            try:
                engagements = post.get("engagements", {}) or {}
                likes = engagements.get("totalReactions", 0) or 0
                comments = engagements.get("commentsCount", 0) or 0
                total_eng = likes + comments

                # Parse date
                raw_date = post.get("date") or post.get("postedAt") or ""
                try:
                    date_str = str(raw_date)[:10] if raw_date else datetime.utcnow().strftime("%Y-%m-%d")
                except Exception:
                    date_str = datetime.utcnow().strftime("%Y-%m-%d")

                text = post.get("text") or post.get("content") or ""
                url = post.get("postUrl") or post.get("url") or ""

                posts.append({
                    "source": "linkedin",
                    "type": "post",
                    "title": text[:100] if text else "(no title)",
                    "text": text,
                    "url": url,
                    "score": total_eng,
                    "date": date_str,
                    "subreddit": None,
                    "likes": likes,
                    "comments_count": comments,
                    "engagements": engagements,
                })
            except Exception as e:
                logger.debug(f"Error parsing post: {e}")
                continue

    except Exception as e:
        logger.warning(f"LinkedIn post search failed: {e}")

    logger.info(f"LinkedIn scrape returned {len(posts)} posts for '{brand}'")
    return posts
