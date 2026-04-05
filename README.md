# 🎧 Brand Listener

> AI-powered social listening + LLM brand audit tool — no GPU required.
> Track what people **and** AI models say about your brand. Runs automatically on a schedule.

[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![AWS Bedrock](https://img.shields.io/badge/AI-AWS%20Bedrock-orange)](https://aws.amazon.com/bedrock/)
[![No GPU](https://img.shields.io/badge/GPU-not%20required-green)]()

---

## ✨ Key Features

### 🔄 Automated Weekly Reports
Set it once. Every Monday (or your chosen schedule), Brand Listener runs automatically — pulling fresh data, generating reports, and emailing them to you. No manual intervention needed.

### 🧠 Adaptive Search (Karpathy-inspired)
Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch), the tool **learns from previous runs**. Instead of static queries, it blends emerging themes from last week's report into this week's search — chasing the conversations that matter, not just keyword matches.

### 📈 Trend Detection & Alerts
Week-over-week sentiment comparison. If your brand's sentiment drops significantly, you get an immediate alert — before it becomes a crisis.

### 🔍 Two Data Sources
- **LinkedIn** — posts, articles, profiles mentioning your brand (via Google Search)
- **News** — Google News RSS for the freshest press coverage

Plus Reddit and HackerNews for community and developer sentiment.

### 🤖 LLM Brand Audit
Asks Claude what AI models "think" about your brand vs competitors — surfacing blind spots, AI visibility scores, and recommendations to improve how AI represents your brand.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install boto3
# AWS credentials must be configured for Bedrock access (us-west-2)
```

### 2. Configure your watchlist
```bash
cp watchlist.example.json watchlist.json
# Edit watchlist.json — add your brands, competitors, schedule, and email
```

### 3. Run once (manual)
```bash
python3 main.py --brand "Adidas" --competitors "Nike,Puma" --topic "sportswear"
```

### 4. Run all brands from watchlist
```bash
python3 main.py --schedule --run-now
```

### 5. Run as daemon (automated weekly)
```bash
python3 main.py --schedule --daemon
# Fires every Monday at 08:00 by default
# Or add to cron:  0 8 * * 1  python3 /path/to/main.py --schedule --run-now
```

---

## 📋 watchlist.json Configuration

```json
{
  "watchlist": [
    {
      "brand": "Your Brand",
      "competitors": ["Competitor A", "Competitor B"],
      "topic": "your industry",
      "region": "global",
      "country": "",
      "subsidiaries": []
    }
  ],
  "schedule": {
    "frequency": "weekly",
    "day": "monday",
    "hour": 8
  },
  "distribution": {
    "email": "you@email.com",
    "save_reports": true
  },
  "adaptive": {
    "enabled": true,
    "sentiment_alert_threshold": -0.3
  }
}
```

**Region options:** `global` | `european` | `italian` | `us` | `uk` | `apac`

**Email setup** (optional): Set env vars `SMTP_USER`, `SMTP_PASS`, `SMTP_HOST` (default: Gmail)

---

## 📊 What's in a Report

Each report includes:

- **Social Listening Summary** — overall sentiment, score, source breakdown
- **Top Themes** — what people are actually talking about
- **Alerts** — PR risks, negative trends
- **LLM Brand Audit** — AI visibility scores vs competitors, gaps, recommendations
- **Top Mentions** — highest-scoring posts with links

Reports saved as `.md` and `.html` in the `reports/` folder.

---

## 🧠 Adaptive Loop (How It Works)

```
Week 1: Search "Adidas sportswear"
        → Top themes: ["sustainability", "Yeezy controversy"]

Week 2: Search "Adidas sportswear sustainability Yeezy controversy"  ← adapted!
        → Chases the conversations that are gaining traction

Week 3: Sentiment drops -0.4 → ALERT fired automatically
```

This is the core insight from Karpathy's autoresearch: **static queries go stale**. The tool should evolve its understanding week by week.

---

## 📁 Project Structure

```
brand-listener/
├── main.py                    # ← Single entrypoint (start here)
├── watchlist.example.json     # ← Copy this to watchlist.json and edit
├── core/
│   ├── brand_listener.py      # Core engine: scraping + sentiment + LLM audit
│   ├── report_html.py         # HTML report generator
│   └── dashboard.py           # Streamlit dashboard (interactive exploration)
├── scrapers/
│   ├── linkedin_scraper.py    # LinkedIn posts + articles (Google Search)
│   ├── meta_scraper.py        # Facebook + Instagram (DuckDuckGo)
│   └── tiktok_scraper.py      # TikTok videos + creators (DuckDuckGo)
├── scheduler/
│   └── scheduler.py           # Automated scheduler + adaptive loop + trend detection
├── docs/
│   └── ARCHITECTURE.md        # Full system architecture diagram
└── reports/                   # Generated reports (auto-created)
    ├── history.json           # Run history for adaptive loop + trend tracking
    ├── YYYY-MM-DD-brand.md    # Markdown reports
    └── YYYY-MM-DD-brand.html  # HTML reports
```

📄 [View full architecture diagram](docs/ARCHITECTURE.md)

---

## ⚙️ Requirements

- Python 3.11+
- AWS account with Bedrock access (Claude Sonnet via `us-west-2`)
- No GPU required
- No paid third-party APIs required for basic use

> **Note on Google rate limits:** LinkedIn, Meta, and TikTok scrapers use Google Search.
> If you run reports frequently, set `GOOGLE_CSE_ID` + `GOOGLE_API_KEY` env vars
> to use the [Google Custom Search API](https://developers.google.com/custom-search/v1/overview)
> (100 free queries/day). For weekly scheduled runs, the free scraper works fine.

---

*Built by [Kumaresa Perumal](https://github.com/NinjaDS) · Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch)*
