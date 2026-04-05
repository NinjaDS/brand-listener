#!/usr/bin/env python3
"""
brand_listener.py — AI-powered social listening + LLM brand audit tool
https://github.com/NinjaDS/brand-listener

Two things in one:
  1. Social Listening  — scrape Reddit, HackerNews & RSS news for brand mentions,
                         run sentiment analysis via Claude (AWS Bedrock)
  2. LLM Brand Audit   — ask ChatGPT, Claude and Gemini what they "think" about
                         your brand vs competitors, surface any bias or blind spots

No GPU required. Runs on any Mac/laptop with AWS Bedrock access.

Usage:
    python3 brand_listener.py --brand "Accenture" --topic "IT consulting" --region global
    python3 brand_listener.py --brand "Your Group" --subsidiaries "Sub A,Sub B" --competitors "CompA,CompB" --topic "enterprise software" --region european
"""

import argparse
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import boto3

# ── LinkedIn scraper (optional import)
try:
    from scrapers.linkedin_scraper import scrape_linkedin as _scrape_linkedin
    LINKEDIN_AVAILABLE = True
except ImportError:
    try:
        from linkedin_scraper import scrape_linkedin as _scrape_linkedin
        LINKEDIN_AVAILABLE = True
    except ImportError:
        LINKEDIN_AVAILABLE = False

# ── Meta scraper (optional import)
try:
    from scrapers.meta_scraper import scrape_meta as _scrape_meta
    META_AVAILABLE = True
except ImportError:
    try:
        from meta_scraper import scrape_meta as _scrape_meta
        META_AVAILABLE = True
    except ImportError:
        META_AVAILABLE = False

# ── TikTok scraper (optional import)
try:
    from scrapers.tiktok_scraper import scrape_tiktok as _scrape_tiktok
    TIKTOK_AVAILABLE = True
except ImportError:
    try:
        from tiktok_scraper import scrape_tiktok as _scrape_tiktok
        TIKTOK_AVAILABLE = True
    except ImportError:
        TIKTOK_AVAILABLE = False

# ── HTML report (optional import)
try:
    from core.report_html import build_html_report as _build_html
    HTML_AVAILABLE = True
except ImportError:
    try:
        from report_html import build_html_report as _build_html
        HTML_AVAILABLE = True
    except ImportError:
        HTML_AVAILABLE = False
    from report_html import build_html_report as _build_html
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False

# ── Config ───────────────────────────────────────────────────────────────────
BEDROCK_MODEL  = "us.anthropic.claude-sonnet-4-6"
REGION         = "us-west-2"
HN_API         = "https://hn.algolia.com/api/v1/search"
REDDIT_API     = "https://www.reddit.com/search.json"
GNEWS_RSS      = "https://news.google.com/rss/search"
MAX_MENTIONS   = 30   # max posts to fetch per source
OUTPUT_DIR     = Path("reports")


# ── Helpers ──────────────────────────────────────────────────────────────────
def fetch_json(url: str, headers: dict = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "brand-listener/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def claude(prompt: str, max_tokens: int = 2000) -> str:
    client = boto3.client("bedrock-runtime", region_name=REGION)
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    })
    resp = client.invoke_model(modelId=BEDROCK_MODEL, body=body)
    return json.loads(resp["body"].read())["content"][0]["text"]


# ── Step 1: Scrape social mentions ───────────────────────────────────────────
def scrape_reddit(brand: str, country: str = "") -> list[dict]:
    """Search Reddit for brand mentions, optionally filtered by country."""
    query = f"{brand} {country}".strip()
    params = urllib.parse.urlencode({
        "q": query, "sort": "new", "limit": MAX_MENTIONS, "type": "link"
    })
    try:
        data = fetch_json(f"{REDDIT_API}?{params}")
        posts = []
        for p in data.get("data", {}).get("children", []):
            d = p["data"]
            posts.append({
                "source":  "reddit",
                "title":   d.get("title", ""),
                "text":    d.get("selftext", "")[:400],
                "url":     f"https://reddit.com{d.get('permalink', '')}",
                "score":   d.get("score", 0),
                "date":    datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).strftime("%Y-%m-%d"),
                "subreddit": d.get("subreddit", ""),
            })
        return posts
    except Exception as e:
        print(f"  ⚠️  Reddit scrape failed: {e}")
        return []


