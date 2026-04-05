# 🏗️ Brand Listener — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BRAND LISTENER SYSTEM                              │
│                    AI-powered Social Listening + LLM Brand Audit                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   watchlist.json │  ← User defines brands, competitors, topic, schedule, email
│  (Configuration) │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           SCHEDULER  (scheduler/scheduler.py)                    │
│                                                                                  │
│   Triggers automatically: weekly / daily / on-demand                            │
│   Loads watchlist → loops over each brand → orchestrates full pipeline          │
└────────────────────────────────┬─────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────▼───────────────────────────────┐
         │          ★ ADAPTIVE LAYER  (Karpathy-inspired)        │
         │                                                        │
         │  1. Load history from prior run (reports/history.json)│
         │  2. Extract top themes from last week's report        │
         │  3. Blend themes into this week's search query        │
         │                                                        │
         │  Example:                                              │
         │  Week 1 → query: "Adidas sportswear"                  │
         │  Week 2 → query: "Adidas sportswear sustainability    │
         │                   Yeezy controversy" ← auto-adapted!  │
         │                                                        │
         │  ★ The tool gets smarter every week — it chases       │
         │    real conversations, not static keywords            │
         └───────────────────────┬────────────────────────────────┘
                                 │ adaptive query
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DATA COLLECTION  (scrapers/ + core/)                     │
│                                                                                 │
│  ┌────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Reddit    │  │ HackerNews  │  │  News    │  │ LinkedIn │  │   Meta    │  │
│  │ (Reddit    │  │ (Algolia    │  │ (Google  │  │ (DDG     │  │ Facebook  │  │
│  │  JSON API) │  │  API)       │  │  News    │  │  search) │  │ Instagram │  │
│  │            │  │             │  │  RSS)    │  │          │  │  (DDG)    │  │
│  └────────────┘  └─────────────┘  └──────────┘  └──────────┘  └───────────┘  │
│                                                                    ┌──────────┐ │
│                                                                    │  TikTok  │ │
│                                                                    │  (DDG    │ │
│                                                                    │  search) │ │
│                                                                    └──────────┘ │
│                                                                                 │
│  All sources → unified mention format: {source, title, text, url, date, score} │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │ up to 180 mentions
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     SENTIMENT ANALYSIS  (core/brand_listener.py)                │
│                                                                                 │
│  Claude (AWS Bedrock) analyses all mentions in one batch:                       │
│  → Overall sentiment (positive / negative / neutral / mixed)                   │
│  → Sentiment score (-1.0 to +1.0)                                              │
│  → Top themes (these feed back into the ★ ADAPTIVE LAYER next week)            │
│  → Alerts: PR risks, emerging negative trends                                  │
│  → 2-3 sentence plain English summary                                          │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       LLM BRAND AUDIT  (core/brand_listener.py)                 │
│                                                                                 │
│  Claude simulates: "What would an AI assistant say about your brand?"           │
│                                                                                 │
│  → Is the brand mentioned at all?                                               │
│  → What position? (first / top3 / mentioned / not mentioned)                   │
│  → AI visibility scores: Brand vs each competitor (0-100)                      │
│  → Perception gaps: Where does the brand lose vs competitors in AI?            │
│  → Recommendations: How to improve AI visibility                               │
│                                                                                 │
│  Region-aware: global / uk / european / us / italian / apac audience           │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ★ TREND DETECTION  (scheduler/scheduler.py)                  │
│                                                                                 │
│  Compares THIS week vs LAST week (from history.json):                          │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │  Last week score: +0.42 (positive)                           │              │
│  │  This week score: +0.05 (mixed)                              │              │
│  │  Delta: -0.37  ← exceeds threshold (-0.3)                   │              │
│  │                                                               │              │
│  │  → 🚨 TREND ALERT: Sentiment dropped 0.37 points!           │              │
│  └──────────────────────────────────────────────────────────────┘              │
│                                                                                 │
│  Alerts are prepended to report + email subject line flagged 🚨                │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         REPORT GENERATION  (core/report_html.py)                │
│                                                                                 │
│  Output formats:                                                                │
│  ┌────────────────────┐    ┌─────────────────────┐                             │
│  │  Markdown (.md)    │    │   HTML (.html)       │                             │
│  │  reports/YYYY-MM-  │    │   Full styled report │                             │
│  │  DD-brand.md       │    │   with charts        │                             │
│  └────────────────────┘    └─────────────────────┘                             │
│                                                                                 │
│  Sections: Sentiment Summary → Themes → Alerts → LLM Audit →                  │
│            Visibility Scores → Gaps → Recommendations → Top Mentions           │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
         ┌─────────────────────┐          ┌─────────────────────┐
         │   Save to reports/  │          │   Email delivery    │
         │   (always)          │          │   (if SMTP set)     │
         │                     │          │                     │
         │  reports/           │          │  Subject: 🚨 if     │
         │  ├── history.json   │          │  trend alert fired  │
         │  ├── YYYY-MM-DD-    │          │                     │
         │  │   brand.md       │          │  Set env vars:      │
         │  └── YYYY-MM-DD-    │          │  SMTP_USER          │
         │      brand.html     │          │  SMTP_PASS          │
         └─────────────────────┘          └─────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Update history.json│  ← feeds back into ★ ADAPTIVE LAYER next run
         │  (top themes,       │
         │   sentiment score,  │
         │   date, report path)│
         └─────────────────────┘
```

---

## ★ The Adaptive Loop (Key Differentiator)

```
                     ┌──────────────────────────────────┐
                     │         ADAPTIVE LOOP            │
                     │                                  │
         ┌───────────▼───────────┐                      │
         │    Run brand report   │                      │
         └───────────┬───────────┘                      │
                     │                                  │
         ┌───────────▼───────────┐                      │
         │  Extract top themes   │                      │
         │  from this report     │                      │
         └───────────┬───────────┘                      │
                     │                                  │
         ┌───────────▼───────────┐                      │
         │  Save to history.json │                      │
         └───────────┬───────────┘                      │
                     │                                  │
         ┌───────────▼───────────┐                      │
         │  Next week: blend     │                      │
         │  themes into query    │──────────────────────┘
         │  (adaptive search)    │
         └───────────────────────┘

  Static tools repeat the same search forever.
  Brand Listener evolves — chasing what matters right now.
```

---

## Data Flow Summary

```
watchlist.json
      │
      ▼
 Scheduler ──► Adaptive Layer (history.json) ──► Refined Query
                                                        │
                    ┌───────────────────────────────────┤
                    ▼           ▼           ▼           ▼
                 Reddit      HackerNews   News    LinkedIn/Meta/TikTok
                    └───────────────────────────────────┘
                                        │
                              Sentiment Analysis (Claude)
                                        │
                               LLM Brand Audit (Claude)
                                        │
                              ★ Trend Detection (week-on-week)
                                        │
                          ┌─────────────┴─────────────┐
                          ▼                           ▼
                    Report (.md/.html)          Email Alert (SMTP)
                          │
                    history.json ──► feeds next week's adaptive query
```

---

*Architecture by [Kumaresa Perumal](https://github.com/NinjaDS) · Brand Listener v2*
