#!/usr/bin/env python3
"""
tiktok_scraper.py — TikTok mention scraper via Google Search
Part of brand-listener: https://github.com/NinjaDS/brand-listener

TikTok has no public API for content scraping. This module uses
Google Search (site:tiktok.com) to surface public videos, creators,
and hashtag pages mentioning the brand.

No API key needed for basic use. Optional: set GOOGLE_CSE_ID and
GOOGLE_API_KEY env vars for higher volume.
"""

import os
import time
import urllib.request
import urllib.parse
import json
import re
from datetime import datetime

GOOGLE_CSE_ID  = os.environ.get("GOOGLE_CSE_ID", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
HEADERS        = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def _google_cse(query: str, num: int = 10) -> list[dict]:
    if not GOOGLE_CSE_ID or not GOOGLE_API_KEY:
        return []
    params = urllib.parse.urlencode({
        "key": GOOGLE_API_KEY, "cx": GOOGLE_CSE_ID,
        "q": query, "num": min(num, 10),
    })
    try:
        req = urllib.request.Request(
            f"https://www.googleapis.com/customsearch/v1?{params}", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("items", [])
    except Exception as e:
        print(f"  ⚠️  Google CSE failed: {e}")
        return []


def _google_scrape(query: str, num: int = 10) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "num": num, "hl": "en"})
    try:
        req = urllib.request.Request(
            f"https://www.google.com/search?{params}", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
        links    = re.findall(r'/url\?q=(https?://[^&"]+)', html)
        titles   = re.findall(r'<h3[^>]*>([^<]+)</h3>', html)
        snippets = re.findall(r'<div[^>]*data-sncf[^>]*>([^<]{30,300})<', html)
        results  = []
        for i, link in enumerate(links[:num]):
            link = urllib.parse.unquote(link)
            if "google.com" in link or "accounts.google" in link:
                continue
            results.append({
                "title":   titles[i] if i < len(titles) else link,
                "link":    link,
                "snippet": snippets[i] if i < len(snippets) else "",
            })
        return results
    except Exception as e:
        print(f"  ⚠️  Google scrape failed: {e}")
        return []


def scrape_tiktok(brand: str, max_results: int = 20, country: str = "") -> list[dict]:
    """
    Search TikTok public content for brand mentions via Google.
    Covers: video posts, creator profiles, hashtag pages.
    """
    # normalise brand to hashtag-style
    hashtag = brand.lower().replace(" ", "")
    country_suffix = f' "{country}"' if country else ""

    queries = [
        f'site:tiktok.com/video "{brand}"{country_suffix}',
        f'site:tiktok.com "{brand}"{country_suffix}',
        f'site:tiktok.com/tag/{hashtag}',
        f'site:tiktok.com "@{hashtag}"',
    ]

    all_results = []
    per_query = max(4, max_results // len(queries))

    for query in queries:
        time.sleep(1.5)
        items = _google_cse(query, per_query) or _google_scrape(query, per_query)

        for item in items:
            url     = item.get("link") or item.get("url", "")
            title   = item.get("title", "")
            snippet = re.sub(r"<[^>]+>", "", item.get("snippet", "") or item.get("htmlSnippet", ""))

            if not url or "tiktok.com" not in url:
                continue

            # classify content type
            if "/video/" in url:
                content_type = "video"
            elif "/tag/" in url:
                content_type = "hashtag"
            elif "/@" in url:
                content_type = "creator"
            else:
                content_type = "other"

            # try to extract creator name from URL
            creator_match = re.search(r'tiktok\.com/@([^/]+)', url)
            creator = creator_match.group(1) if creator_match else ""

            all_results.append({
                "source":    "tiktok",
                "type":      content_type,
                "title":     title,
                "text":      snippet[:400],
                "url":       url,
                "score":     None,
                "date":      datetime.now().strftime("%Y-%m-%d"),
                "subreddit": f"TikTok/{creator}" if creator else "TikTok",
            })

    # deduplicate
    seen, unique = set(), []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    video_count   = sum(1 for r in unique if r["type"] == "video")
    creator_count = sum(1 for r in unique if r["type"] == "creator")
    hashtag_count = sum(1 for r in unique if r["type"] == "hashtag")
    print(f"   TikTok: {len(unique)} results ({video_count} videos, {creator_count} creators, {hashtag_count} hashtags)")
    return unique[:max_results]