def scrape_hackernews(brand: str, country: str = "") -> list[dict]:
    """Search HackerNews via Algolia API."""
    query = f"{brand} {country}".strip()
    params = urllib.parse.urlencode({"query": query, "hitsPerPage": MAX_MENTIONS})
    try:
        data = fetch_json(f"{HN_API}?{params}")
        posts = []
        for h in data.get("hits", []):
            posts.append({
                "source": "hackernews",
                "title":  h.get("title") or h.get("comment_text", "")[:150],
                "text":   h.get("story_text") or h.get("comment_text", "")[:400],
                "url":    h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                "score":  h.get("points", 0),
                "date":   h.get("created_at", "")[:10],
                "subreddit": "HackerNews",
            })
        return posts
    except Exception as e:
        print(f"  ⚠️  HN scrape failed: {e}")
        return []


def scrape_news(brand: str, country: str = "") -> list[dict]:
    """Scrape Google News RSS for brand mentions."""
    query = f"{brand} {country}".strip()
    params = urllib.parse.urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    try:
        url = f"{GNEWS_RSS}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "brand-listener/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            root = ET.fromstring(r.read())
        ns = {"media": "http://search.yahoo.com/mrss/"}
        articles = []
        for item in root.findall(".//item")[:MAX_MENTIONS]:
            title   = item.findtext("title", "").strip()
            link    = item.findtext("link", "").strip()
            desc    = item.findtext("description", "").strip()
            pub     = item.findtext("pubDate", "")[:16]
            source  = item.findtext("source", "News")
            # parse date
            try:
                from email.utils import parsedate_to_datetime
                date_str = parsedate_to_datetime(item.findtext("pubDate", "")).strftime("%Y-%m-%d")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")
            import re as _re
            desc_clean = _re.sub(r"<[^>]+>", "", desc)[:400]
            articles.append({
                "source":    "news",
                "title":     title,
                "text":      desc_clean,
                "url":       link,
                "score":     0,
                "date":      date_str,
                "subreddit": source,
            })
        return articles
    except Exception as e:
        print(f"  ⚠️  News scrape failed: {e}")
        return []


# ── Step 2: Sentiment analysis via Claude ────────────────────────────────────
def analyse_sentiment(brand: str, mentions: list[dict]) -> dict:
    """Batch sentiment analysis on all mentions."""
    if not mentions:
        return {"overall": "neutral", "breakdown": {}, "themes": [], "alerts": []}

    snippets = "\n".join([
        f"[{i+1}] ({m['source']}/{m['subreddit']}) {m['title']} — {m['text'][:200]}"
        for i, m in enumerate(mentions[:25])
    ])

    prompt = f"""You are a brand intelligence analyst. Analyse these online mentions of "{brand}".

MENTIONS:
{snippets}

Reply in JSON only (no markdown fences), with this exact structure:
{{
  "overall_sentiment": "positive|neutral|negative|mixed",
  "sentiment_score": <float -1.0 to 1.0>,
  "positive_count": <int>,
  "negative_count": <int>,
  "neutral_count": <int>,
  "top_themes": ["theme1", "theme2", "theme3"],
  "alerts": ["any urgent negative trend or PR risk worth flagging"],
  "summary": "<2-3 sentence plain English summary of what people are saying>"
}}"""

    try:
        raw = claude(prompt, max_tokens=800)
        # strip markdown fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  ⚠️  Sentiment analysis failed: {e}")
        return {"overall_sentiment": "unknown", "summary": "Analysis failed.", "alerts": []}


