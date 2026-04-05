# Brand Listener 🎧

> AI-powered social listening + LLM brand audit tool — no GPU, no paid APIs required.

## What It Does

Two things most tools don't combine:

### 1. Social Listening
Scrapes Reddit, HackerNews, and arXiv for brand mentions — then uses Claude (AWS Bedrock) to:
- Analyse overall sentiment (score from −1 to +1)
- Surface top themes in the conversation
- Flag urgent PR risks or negative trends

### 2. LLM Brand Audit *(the new frontier)*
Simulates what an AI assistant would say about your brand when someone asks *"What are the best companies for [topic]?"*

- Is your brand mentioned at all?
- How is it described vs competitors?
- What are the AI visibility scores for each brand?
- What are the perception gaps, and how do you fix them?

This matters because **AI assistants are becoming the new search engine**. If ChatGPT or Claude don't mention your brand, you're invisible to a growing slice of buyers.

---

## Requirements

- Python 3.10+
- AWS credentials with Bedrock access (Claude Sonnet via `~/.aws/credentials`)
- No other paid APIs, no GPU

---

## Usage

```bash
# Any single brand
python3 brand_listener.py --brand "Accenture" --topic "IT consulting" --region global

# Brand with subsidiaries (group model)
python3 brand_listener.py \
  --brand "Your Group" \
  --subsidiaries "Sub Brand A,Sub Brand B,Sub Brand C" \
  --competitors "Competitor1,Competitor2,Competitor3" \
  --topic "your industry topic" \
  --region european

# Startup vs big players
python3 brand_listener.py \
  --brand "Monzo" \
  --competitors "HSBC,Barclays,Starling,Revolut" \
  --topic "digital banking UK" \
  --region uk

# With country + region context
python3 brand_listener.py \
  --brand "Your Brand" \
  --competitors "CompA,CompB" \
  --topic "enterprise software" \
  --country "Germany" \
  --region european
```

Reports are saved to `reports/YYYY-MM-DD-brand-name.md` and `reports/YYYY-MM-DD-brand-name.html`

---

## CLI Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--brand` | Brand name to monitor (required) | `"Accenture"` |
| `--competitors` | Comma-separated competitor names | `"Deloitte,KPMG"` |
| `--topic` | Industry/topic context | `"IT consulting"` |
| `--country` | Country focus for scraping | `"Italy"` |
| `--region` | Audience context for LLM audit | `italian` |
| `--subsidiaries` | Sub-brands belonging to the same group | `"Brand A,Brand B"` |

**Region options:** `global` · `european` · `italian` · `us` · `uk` · `apac`

---

## Architecture

```
brand_listener.py      — main tool (scraping, sentiment, LLM audit, reports)
linkedin_scraper.py    — LinkedIn public mention scraper via Google
report_html.py         — self-contained HTML report generator
dashboard.py           — Streamlit interactive dashboard
```

```
brand_listener.py
├── scrape_reddit()        → Reddit public JSON API (no auth)
├── scrape_hackernews()    → HN Algolia API (no auth)
├── scrape_arxiv()         → arXiv API (no auth)
├── scrape_linkedin()      → via linkedin_scraper.py
├── analyse_sentiment()    → Claude via AWS Bedrock
├── llm_brand_audit()      → Claude simulates AI brand perception
└── build_report()         → Markdown + HTML reports
```

---

## Dashboard

```bash
streamlit run dashboard.py
```

Opens at **http://localhost:8501** — interactive UI with charts, LinkedIn breakdown, LLM audit panel, and report download.

---

## Sample Output

```
🎧 Brand Listener — Accenture
   Topic: IT consulting
   Region context: global

🔍 Scraping mentions...
   Reddit: 30 posts
   HackerNews: 28 posts
   arXiv: 10 papers
   Total: 68 mentions

🧠 Analysing sentiment (Claude)...
   Overall: positive (score: 0.42)

🤖 Running LLM brand audit (Claude)...
   Brand ✅ mentioned | Position: top3

✅ Markdown report saved: reports/2026-04-05-accenture.md
✅ HTML report saved:     reports/2026-04-05-accenture.html
```

---

## Roadmap

- [ ] Twitter/X scraping (via xurl)
- [ ] Scheduled weekly reports via cron
- [ ] Slack/Telegram alerts for sentiment spikes
- [ ] Multi-LLM audit (ChatGPT + Gemini + Claude comparison)
- [ ] Historical trend tracking

---

## References

- [Auditing Preferences for Brands in LLMs](https://arxiv.org/abs/2603.18300) — March 2026
- [SocialED — Social Event Detection](https://github.com/RingBDStack/SocialED)
- [AI Watchman — LLM Content Monitoring](https://arxiv.org/abs/2510.01255)

---

*MIT License — contributions welcome*
