# Brand Ops Marketing Suite — System Architecture

> **Vision:** An AI-powered marketing intelligence platform where agents handle the full research-to-insight pipeline autonomously. Your always-on marketing team.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   BRAND OPS MARKETING SUITE                      │
│                   "Your AI Marketing Team"                       │
└─────────────────────────────────────────────────────────────────┘
                               │
       ┌───────────────────────┼──────────────────────┐
       ▼                       ▼                      ▼
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  INGESTION  │        │  ANALYSIS   │        │  DELIVERY   │
│    LAYER    │        │    LAYER    │        │    LAYER    │
└─────────────┘        └─────────────┘        └─────────────┘
```

---

## Layer 0 — Orchestration (spans everything)

```
┌──────────────────────────────────────────────────────────────┐
│  Task Queue       → assign research briefs to agents         │
│                     track status (queued/running/done/failed) │
│  Skills Library   → reusable workflows per client/brand      │
│                     e.g. "Curlsmith Reddit Scan" as a skill  │
│                     new clients reuse existing skills        │
│  Workspace Mgr    → isolated per brand/client                │
│                     own agents, data, reports, history       │
│                                                              │
│  ✅ AGENT READINESS CHECK (pre-flight before every run)      │
│   └─ data sources live and returning results?                │
│   └─ models reachable? (Bedrock + Apify health check)        │
│   └─ LinkedIn collector credentials valid?                   │
│   └─ skills/templates loaded for this workspace?             │
│   └─ synthetic audience personas warmed up?                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Ingestion + Social Listening

> 📡 **Always-on ear** — continuously monitors sources for brand mentions, keywords, competitor activity. Real-time stream + scheduled batch modes.

```
┌──────────────────────────────────────────────────────────────┐
│  [Reddit Agent]      → posts, comments, subreddits           │
│                        (PRAW — already live in brand-listener)│
│                                                              │
│  [Twitter/X Agent]   → tweets, hashtags, mentions           │
│                        (xurl CLI / Twitter API v2)           │
│                                                              │
│  [LinkedIn Agent]    → company posts, engagement, themes     │
│                        (Apify: vdrmota/linkedin-company-posts)│
│                        ✅ ALREADY BUILT in competitor-intel  │
│                        collector: collectors/linkedin_collector.py │
│                        covers: S&P Global, Moody's, Fitch    │
│                        → extend to any brand/client          │
│                                                              │
│  [TikTok Agent]      → captions, comments, trend sounds      │
│                                                              │
│  [News Agent]        → press coverage, articles, mentions    │
│                        (BeautifulSoup / Playwright)          │
│                                                              │
│  [Review Agent]      → Trustpilot, G2, Amazon reviews        │
│                                                              │
│  [SEO Agent]         → search trends, keyword volume         │
│                        (Google Trends / SerpAPI)             │
│                                                              │
│  Output → Raw Data Store (PostgreSQL + pgvector)             │
└──────────────────────────────────────────────────────────────┘
```

### LinkedIn — What We Already Have

The `competitor-intel` repo contains a working LinkedIn collector:

| What | Detail |
|---|---|
| File | `collectors/linkedin_collector.py` |
| Source | Apify actor `vdrmota/linkedin-company-posts` |
| Data captured | Post text, likes, comments, media type, posted date |
| Current scope | S&P Global, Moody's, Fitch Ratings |
| Extend to | Any brand — just add to `COMPETITORS` dict |
| Free tier | ~100 results/month (enough for 3 brands weekly) |

**For the Marketing Suite:** The LinkedIn collector becomes a general-purpose brand LinkedIn monitor — pluggable per client workspace.

---

## Layer 2 — Analysis + Brand Awareness Measurement

```
┌──────────────────────────────────────────────────────────────┐
│  [Sentiment Agent]                                           │
│   └─ positive / negative / neutral scoring                   │
│   └─ emotion tagging (anger, trust, frustration, love)       │
│                                                              │
│  [Theme Agent]                                               │
│   └─ topic clustering — what people actually talk about      │
│   └─ emerging trend detection over time                      │
│                                                              │
│  [Audience Agent]                                            │
│   └─ demographic profiling (age, gender, region)             │
│   └─ psychographic mapping                                   │
│   └─ community graph — where does the audience hang out?     │
│                                                              │
│  [Competitor Agent]                                          │
│   └─ share of voice vs competitors                           │
│   └─ campaign detection (when a competitor launches)         │
│   └─ gap analysis — what they're missing that you can own    │
│   └─ LinkedIn engagement benchmarking ← uses competitor-intel│
│                                                              │
│  📊 BRAND AWARENESS MODULE                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  └─ mention volume & estimated reach                   │  │
│  │  └─ sentiment share over time (trend line)             │  │
│  │  └─ share of voice vs competitors                      │  │
│  │  └─ community penetration score                        │  │
│  │  └─ LinkedIn presence score (posts, engagement, reach) │  │
│  │  └─ awareness trajectory: growing / stable / declining │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  [Synthetic Audience Agent]  ← unique moat                   │
│   └─ simulate how target personas react to campaigns         │
│   └─ pre-test messaging before going live                    │
│   └─ powered by AWS Bedrock (Claude 3.5 Sonnet)              │
│   └─ 4-layer trait selection (semantic + contextual +        │
│       domain + statistical)                                  │
│   └─ ~70% accuracy vs GWI real human benchmarks             │
└──────────────────────────────────────────────────────────────┘
```

---

## Layer 2b — LLM Council / AI Jury

> Instead of one model making a judgement call — a **panel of AI jurors** with different perspectives deliberates and reaches a consensus verdict with dissenting notes.