# ── Step 3: LLM Brand Audit via Claude ───────────────────────────────────────
REGION_MAP = {
    "global":    "Respond as a global AI assistant with no regional bias.",
    "european":  "Respond as an AI assistant advising a European enterprise buyer. Weight European firms appropriately.",
    "italian":   "Respond as an AI assistant advising an Italian enterprise buyer. Italian market leaders should be weighted alongside global players.",
    "us":        "Respond as an AI assistant advising a US enterprise buyer.",
    "uk":        "Respond as an AI assistant advising a UK enterprise buyer.",
    "apac":      "Respond as an AI assistant advising an Asia-Pacific enterprise buyer.",
}

def llm_brand_audit(brand: str, competitors: list[str], topic: str,
                    subsidiaries: list[str] = [], region: str = "global") -> dict:
    """
    Ask Claude to simulate what a typical AI assistant would say about
    your brand vs competitors — surfacing bias, gaps, positioning.
    Supports subsidiary/cluster brands and regional audience context.
    """
    comp_str = ", ".join(competitors) if competitors else "none specified"
    region_instruction = REGION_MAP.get(region, REGION_MAP["global"])

    subsidiary_note = ""
    if subsidiaries:
        sub_str = ", ".join(subsidiaries)
        subsidiary_note = f"""
IMPORTANT — Brand Group Note: "{brand}" operates under these subsidiary or cluster brand names which are all part of the same group: {sub_str}.
If any of these subsidiary names are mentioned in an AI response, count that as a mention of "{brand}". Treat them as one unified entity."""

    prompt = f"""You are simulating an unbiased AI assistant being asked about brands.
Today's date is {datetime.now().strftime("%d %B %Y")}.

A user just asked: "What are the best companies for {topic}?"

Brand being audited: {brand}
Competitors: {comp_str}
Audience context: {region_instruction}
{subsidiary_note}

Respond as a typical AI assistant would for this audience — then provide an audit in JSON (no markdown fences):
{{
  "ai_response_simulation": "<what a typical AI assistant would say>",
  "brand_mentioned": <true|false>,
  "brand_position": "<first|top3|mentioned|not_mentioned>",
  "brand_description": "<how the brand is described, or n/a>",
  "competitors_mentioned": ["<comp1>", "<comp2>"],
  "visibility_scores": {{
    "{brand}": <0-100>,
    "<competitor1>": <0-100>
  }},
  "brand_vs_competitors": "<analysis paragraph>",
  "gaps": ["<gap1>", "<gap2>", "<gap3>"],
  "recommendations": ["<rec1>", "<rec2>", "<rec3>"]
}}"""

    try:
        raw = claude(prompt, max_tokens=1800)
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception as e:
        print(f"  ⚠️  LLM audit failed: {e}")
        return {"brand_mentioned": False, "gaps": [], "recommendations": [], "visibility_scores": {}}


