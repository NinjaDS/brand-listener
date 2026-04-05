#!/usr/bin/env python3
"""
dashboard.py — Streamlit dashboard for brand-listener
https://github.com/NinjaDS/brand-listener

Run:
    streamlit run dashboard.py

Or with a specific brand pre-loaded:
    streamlit run dashboard.py -- --brand "Accenture" --topic "IT consulting"
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# add parent dir so we can import brand_listener
sys.path.insert(0, str(Path(__file__).parent))
from brand_listener import run as run_analysis
from linkedin_scraper import scrape_linkedin

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Brand Listener 🎧",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎧 Brand Listener")
    st.caption("AI-powered social listening + LLM brand audit")
    st.divider()

    brand = st.text_input("Brand name", value="", placeholder="e.g. Accenture, Monzo, Tesla")
    competitors_raw = st.text_input(
        "Competitors (comma-separated)",
        value="Accenture, Deloitte, KPMG",
        placeholder="e.g. Accenture, Deloitte"
    )
    topic = st.text_input("Topic / industry", value="AI consulting enterprise")
    include_linkedin = st.toggle("Include LinkedIn mentions", value=True)

    run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

    st.divider()
    st.caption("Powered by AWS Bedrock (Claude)")
    st.caption("[github.com/brand-listener](https://github.com/NinjaDS/brand-listener)")

# ── Load existing reports ────────────────────────────────────────────────────
reports_dir = Path(__file__).parent / "reports"
reports_dir.mkdir(exist_ok=True)
existing_reports = sorted(reports_dir.glob("*.md"), reverse=True)

# ── Main area ─────────────────────────────────────────────────────────────────
st.title(f"🎧 Brand Listener Dashboard")

if not run_btn and not existing_reports:
    st.info("👈 Enter your brand details in the sidebar and click **Run Analysis** to get started.")
    st.stop()

# ── Run analysis ─────────────────────────────────────────────────────────────
if run_btn:
    competitors = [c.strip() for c in competitors_raw.split(",") if c.strip()]

    with st.status("Running brand analysis…", expanded=True) as status:
        st.write("🔍 Scraping Reddit, HackerNews, arXiv…")

        # patch run() to capture data before writing report
        import brand_listener as bl
        from brand_listener import (
            scrape_reddit, scrape_hackernews, scrape_arxiv,
            analyse_sentiment, llm_brand_audit, build_report
        )

        mentions = []
        mentions += scrape_reddit(brand)
        mentions += scrape_hackernews(brand)
        mentions += scrape_arxiv(brand, topic)

        if include_linkedin:
            st.write("💼 Scraping LinkedIn mentions…")
            mentions += scrape_linkedin(brand)

        st.write(f"   Found **{len(mentions)}** total mentions")

        st.write("🧠 Analysing sentiment with Claude…")
        sentiment = analyse_sentiment(brand, mentions)

        st.write("🤖 Running LLM brand audit…")
        audit = llm_brand_audit(brand, competitors, topic)

        st.write("📝 Saving report…")
        ts = datetime.now().strftime("%Y-%m-%d")
        safe = brand.lower().replace(" ", "-")
        out  = reports_dir / f"{ts}-{safe}.md"
        report_md = build_report(brand, competitors, topic, mentions, sentiment, audit)
        out.write_text(report_md, encoding="utf-8")

        status.update(label="✅ Analysis complete!", state="complete")

    # store in session state
    st.session_state["brand"]     = brand
    st.session_state["mentions"]  = mentions
    st.session_state["sentiment"] = sentiment
    st.session_state["audit"]     = audit
    st.session_state["report_md"] = report_md
    st.session_state["topic"]     = topic
    existing_reports = sorted(reports_dir.glob("*.md"), reverse=True)

# ── Display results ───────────────────────────────────────────────────────────
if "sentiment" in st.session_state:
    sentiment = st.session_state["sentiment"]
    audit     = st.session_state["audit"]
    mentions  = st.session_state["mentions"]
    brand_    = st.session_state["brand"]
    topic_    = st.session_state["topic"]

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    score = sentiment.get("sentiment_score", 0) or 0
    overall = sentiment.get("overall_sentiment", "?").upper()
    emoji = "😊" if score > 0.2 else "😐" if score > -0.2 else "😟"

    k1.metric("Total Mentions",  len(mentions))
    k2.metric("Sentiment",       f"{emoji} {overall}")
    k3.metric("Sentiment Score", f"{score:+.2f}")
    k4.metric("AI Visibility",   "✅ Yes" if audit.get("brand_mentioned") else "❌ No")
    k5.metric("AI Position",     audit.get("brand_position", "?").replace("_", " ").title())

    st.divider()

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1])

    with col_left:
        # Mentions by source pie
        source_counts = {}
        for m in mentions:
            source_counts[m["source"].capitalize()] = source_counts.get(m["source"].capitalize(), 0) + 1
        fig_pie = px.pie(
            values=list(source_counts.values()),
            names=list(source_counts.keys()),
            title="📊 Mentions by Source",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        # Sentiment breakdown bar
        pos = sentiment.get("positive_count", 0) or 0
        neg = sentiment.get("negative_count", 0) or 0
        neu = sentiment.get("neutral_count",  0) or 0
        fig_bar = go.Figure(data=[
            go.Bar(name="Positive", x=["Sentiment"], y=[pos],  marker_color="#2ecc71"),
            go.Bar(name="Neutral",  x=["Sentiment"], y=[neu],  marker_color="#95a5a6"),
            go.Bar(name="Negative", x=["Sentiment"], y=[neg],  marker_color="#e74c3c"),
        ])
        fig_bar.update_layout(
            barmode="group", title="😊 Sentiment Breakdown",
            margin=dict(t=40, b=0, l=0, r=0), showlegend=True
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ── Social Listening summary ──────────────────────────────────────────────
    st.subheader("💬 What People Are Saying")
    st.info(sentiment.get("summary", "No summary available."))

    themes = sentiment.get("top_themes", [])
    if themes:
        st.write("**Top Themes:**  " + "   ".join([f"`{t}`" for t in themes]))

    alerts = sentiment.get("alerts", [])
    if alerts:
        st.subheader("⚠️ Alerts")
        for a in alerts:
            st.error(f"🚨 {a}")

    # ── LinkedIn section ──────────────────────────────────────────────────────
    li_mentions = [m for m in mentions if m["source"] == "linkedin"]
    if li_mentions:
        st.divider()
        st.subheader(f"💼 LinkedIn Mentions ({len(li_mentions)})")

        li_types = {}
        for m in li_mentions:
            li_types[m.get("type", "other")] = li_types.get(m.get("type", "other"), 0) + 1

        t_cols = st.columns(len(li_types))
        for i, (k, v) in enumerate(li_types.items()):
            t_cols[i].metric(k.capitalize(), v)

        with st.expander("View LinkedIn mentions"):
            for m in li_mentions[:10]:
                st.markdown(f"**[{m['title']}]({m['url']})**  \n{m['text'][:200]}")
                st.caption(f"{m.get('type', '').capitalize()} · {m['date']}")
                st.divider()

    # ── LLM Brand Audit ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("🤖 LLM Brand Audit")
    st.caption(f"What does Claude say about {brand_} when asked: *\"What are the best companies for {topic_}?\"*")

    a1, a2 = st.columns([1, 1])
    with a1:
        st.markdown(f"**Brand Mentioned:** {'✅ Yes' if audit.get('brand_mentioned') else '❌ No'}")
        st.markdown(f"**AI Position:** `{audit.get('brand_position', '?')}`")
        st.markdown(f"**How AI describes {brand_}:**")
        st.info(audit.get("brand_description", "Not mentioned by AI."))

        st.markdown("**AI Response Simulation:**")
        with st.expander("See what AI says"):
            st.write(audit.get("ai_response_simulation", "Not available."))

    with a2:
        gaps = audit.get("gaps", [])
        recs = audit.get("recommendations", [])

        st.markdown("**🕳️ Perception Gaps:**")
        for g in gaps:
            st.warning(f"• {g}")

        st.markdown("**✅ Recommendations:**")
        for r in recs:
            st.success(f"• {r}")

    st.markdown(f"**Brand vs Competitors:**")
    st.write(audit.get("brand_vs_competitors", "No comparison available."))

    # ── Top Mentions table ────────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Top Mentions")
    top = sorted(mentions, key=lambda x: x.get("score") or 0, reverse=True)[:20]
    rows = []
    for m in top:
        rows.append({
            "Source":  m["source"].capitalize(),
            "Type":    m.get("type", m.get("subreddit", "")),
            "Date":    m["date"],
            "Title":   m["title"][:80],
            "Score":   m.get("score") or 0,
            "URL":     m["url"],
        })
    st.dataframe(rows, use_container_width=True)

    # ── Download report ───────────────────────────────────────────────────────
    st.divider()
    st.download_button(
        label="📥 Download Full Report (Markdown)",
        data=st.session_state.get("report_md", ""),
        file_name=f"brand-report-{brand_.lower().replace(' ','-')}.md",
        mime="text/markdown",
    )

elif existing_reports:
    st.subheader("📁 Previous Reports")
    for r in existing_reports[:10]:
        with st.expander(f"📄 {r.name}"):
            st.markdown(r.read_text(encoding="utf-8"))
