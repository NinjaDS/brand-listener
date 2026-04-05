#!/usr/bin/env python3
"""
report_html.py — Generate a rich self-contained HTML report from brand-listener data
https://github.com/NinjaDS/brand-listener

Usage (called internally by brand_listener.py, or standalone):
    from report_html import build_html_report
    html = build_html_report(brand, competitors, topic, mentions, sentiment, audit, country)
    Path("reports/my-report.html").write_text(html)
"""

from datetime import datetime


def _sentiment_color(score) -> str:
    try:
        s = float(score)
        if s > 0.2:  return "#2ecc71"
        if s < -0.2: return "#e74c3c"
        return "#f39c12"
    except:
        return "#95a5a6"


def _badge(text: str, color: str) -> str:
    return (f'<span style="background:{color};color:white;padding:3px 10px;'
            f'border-radius:12px;font-size:0.8em;font-weight:600">{text}</span>')


def build_html_report(brand: str, competitors: list, topic: str,
                      mentions: list, sentiment: dict, audit: dict,
                      country: str = "") -> str:
    date  = datetime.now().strftime("%d %B %Y, %H:%M")
    total = len(mentions)
    score = sentiment.get("sentiment_score", 0) or 0
    overall = sentiment.get("overall_sentiment", "unknown")
    score_color = _sentiment_color(score)
    comp_str = ", ".join(competitors) if competitors else "None"
    country_row = f"<tr><td>Country Focus</td><td><strong>{country}</strong></td></tr>" if country else ""

    # source breakdown
    sources = {}
    for m in mentions:
        src = m["source"].capitalize()
        sources[src] = sources.get(src, 0) + 1

    source_rows = "".join(
        f'<tr><td>{src}</td><td>{cnt}</td><td>'
        f'<div style="background:#3498db;height:12px;border-radius:6px;'
        f'width:{min(int(cnt/max(total,1)*300),300)}px"></div></td></tr>'
        for src, cnt in sources.items()
    )

    # LinkedIn breakdown
    li_mentions = [m for m in mentions if m["source"] == "linkedin"]
    li_types = {}
    for m in li_mentions:
        t = m.get("type", "other").capitalize()
        li_types[t] = li_types.get(t, 0) + 1
    li_badges = " ".join(_badge(f"{t}: {c}", "#0077b5") for t, c in li_types.items())

    # top mentions table rows
    top = sorted(mentions, key=lambda x: x.get("score") or 0, reverse=True)[:20]
    mention_rows = ""
    for m in top:
        src_color = {"reddit": "#ff4500", "hackernews": "#ff6600",
                     "linkedin": "#0077b5", "arxiv": "#b31b1b"}.get(m["source"], "#666")
        title = m["title"][:80] + ("…" if len(m["title"]) > 80 else "")
        mention_rows += f"""
        <tr>
          <td><span style="color:{src_color};font-weight:600">{m['source'].upper()}</span></td>
          <td>{m.get('subreddit','')}</td>
          <td>{m['date']}</td>
          <td><a href="{m['url']}" target="_blank" style="color:#3498db">{title}</a></td>
          <td style="text-align:center">{m.get('score') or '-'}</td>
        </tr>"""

    # themes
    themes_html = " ".join(
        _badge(t, "#8e44ad") for t in sentiment.get("top_themes", [])
    )

    # alerts
    alerts_html = ""
    for a in sentiment.get("alerts", []):
        alerts_html += f'<div class="alert-box">🚨 {a}</div>'

    # gaps & recommendations
    gaps_html = "".join(f"<li>{g}</li>" for g in audit.get("gaps", []))
    recs_html = "".join(f"<li>{r}</li>" for r in audit.get("recommendations", []))

    # sentiment gauge (simple CSS arc)
    gauge_deg = int((float(score) + 1) / 2 * 180)  # 0–180 degrees
    gauge_color = score_color

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Brand Report — {brand}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f0f2f5; color: #2c3e50; }}
    .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
               color: white; padding: 40px 48px; }}
    .header h1 {{ font-size: 2em; margin-bottom: 8px; }}
    .header .meta {{ opacity: 0.7; font-size: 0.9em; margin-top: 8px; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 32px; }}
    .kpi {{ background: white; border-radius: 12px; padding: 20px; text-align: center;
             box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
    .kpi .value {{ font-size: 1.8em; font-weight: 700; color: #2c3e50; }}
    .kpi .label {{ font-size: 0.8em; color: #7f8c8d; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
    .card h2 {{ font-size: 1.1em; margin-bottom: 16px; color: #2c3e50;
                 border-bottom: 2px solid #f0f2f5; padding-bottom: 12px; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
    .three-col {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
    th {{ background: #f8f9fa; padding: 10px 12px; text-align: left;
           font-weight: 600; color: #7f8c8d; text-transform: uppercase;
           font-size: 0.75em; letter-spacing: 0.5px; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #f0f2f5; }}
    tr:hover td {{ background: #fafafa; }}
    .summary-box {{ background: #f8f9fa; border-left: 4px solid #3498db;
                     padding: 16px; border-radius: 0 8px 8px 0; line-height: 1.6; }}
    .alert-box {{ background: #fef0f0; border-left: 4px solid #e74c3c;
                   padding: 12px 16px; border-radius: 0 8px 8px 0;
                   margin-bottom: 8px; color: #c0392b; }}
    .audit-mentioned {{ font-size: 1.4em; font-weight: 700; margin-bottom: 8px; }}
    .gap-list {{ list-style: none; }}
    .gap-list li {{ padding: 8px 0; border-bottom: 1px solid #f0f2f5;
                     padding-left: 20px; position: relative; }}
    .gap-list li::before {{ content: '⚠'; position: absolute; left: 0; }}
    .rec-list {{ list-style: none; }}
    .rec-list li {{ padding: 8px 0; border-bottom: 1px solid #f0f2f5;
                     padding-left: 20px; position: relative; color: #27ae60; }}
    .rec-list li::before {{ content: '✅'; position: absolute; left: 0; }}
    .gauge-wrap {{ text-align: center; padding: 8px 0; }}
    .score-big {{ font-size: 3em; font-weight: 800; color: {gauge_color}; }}
    .ai-sim {{ background: #f8f9fa; border-radius: 8px; padding: 16px;
                font-style: italic; line-height: 1.6; color: #555; font-size: 0.95em; }}
    .footer {{ text-align: center; color: #aaa; font-size: 0.8em; padding: 32px; }}
    .linkedin-badge {{ background: #0077b5; color: white; padding: 2px 8px;
                        border-radius: 4px; font-size: 0.75em; }}
    @media(max-width: 768px) {{
      .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .two-col, .three-col {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>🎧 Brand Listening Report</h1>
  <h2 style="font-size:1.6em;margin-top:4px;opacity:0.9">{brand}</h2>
  <div class="meta">
    Topic: {topic} &nbsp;|&nbsp;
    {f'Country: {country} &nbsp;|&nbsp;' if country else ''}
    Competitors: {comp_str} &nbsp;|&nbsp;
    Generated: {date}
  </div>
</div>

<div class="container">

  <!-- KPI Row -->
  <div class="kpi-grid">
    <div class="kpi">
      <div class="value">{total}</div>
      <div class="label">Total Mentions</div>
    </div>
    <div class="kpi">
      <div class="value" style="color:{score_color}">{overall.upper()}</div>
      <div class="label">Sentiment</div>
    </div>
    <div class="kpi">
      <div class="value" style="color:{score_color}">{score:+.2f}</div>
      <div class="label">Sentiment Score</div>
    </div>
    <div class="kpi">
      <div class="value">{'✅' if audit.get('brand_mentioned') else '❌'}</div>
      <div class="label">AI Visibility</div>
    </div>
    <div class="kpi">
      <div class="value" style="font-size:1.2em">{audit.get('brand_position','?').replace('_',' ').title()}</div>
      <div class="label">AI Position</div>
    </div>
  </div>

  <div class="two-col">

    <!-- Sentiment Summary -->
    <div class="card">
      <h2>💬 Social Listening Summary</h2>
      <div class="gauge-wrap">
        <div class="score-big">{score:+.2f}</div>
        <div style="color:{score_color};font-weight:600;margin-top:4px">{overall.upper()}</div>
        <div style="color:#aaa;font-size:0.8em;margin-top:2px">−1 very negative &nbsp;→&nbsp; +1 very positive</div>
      </div>
      <div style="margin-top:16px">
        <div style="display:flex;gap:16px;justify-content:center;margin-bottom:16px">
          <span>✅ Positive: <strong>{sentiment.get('positive_count',0)}</strong></span>
          <span>😐 Neutral: <strong>{sentiment.get('neutral_count',0)}</strong></span>
          <span>❌ Negative: <strong>{sentiment.get('negative_count',0)}</strong></span>
        </div>
      </div>
      <div class="summary-box">{sentiment.get('summary','No summary available.')}</div>
      {"<div style='margin-top:16px'><strong>Top Themes:</strong><br><br>" + themes_html + "</div>" if themes_html else ""}
      {"<div style='margin-top:16px'>" + alerts_html + "</div>" if alerts_html else ""}
    </div>

    <!-- Mentions by Source -->
    <div class="card">
      <h2>📊 Mentions by Source</h2>
      <table>
        <thead><tr><th>Source</th><th>Count</th><th>Volume</th></tr></thead>
        <tbody>{source_rows}</tbody>
      </table>
      {f'''<div style="margin-top:20px">
        <strong><span class="linkedin-badge">LinkedIn</span> Breakdown</strong><br><br>
        {li_badges or "No LinkedIn mentions found."}
      </div>''' if li_mentions else ""}

      <!-- Meta table -->
      <div style="margin-top:20px">
        <table>
          <thead><tr><th>Parameter</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>Brand</td><td><strong>{brand}</strong></td></tr>
            <tr><td>Topic</td><td>{topic}</td></tr>
            {country_row}
            <tr><td>Competitors</td><td>{comp_str}</td></tr>
            <tr><td>Generated</td><td>{date}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- LLM Brand Audit -->
  <div class="card">
    <h2>🤖 LLM Brand Audit — <em style="font-weight:400;font-size:0.9em">What does AI say about {brand}?</em></h2>
    <p style="color:#7f8c8d;margin-bottom:20px;font-size:0.9em">
      Prompt simulated: <em>"What are the best companies for {topic}?"</em>
    </p>
    <div class="three-col">
      <div>
        <div class="audit-mentioned">{'✅ Mentioned' if audit.get('brand_mentioned') else '❌ Not Mentioned'}</div>
        <div style="color:#7f8c8d;margin-bottom:12px">Position: <strong>{audit.get('brand_position','?')}</strong></div>
        <p><strong>How AI describes {brand}:</strong></p>
        <div class="summary-box" style="margin-top:8px">{audit.get('brand_description','Not mentioned.')}</div>
        <p style="margin-top:16px"><strong>Brand vs Competitors:</strong></p>
        <div class="summary-box" style="margin-top:8px">{audit.get('brand_vs_competitors','N/A')}</div>
      </div>
      <div>
        <p><strong>🕳️ Perception Gaps:</strong></p>
        <ul class="gap-list" style="margin-top:8px">{gaps_html}</ul>
      </div>
      <div>
        <p><strong>✅ Recommendations:</strong></p>
        <ul class="rec-list" style="margin-top:8px">{recs_html}</ul>
      </div>
    </div>
    <div style="margin-top:24px">
      <p style="margin-bottom:8px"><strong>🤖 AI Response Simulation:</strong></p>
      <div class="ai-sim">{audit.get('ai_response_simulation','Not available.')}</div>
    </div>
  </div>

  <!-- Top Mentions Table -->
  <div class="card">
    <h2>📋 Top Mentions</h2>
    <div style="overflow-x:auto">
      <table>
        <thead>
          <tr>
            <th>Source</th><th>Type</th><th>Date</th><th>Title</th><th>Score</th>
          </tr>
        </thead>
        <tbody>{mention_rows}</tbody>
      </table>
    </div>
  </div>

</div>

<div class="footer">
  Generated by <a href="https://github.com/NinjaDS/brand-listener" style="color:#3498db">brand-listener</a>
  — built by <a href="https://linkedin.com/in/perumal-kumaresa-57053a5b/" style="color:#3498db">Kumaresa Perumal</a>
  &nbsp;·&nbsp; Maintained with help from Suresh 🙏
</div>

</body>
</html>"""

    return html