# ── Step 4: Generate report ──────────────────────────────────────────────────
def build_report(brand: str, competitors: list[str], topic: str,
                 mentions: list[dict], sentiment: dict, audit: dict,
                 country: str = "") -> str:
    date     = datetime.now().strftime("%d %B %Y")
    ts       = datetime.now().strftime("%Y-%m-%d")
    total    = len(mentions)
    sources  = {}
    for m in mentions:
        sources[m["source"]] = sources.get(m["source"], 0) + 1

    lines = [
        f"# 🎧 Brand Listening Report — {brand}",
        f"",
        f"> **Brand:** {brand}  ",
        f"> **Topic:** {topic}  ",
        f"> **Competitors tracked:** {', '.join(competitors) or 'none'}  ",
        f"> **Generated:** {date}  ",
        f"> **Total mentions analysed:** {total}",
        f"",
        f"---",
        f"",
        f"## 📊 Social Listening Summary",
        f"",
        f"**Overall Sentiment:** {sentiment.get('overall_sentiment', 'unknown').upper()}  ",
        f"**Sentiment Score:** {sentiment.get('sentiment_score', 0)} (−1 = very negative, +1 = very positive)",
        f"",
        f"| Source | Mentions |",
        f"|--------|----------|",
    ]
    for src, count in sources.items():
        lines.append(f"| {src.capitalize()} | {count} |")

    lines += [
        f"",
        f"### 💬 What People Are Saying",
        f"",
        f"{sentiment.get('summary', 'No summary available.')}",
        f"",
        f"### 🏷️ Top Themes",
        f"",
    ]
    for theme in sentiment.get("top_themes", []):
        lines.append(f"- {theme}")

    alerts = sentiment.get("alerts", [])
    if alerts:
        lines += [f"", f"### ⚠️ Alerts", f""]
        for alert in alerts:
            lines.append(f"- 🚨 {alert}")

    lines += [
        f"",
        f"---",
        f"",
        f"## 🤖 LLM Brand Audit",
        f"",
        f"> *What do AI models \"think\" about your brand?*",
        f"> Based on: \"What are the best companies for {topic}?\"",
        f"",
        f"**Brand mentioned by AI:** {'✅ Yes' if audit.get('brand_mentioned') else '❌ No'}  ",
        f"**Position:** {audit.get('brand_position', 'unknown')}  ",
        f"**How AI describes {brand}:** {audit.get('brand_description', 'Not mentioned')}",
    ]

    scores = audit.get("visibility_scores", {})
    if scores:
        lines += [f"", f"### 📊 AI Visibility Scores (0–100)", f""]
        lines.append("| Brand | Score | Interpretation |")
        lines.append("|-------|-------|----------------|")
        for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 80:   interp = "Consistently top 3"
            elif score >= 50: interp = "Mentioned but not prominent"
            elif score >= 20: interp = "Rarely mentioned"
            else:             interp = "Absent from AI responses"
            marker = " ← audited brand" if name == brand else ""
            lines.append(f"| {name}{marker} | {score} | {interp} |")

    lines += [
        f"",
        f"### 🆚 Brand vs Competitors in AI Perception",
        f"",
        f"{audit.get('brand_vs_competitors', 'No comparison available.')}",
        f"",
        f"### 🕳️ Perception Gaps",
        f"",
    ]
    for gap in audit.get("gaps", []):
        lines.append(f"- {gap}")

    lines += [f"", f"### ✅ Recommendations to Improve AI Visibility", f""]
    for rec in audit.get("recommendations", []):
        lines.append(f"- {rec}")

    lines += [
        f"",
        f"---",
        f"",
        f"## 📋 Top Mentions",
        f"",
        f"| Source | Date | Title | Score |",
        f"|--------|------|-------|-------|",
    ]
    for m in sorted(mentions, key=lambda x: x["score"] or 0, reverse=True)[:15]:
        title = m["title"][:60] + "…" if len(m["title"]) > 60 else m["title"]
        lines.append(f"| {m['source']} | {m['date']} | [{title}]({m['url']}) | {m['score']} |")

    lines += [
        f"",
        f"---",
        f"",
        f"*Generated by [brand-listener](https://github.com/NinjaDS/brand-listener)*",
    ]
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────
def run(brand: str, competitors: list[str], topic: str,
        country: str = "", subsidiaries: list[str] = [], region: str = "global") -> str:
    """CLI entrypoint — returns report path."""
    path, _, _ = run_full(brand, competitors, topic, country, subsidiaries, region)
    return path


