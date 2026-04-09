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

### 🔍 Data Sources
- **Reddit** — real community comments across curly hair subreddits (r/curlyhair, r/CurlyHairCare, r/wavyhair, r/NaturalHair, r/finehair, r/curlygirl)
- **LinkedIn** — posts, articles, profiles mentioning your brand (via Google Search)
- **News** — Google News RSS for the freshest press coverage
- **Meta & TikTok** — via DuckDuckGo scraping

### 🤖 LLM Brand Audit
Asks Claude what AI models "think" about your brand vs competitors — surfacing blind spots, AI visibility scores, and recommendations to improve how AI represents your brand.

### 🗺️ Brand Positioning Analysis
Full competitive positioning suite including:
- Brand association inventory (what audiences actually associate with the brand)
- Attribute scorecard vs competitors (radar chart)
- Competitive proximity matrix + substitution risk
- Perceptual map (price × credibility axes)
- Whitespace opportunity assessment
- Positioning recommendation

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install boto3 matplotlib pandas
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

### 4. Run as daemon (automated weekly)
```bash
python3 main.py --schedule --daemon
# Fires every Monday at 08:00 by default
```

---

## 📁 Project Structure

```
brand-listener/
├── main.py                          # Single entrypoint
├── watchlist.example.json           # Copy to watchlist.json and edit
├── core/
│   ├── brand_listener.py            # Core engine: scraping + sentiment + LLM audit
│   ├── report_html.py               # HTML report generator
│   ├── dashboard.py                 # Streamlit dashboard
│   ├── reddit_analyser.py           # Reddit sentiment + age/topic analysis
│   └── reddit_report_builder.py     # Reddit audience report generator
├── scrapers/
│   ├── linkedin_scraper.py          # LinkedIn posts + articles
│   ├── meta_scraper.py              # Facebook + Instagram
│   ├── tiktok_scraper.py            # TikTok videos + creators
│   ├── reddit_scraper.py            # Reddit brand mention scraper
│   └── reddit_targeted_scraper.py   # Targeted subreddit scraper
├── ideas/                           # Working scripts and analysis tools
│   ├── curlsmith_brand_positioning.py   # Positioning charts + data generator
│   └── curlsmith_positioning_report.py  # Positioning MD report builder
├── scheduler/
│   └── scheduler.py                 # Automated scheduler + adaptive loop
├── docs/
│   └── ARCHITECTURE.md              # Full system architecture diagram
└── reports/
    └── curlsmith/
        ├── reddit_audience_report.md        # Audience intelligence report
        ├── brand_positioning_report.md      # Full brand positioning report
        ├── reddit_comments_raw.json         # 487 raw Reddit comments
        ├── positioning_data.json            # Structured positioning data
        └── charts/
            ├── perceptual_map.png           # Price × credibility perceptual map
            └── attribute_scorecard.png      # Radar chart vs competitors
```

---

## 📊 Latest Reports — Curlsmith (April 2026)

| Report | Link |
|--------|------|
| 👥 Audience Intelligence | [reddit_audience_report.md](reports/curlsmith/reddit_audience_report.md) |
| 🗺️ Brand Positioning | [brand_positioning_report.md](reports/curlsmith/brand_positioning_report.md) |
| 📊 Perceptual Map | [perceptual_map.png](reports/curlsmith/charts/perceptual_map.png) |
| 📊 Attribute Scorecard | [attribute_scorecard.png](reports/curlsmith/charts/attribute_scorecard.png) |

**Key findings (487 Reddit comments analysed):**
- 🥇 Core audience: women in their **20s–30s**; secondary: parents, postpartum women
- 💧 Strongest association: **Moisture & Hydration** (37%), not curl definition
- 🥊 Closest competitor: **Innersense** (highest substitution risk post-acquisition)
- ⚠️ Main risk: **formula change concern** after Helen of Troy acquisition (2022)
- 🎯 Whitespace: postpartum hair, kids/mixed texture, men with curls — all unclaimed
- 💡 Recommended positioning: *"The curl expert that works for real life — not just salon days"*

---

## ⚙️ Requirements

- Python 3.11+
- AWS account with Bedrock access (Claude Sonnet via `us-west-2`)
- No GPU required
- No paid third-party APIs required for basic use

---

*Built by [Kumaresa Perumal](https://github.com/NinjaDS) · Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch)*
