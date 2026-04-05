#!/usr/bin/env python3
"""
linkedin_scraper.py — LinkedIn mention scraper via Google Search
Part of brand-listener: https://github.com/NinjaDS/brand-listener

LinkedIn's API is locked down for public access. This module uses
Google's public search (site:linkedin.com) to surface public posts,
company pages, articles and profiles mentioning the brand.

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
    """Use Google Custom Search API if credentials available."""
    if not GOOGLE_CSE_ID or not GOOGLE_API_KEY:
        return []
    params = urllib.parse.urlencode({
        "key": GOOGLE_API_KEY,
        "cx":  GOOGLE_CSE_ID,
        "q":   query,
        "num": min(num, 10),
    })
    url = f"https://www.googleapis.com/customsearch/v1?{params}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return data.get("items", [])
    except Exception as e:
        print(f"  ⚠️  Google CSE failed: {e}")
        return []


def _google_scrape(query: str, num: int = 10) -> list[dict]:
    """
    Fallback: scrape Google search results page.
    Returns list of {title, url, snippet}.
    """
    params = urllib.parse.urlencode({"q": query, "num": num, "hl": "en"})
    url = f"https://www.google.com/search?{params}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")

        results = []
        # extract href links from Google result anchors
        links = re.findall(r'/url\?q=(https?://[^&"]+)', html)
        titles = re.findall(r'<h3[^>]*>([^<]+)</h3>', html)
        snippets = re.findall(r'<div[^>]*data-sncf[^>]*>([^<]{30,300})<', html)

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


def scrape_linkedin(brand: str, max_results: int = 20, country: str = "") -> list[dict]:
    """
    Search LinkedIn public content for brand mentions via Google.
    Covers: posts, articles, company pages, people profiles.
    Optional country filter narrows results geographically.
    """
    country_suffix = f' "{country}"' if country else ""
    queries = [
        f'site:linkedin.com/posts "{brand}"{country_suffix}',
        f'site:linkedin.com/pulse "{brand}"{country_suffix}',
        f'site:linkedin.com/company "{brand}"',
        f'site:linkedin.com/in "{brand}"{country_suffix}',
    ]

    all_results = []
    per_query = max(4, max_results // len(queries))

    for query in queries:
        time.sleep(1.5)  # be polite to Google

        # try CSE first, fall back to scrape
        items = _google_cse(query, per_query)
        if not items:
            items = _google_scrape(query, per_query)

        for item in items:
            url     = item.get("link") or item.get("url", "")
            title   = item.get("title", "")
            snippet = item.get("snippet", "") or item.get("htmlSnippet", "")
            snippet = re.sub(r"<[^>]+>", "", snippet)  # strip HTML

            if not url or "linkedin.com" not in url:
                continue

            # classify the type of LinkedIn content
            if "/posts/" in url or "/feed/" in url:
                li_type = "post"
            elif "/pulse/" in url or "/article" in url:
                li_type = "article"
            elif "/company/" in url:
                li_type = "company"
            elif "/in/" in url:
                li_type = "profile"
            else:
                li_type = "other"

            all_results.append({
                "source":    "linkedin",
                "type":      li_type,
                "title":     title,
                "text":      snippet[:400],
                "url":       url,
                "score":     None,
                "date":      datetime.now().strftime("%Y-%m-%d"),
                "subreddit": f"LinkedIn/{li_type}",
            })

    # deduplicate by URL
    seen = set()
    unique = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    print(f"   LinkedIn: {len(unique)} results "
          f"({sum(1 for r in unique if r['type']=='post')} posts, "
          f"{sum(1 for r in unique if r['type']=='article')} articles, "
          f"{sum(1 for r in unique if r['type']=='company')} company pages)")
    return unique[:max_results]