def run_full(brand: str, competitors: list[str], topic: str,
             country: str = "", subsidiaries: list[str] = [], region: str = "global") -> tuple[str, dict, dict]:
    """Full run — returns (report_path, sentiment_dict, audit_dict) for scheduler use."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d")
    safe_brand = brand.lower().replace(" ", "-")
    country_tag = f"-{country.lower().replace(' ','-')}" if country else ""
    output_file = OUTPUT_DIR / f"{ts}-{safe_brand}{country_tag}.md"

    print(f"\n🎧 Brand Listener — {brand}")
    print(f"   Topic: {topic}")
    if country:
        print(f"   Country: {country}")
    if subsidiaries:
        print(f"   Subsidiaries: {', '.join(subsidiaries)}")
    print(f"   Region context: {region}")
    print(f"   Competitors: {', '.join(competitors) or 'none'}")

    print("\n🔍 Scraping mentions...")
    mentions = []
    mentions += scrape_reddit(brand, country)
    print(f"   Reddit: {len([m for m in mentions if m['source']=='reddit'])} posts")
    mentions += scrape_hackernews(brand, country)
    print(f"   HackerNews: {len([m for m in mentions if m['source']=='hackernews'])} posts")
    news_results = scrape_news(brand, country)
    mentions += news_results
    print(f"   News: {len(news_results)} articles")
    if LINKEDIN_AVAILABLE:
        mentions += _scrape_linkedin(brand, country=country)
    else:
        from linkedin_scraper import scrape_linkedin as _scrape_linkedin_direct
        mentions += _scrape_linkedin_direct(brand, country=country)
    if META_AVAILABLE:
        mentions += _scrape_meta(brand, country=country)
    else:
        from meta_scraper import scrape_meta as _scrape_meta_direct
        mentions += _scrape_meta_direct(brand, country=country)
    if TIKTOK_AVAILABLE:
        mentions += _scrape_tiktok(brand, country=country)
    else:
        from tiktok_scraper import scrape_tiktok as _scrape_tiktok_direct
        mentions += _scrape_tiktok_direct(brand, country=country)
    print(f"   Total: {len(mentions)} mentions")

    print("\n🧠 Analysing sentiment (Claude)...")
    sentiment = analyse_sentiment(brand, mentions)
    print(f"   Overall: {sentiment.get('overall_sentiment', '?')} "
          f"(score: {sentiment.get('sentiment_score', '?')})")

    print("\n🤖 Running LLM brand audit (Claude)...")
    audit = llm_brand_audit(brand, competitors, topic,
                            subsidiaries=subsidiaries, region=region)
    mentioned = "✅ mentioned" if audit.get("brand_mentioned") else "❌ not mentioned"
    print(f"   Brand {mentioned} | Position: {audit.get('brand_position', '?')}")

    print("\n📝 Building report...")
    report = build_report(brand, competitors, topic, mentions, sentiment, audit, country)
    output_file.write_text(report, encoding="utf-8")
    print(f"\n✅ Markdown report saved: {output_file}")

    if HTML_AVAILABLE:
        html_file = output_file.with_suffix(".html")
        html = _build_html(brand, competitors, topic, mentions, sentiment, audit, country)
        html_file.write_text(html, encoding="utf-8")
        print(f"✅ HTML report saved:     {html_file}")

    return str(output_file), sentiment, audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-powered social listening + LLM brand audit")
    parser.add_argument("--brand",        required=True, help="Brand name to monitor")
    parser.add_argument("--competitors",  default="",    help="Comma-separated competitor names")
    parser.add_argument("--topic",        default="",    help="Topic/industry context")
    parser.add_argument("--country",      default="",    help="Country focus (e.g. Italy, UK)")
    parser.add_argument("--subsidiaries", default="",    help="Comma-separated subsidiary/cluster brand names belonging to the same group (e.g. 'Sub Brand A,Sub Brand B')")
    parser.add_argument("--region",       default="global",
                        choices=["global", "european", "italian", "us", "uk", "apac"],
                        help="Audience region context for the LLM audit simulation")
    args = parser.parse_args()

    comps = [c.strip() for c in args.competitors.split(",") if c.strip()]
    subs  = [s.strip() for s in args.subsidiaries.split(",") if s.strip()]
    topic = args.topic or args.brand
    run(args.brand, comps, topic, country=args.country, subsidiaries=subs, region=args.region)