```
┌──────────────────────────────────────────────────────────────┐
│  Input: enriched brand data + insights from Layer 2          │
│                                                              │
│  JUROR ROLES (each = a distinct LLM prompt persona):         │
│   🔴 The Sceptic      → challenges assumptions, finds flaws  │
│   🟢 The Optimist     → finds opportunity and upside         │
│   🔵 The Strategist   → business impact, ROI lens            │
│   🟡 The Consumer     → end-user empathy, real-world feel    │
│   ⚫ The Analyst      → data-driven, no fluff, pure signal   │
│                                                              │
│  VERDICT TYPES:                                              │
│   └─ "Is this campaign ready to launch?" → GO / NO GO        │
│   └─ "Is this a brand crisis or noise?" → severity 1–10      │
│   └─ "Which tagline wins?" → ranked with reasoning           │
│   └─ "How does our LinkedIn presence compare?" → score       │
│   └─ Confidence score (0–100%) + dissenting notes            │
│                                                              │
│  Powered by: AWS Bedrock (multi-model) + LangGraph           │
│  Each juror = separate chain → aggregated by Judge agent     │
└──────────────────────────────────────────────────────────────┘
```

**Data flow into the Jury:**
```
[Sentiment Agent]    ──┐
[Theme Agent]        ──┤
[Audience Agent]     ──┼──► [LLM Council / AI Jury] ──► Verdict
[Competitor Agent]   ──┤         (multi-model panel)     + Confidence
[LinkedIn Agent]     ──┘                                 + Dissent
[Synthetic Audience] ──┘
```

---

## Layer 3 — Delivery

```
┌──────────────────────────────────────────────────────────────┐
│  [Report Agent]                                              │
│   └─ weekly / monthly brand health reports                   │
│   └─ includes LinkedIn engagement section                    │
│   └─ AI Jury verdict summary                                 │
│   └─ client-ready Markdown → PDF                            │
│                                                              │
│  [Dashboard]  (future — Next.js)                            │
│   └─ live brand pulse view                                   │
│   └─ competitor tracker with LinkedIn feed                   │
│   └─ audience heatmaps                                       │
│   └─ AI Jury verdict history                                 │
│                                                              │
│  [Alert Agent]                                               │
│   └─ Telegram for spikes / brand crises                      │
│   └─ Email digests (weekly summary)                          │
│   └─ Slack integration (future)                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Full Data Flow

```
Research Brief / Scheduled Run
           │
           ▼
  Agent Readiness Check ✅
  (sources live? models up? LinkedIn creds valid?)
           │
           ▼
  Orchestration Engine
           │
           ├──► Social Listening Agents
           │     ├─ Reddit (PRAW)
           │     ├─ Twitter/X (xurl)
           │     ├─ LinkedIn (Apify) ← competitor-intel collector
           │     ├─ TikTok
           │     ├─ News
           │     └─ Reviews / SEO
           │         │
           │         ▼
           │    Raw Data Store (PostgreSQL + pgvector)
           │         │
           ├──► Analysis Agents
           │     ├─ Sentiment
           │     ├─ Themes
           │     ├─ Audience
           │     └─ Competitor (LinkedIn benchmarking included)
           │         │
           │         ▼
           │    Brand Awareness Metrics
           │    (incl. LinkedIn presence score)
           │         │
           ├──► Synthetic Audience Agent
           │     └─ simulate reactions → pre-test campaigns
           │         │
           │         ▼
           ├──► LLM Council / AI Jury
           │     └─ multi-juror deliberation → verdict
           │         │
           │         ▼
           └──► Report Agent → Delivery
                 (PDF report / dashboard / Telegram alert)
```

---

## Tech Stack

| Layer | Stack |
|---|---|
| Ingestion — Reddit | Python (PRAW) |
| Ingestion — LinkedIn | Apify (`vdrmota/linkedin-company-posts`) ✅ |
| Ingestion — Twitter/X | xurl CLI / Twitter API v2 |
| Ingestion — Web | BeautifulSoup, Playwright |
| Analysis | AWS Bedrock (Claude 3.5 Sonnet), LangChain, LangGraph |
| Embeddings | sentence-transformers + pgvector |
| LLM Council | Bedrock multi-model, LangGraph multi-agent |
| Database | PostgreSQL 17 |
| Orchestration | Python task queue (Multica-inspired) |
| Synthetic Audience | Bedrock multi-agent (from Synthetic Audience Labs) |
| Reporting | Jinja2 templates → Markdown / PDF |
| Delivery | Telegram Bot, Email (SMTP), future: Next.js dashboard |
| Hosting | AWS (EC2 / Lambda) |

---

## What's Already Built

| Component | Status | Location |
|---|---|---|
| Reddit scraper | ✅ Live | `brand-listener/` |
| LinkedIn collector | ✅ Built | `competitor-intel/collectors/linkedin_collector.py` |
| Competitor categoriser | ✅ Built | `competitor-intel/processors/categoriser.py` |
| Report generator | ✅ Built | `competitor-intel/processors/report_generator.py` |
| Synthetic audience | ✅ MVP | Synthetic Audience Labs (Devpost) |
| Brand positioning scripts | ✅ Built | `brand-listener/ideas/` |

---

## Immediate Next Steps

1. **Generalise LinkedIn collector** → make it accept any brand, not just the 3 hardcoded competitors
2. **Merge brand-listener + competitor-intel** pipelines under one orchestration layer
3. **Build LLM Council prototype** → 3 jurors, simple LangGraph chain, test on existing data
4. **Define task schema** → what a "research brief" looks like as a structured input
5. **Workspace model** → one folder/DB schema per client brand

---

*Architecture drafted: April 2026*
*Repo: https://github.com/NinjaDS/brand-listener*
