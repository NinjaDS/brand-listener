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
Ask Claude to simulate what an AI assistant would say about your brand when someone asks *"What are the best companies for [topic]?"*

- Is your brand mentioned at all?
- How is it described vs competitors?
- What are the perception gaps?
- What should you do to improve AI visibility?

This matters because **AI assistants are becoming the new search engine**. If ChatGPT or Claude don't mention your brand, you're invisible to a growing slice of buyers.

---

## Requirements

- Python 3.10+
- AWS credentials with Bedrock access (Claude Sonnet via `~/.aws/credentials`)
- No other paid APIs, no GPU

---

## Usage

```bash
# Basic — just a brand
python3 brand_listener.py --brand "Data Reply" --topic "AI consulting"

# With competitors
python3 brand_listener.py \
  --brand "Data Reply" \
  --competitors "Accenture,Deloitte,McKinsey" \
  --topic "AI consulting enterprise"

# For your startup
python3 brand_listener.py \
  --brand "Synthetic Audience Labs" \
  --competitors "Nielsen,YouGov,Qualtrics" \
  --topic "synthetic audience marketing research"
```

Reports are saved to `reports/YYYY-MM-DD-brand-name.md`

---

## Architecture

```
brand_listener.py
├── scrape_reddit()        → Reddit public JSON API (no auth)
├── scrape_hackernews()    → HN Algolia API (no auth)
├── scrape_arxiv()         → arXiv API (no auth)
├── analyse_sentiment()    → Claude via AWS Bedrock
├── llm_brand_audit()      → Claude simulates AI brand perception
└── build_report()         → Markdown report with all findings
```

---

## Sample Output

```
🎧 Brand Listener — Data Reply
   Topic: AI consulting enterprise

🔍 Scraping mentions...
   Reddit: 12 posts
   HackerNews: 8 posts
   arXiv: 10 papers
   Total: 30 mentions

🧠 Analysing sentiment (Claude)...
   Overall: mixed (score: 0.12)

🤖 Running LLM brand audit (Claude)...
   Brand ✅ mentioned | Position: top3

✅ Report saved: reports/2026-04-04-data-reply.md
```

---

## Roadmap

- [ ] Add Twitter/X scraping (via xurl)
- [ ] Add LinkedIn mentions
- [ ] Scheduled weekly reports via cron
- [ ] Slack/Telegram alerts for sentiment spikes
- [ ] Multi-LLM audit (ChatGPT + Gemini + Claude comparison)
- [ ] Dashboard UI

---

## References

- [Auditing Preferences for Brands in LLMs](https://arxiv.org/abs/2603.18300) — March 2026
- [SocialED — Social Event Detection](https://github.com/RingBDStack/SocialED)
- [AI Watchman — LLM Content Monitoring](https://arxiv.org/abs/2510.01255)

---

*Built by [Kumaresa Perumal](https://linkedin.com/in/perumal-kumaresa-57053a5b/) · Maintained with help from Suresh 🙏*
