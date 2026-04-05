#!/usr/bin/env python3
"""
meta_scraper.py — Meta (Facebook + Instagram) mention scraper via Google Search
Part of brand-listener: https://github.com/NinjaDS/brand-listener

Meta's APIs are locked down for public access. This module uses
Google Search (site:facebook.com / site:instagram.com) to surface
public posts, pages, and profiles mentioning the brand.

No API key needed for basic use. Optional: set GOOGLE_CSE_ID and
GOOGLE_API_KEY env vars to use the Google Custom Search API for
higher volume without rate limits.
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


def scrape_meta(brand: str, max_results: int = 20, country: str = "") -> list[dict]:
    """
    Search Facebook and Instagram public content for brand mentions via Google.
    Covers: FB pages, posts, groups + Instagram profiles and posts.
    """
    country_suffix = f' "{country}"' if country else ""
    queries = [
        f'site:facebook.com/posts "{brand}"{country_suffix}',
        f'site:facebook.com/story "{brand}"{country_suffix}',
        f'site:facebook.com "{brand}" page{country_suffix}',
        f'site:instagram.com "{brand}"{country_suffix}',
        f'site:instagram.com/p "{brand}"{country_suffix}',
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

            if not url:
                continue

            # classify platform + content type
            if "instagram.com" in url:
                platform = "instagram"
                if "/p/" in url or "/reel/" in url:
                    content_type = "post"
                elif "/stories/" in url:
                    content_type = "story"
                else:
                    content_type = "profile"
            elif "facebook.com" in url:
                platform = "facebook"
                if "/posts/" in url or "/story" in url:
                    content_type = "post"
                elif "/groups/" in url:
                    content_type = "group"
                elif "/videos/" in url:
                    content_type = "video"
                else:
                    content_type = "page"
            else:
                continue

            all_results.append({
                "source":    "meta",
                "type":      f"{platform}/{content_type}",
                "title":     title,
                "text":      snippet[:400],
                "url":       url,
                "score":     None,
                "date":      datetime.now().strftime("%Y-%m-%d"),
                "subreddit": f"Meta/{platform.capitalize()}",
            })

    # deduplicate
    seen, unique = set(), []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    fb_count = sum(1 for r in unique if "facebook" in r["type"])
    ig_count = sum(1 for r in unique if "instagram" in r["type"])
    print(f"   Meta: {len(unique)} results ({fb_count} Facebook, {ig_count} Instagram)")
    return unique[:max_results]
