import streamlit as st
import plotly.graph_objects as go
import time
import random

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Brand Listener — Data Reply",
    page_icon="🎧",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root { --dr-green: #00A651; }
    .stApp { background-color: #0f1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #111827; border-right: 2px solid #00A651; }
    .brand-header { font-size: 2.4rem; font-weight: 800; color: #00A651; margin-bottom: 0; }
    .brand-sub { font-size: 1rem; color: #9ca3af; margin-top: -4px; margin-bottom: 1.5rem; }
    .demo-badge {
        display: inline-block; background: #1a2e1a; border: 1px solid #00A651;
        color: #00A651; border-radius: 20px; padding: 4px 14px;
        font-size: 0.78rem; font-weight: 600; margin-bottom: 1.2rem;
    }
    .mention-card {
        background: #1a1f2e; border-left: 4px solid #00A651;
        border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
    }
    .source-badge {
        display: inline-block; border-radius: 12px; padding: 2px 10px;
        font-size: 0.72rem; font-weight: 700; margin-right: 8px;
    }
    .badge-linkedin { background: #0a66c2; color: white; }
    .badge-reddit   { background: #ff4500; color: white; }
    .badge-news     { background: #00A651; color: white; }
    .rec-card {
        background: #1a2e1a; border: 1px solid #00A651;
        border-radius: 10px; padding: 14px 18px; margin-bottom: 10px;
    }
    .headline-row {
        background: #1a1f2e; border-radius: 8px; padding: 12px 16px;
        margin-bottom: 8px; display: flex; align-items: center;
    }
    .sent-pos { color: #00A651; font-weight: 700; font-size: 0.8rem; }
    .sent-neg { color: #ef4444; font-weight: 700; font-size: 0.8rem; }
    .sent-neu { color: #9ca3af; font-weight: 700; font-size: 0.8rem; }
    footer-text { color: #4b5563; font-size: 0.8rem; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎧 Brand Listener")
    st.markdown("**AI-powered social listening + LLM brand audit**")
    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown("1. Enter your brand details\n2. Click Run Analysis\n3. Get sentiment, AI audit & news insights")
    st.markdown("---")
    st.markdown('<div class="demo-badge">🔒 Demo Mode</div>', unsafe_allow_html=True)
    st.caption("Connect AWS Bedrock for live analysis with real data.")
    st.markdown("---")
    st.markdown("**Powered by**")
    st.markdown("🟢 **Data Reply** · AWS Bedrock · Claude")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="brand-header">🎧 Brand Listener</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">AI-powered social listening + LLM brand audit · by Data Reply</div>', unsafe_allow_html=True)
st.markdown('<div class="demo-badge">🔒 Running in Demo Mode — connect AWS Bedrock for live analysis</div>', unsafe_allow_html=True)

# ── Input form ─────────────────────────────────────────────────────────────────
with st.form("brand_form"):
    c1, c2 = st.columns(2)
    with c1:
        brand = st.text_input("Brand Name", placeholder="e.g. Data Reply")
        topic = st.text_input("Topic / Industry", placeholder="e.g. AI consulting enterprise UK")
    with c2:
        competitors = st.text_input("Competitors (comma separated)", placeholder="e.g. Accenture, Deloitte, Capgemini")
        region = st.selectbox("Region", ["UK", "US", "Global", "Europe", "APAC"])
    submitted = st.form_submit_button("🚀 Run Analysis", use_container_width=True)

# ── Results ────────────────────────────────────────────────────────────────────
if submitted and brand:
    comp_list = [c.strip() for c in competitors.split(",") if c.strip()] or ["Competitor A", "Competitor B"]

    with st.spinner(f"Analysing brand presence for **{brand}**... pulling social data, running LLM audit..."):
        time.sleep(2.5)

    st.success(f"✅ Analysis complete for **{brand}** across {region} · {len(comp_list)} competitors benchmarked")

    tab1, tab2, tab3 = st.tabs(["📊 Social Sentiment", "🤖 AI Audit", "📰 News & Trends"])

    # ── TAB 1: Social Sentiment ────────────────────────────────────────────────
    with tab1:
        st.markdown(f"### Sentiment breakdown for **{brand}**")
        c1, c2 = st.columns([1, 1.4])
        with c1:
            fig_pie = go.Figure(go.Pie(
                labels=["Positive", "Neutral", "Negative"],
                values=[58, 28, 14],
                hole=0.5,
                marker_colors=["#00A651", "#374151", "#ef4444"],
                textfont_size=13,
            ))
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e0e0", showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=20, b=20),
                annotations=[dict(text="58%<br>Positive", x=0.5, y=0.5, font_size=14, font_color="#00A651", showarrow=False)]
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.metric("Total Mentions (7 days)", "1,247", "+18%")
            st.metric("Avg. Sentiment Score", "0.62 / 1.0", "+0.08")

        with c2:
            st.markdown("**Top Mentions**")
            mentions = [
                ("linkedin", f"{brand} just launched a new AI-powered consulting framework. Impressive work from their team.", "LinkedIn", "+0.82"),
                ("reddit",   f"Has anyone worked with {brand}? Their {topic} offering seems solid.", "Reddit", "+0.61"),
                ("news",     f"{brand} wins major AI transformation contract in {region}.", "News", "+0.91"),
                ("linkedin", f"Compared {brand} vs {comp_list[0]} for our AI project — {brand} had better domain depth.", "LinkedIn", "+0.74"),
                ("reddit",   f"Anyone else find {brand}'s pricing steep? Curious how they compare to {comp_list[0] if comp_list else 'others'}.", "Reddit", "-0.38"),
            ]
            badge_map = {"linkedin": "badge-linkedin", "reddit": "badge-reddit", "news": "badge-news"}
            for source, text, label, score in mentions:
                colour = "#00A651" if float(score) > 0 else "#ef4444"
                st.markdown(f"""
                <div class="mention-card">
                    <span class="source-badge {badge_map[source]}">{label}</span>
                    <span style="font-size:0.78rem;color:{colour};font-weight:700;">{score}</span>
                    <p style="margin:6px 0 0 0;font-size:0.9rem;color:#d1d5db;">{text}</p>
                </div>""", unsafe_allow_html=True)

    # ── TAB 2: AI Audit ────────────────────────────────────────────────────────
    with tab2:
        st.markdown(f"### AI Visibility Score — *how AI models perceive {brand}*")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=71,
                title={"text": "AI Visibility Score", "font": {"color": "#e0e0e0"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#9ca3af"},
                    "bar": {"color": "#00A651"},
                    "bgcolor": "#1a1f2e",
                    "steps": [
                        {"range": [0, 40], "color": "#2d1a1a"},
                        {"range": [40, 70], "color": "#2d2a1a"},
                        {"range": [70, 100], "color": "#1a2d1a"},
                    ],
                    "threshold": {"line": {"color": "#00A651", "width": 3}, "thickness": 0.75, "value": 71},
                },
                number={"font": {"color": "#00A651", "size": 52}},
            ))
            fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e0e0e0", height=280, margin=dict(t=20, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption("71/100 — Strong AI visibility. Above industry average.")

        with c2:
            st.markdown("**What Claude says about your brand vs competitors:**")
            st.markdown(f"""
            <div style="background:#1a1f2e;border-radius:10px;padding:16px 20px;margin-bottom:12px;">
                <p style="color:#00A651;font-weight:700;margin-bottom:6px;">🧠 Claude on {brand}</p>
                <p style="color:#d1d5db;font-size:0.92rem;margin:0;">"{brand} is widely recognised as a specialist {topic} firm with strong technical depth.
                In the {region} market, they are frequently cited in discussions about enterprise AI transformation.
                Their positioning is differentiated by domain expertise rather than scale."</p>
            </div>
            <div style="background:#1a1f2e;border-radius:10px;padding:16px 20px;">
                <p style="color:#9ca3af;font-weight:700;margin-bottom:6px;">⚔️ vs {comp_list[0] if comp_list else 'Competitor'}</p>
                <p style="color:#d1d5db;font-size:0.92rem;margin:0;">"{comp_list[0] if comp_list else 'Competitor'} has broader market awareness but {brand} scores higher on
                specialisation and AI credibility in the {topic} segment."</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("**Recommendations to improve AI visibility:**")
        recs = [
            f"📝 Publish more thought leadership on **{topic}** — Claude surfaces content-rich brands more frequently",
            f"🔗 Increase mentions on high-authority domains (HBR, Wired, TechCrunch) to improve AI training signal",
            f"🤝 Build co-citations with **{comp_list[0] if comp_list else 'industry leaders'}** to strengthen associative brand positioning in AI models",
        ]
        for r in recs:
            st.markdown(f'<div class="rec-card">{r}</div>', unsafe_allow_html=True)

    # ── TAB 3: News & Trends ───────────────────────────────────────────────────
    with tab3:
        st.markdown(f"### News coverage — **{brand}** · last 7 days")
        headlines = [
            (f"{brand} Announces Strategic AI Partnership for {region} Market", "positive", "FT.com", "2h ago"),
            (f"How {brand} is Redefining {topic.title()} with Generative AI", "positive", "Forbes", "1d ago"),
            (f"{comp_list[0] if comp_list else 'Competitor'} Challenges {brand} in New {region} Tender", "neutral", "CityAM", "2d ago"),
            (f"{brand} Faces Scrutiny Over AI Ethics Framework, Analysts Say", "negative", "Guardian", "3d ago"),
            (f"{brand} Reports Record Growth in AI Practice Division", "positive", "Reuters", "4d ago"),
        ]
        sent_class = {"positive": "sent-pos", "negative": "sent-neg", "neutral": "sent-neu"}
        sent_label = {"positive": "▲ Positive", "negative": "▼ Negative", "neutral": "● Neutral"}
        for headline, sentiment, source, age in headlines:
            st.markdown(f"""
            <div class="headline-row">
                <div style="flex:1">
                    <span style="font-size:0.93rem;color:#e0e0e0;">{headline}</span>
                    <span style="font-size:0.78rem;color:#6b7280;margin-left:10px;">{source} · {age}</span>
                </div>
                <span class="{sent_class[sentiment]}" style="margin-left:12px;">{sent_label[sentiment]}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("**Week-over-week sentiment trend**")
        weeks = ["W-6", "W-5", "W-4", "W-3", "W-2", "Last Week", "This Week"]
        scores = [0.51, 0.54, 0.49, 0.58, 0.61, 0.59, 0.63]
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=weeks, y=scores, mode="lines+markers",
            line=dict(color="#00A651", width=3),
            marker=dict(size=8, color="#00A651"),
            fill="tozeroy", fillcolor="rgba(0,166,81,0.1)",
            name="Sentiment Score"
        ))
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0", yaxis=dict(range=[0, 1], gridcolor="#1f2937"),
            xaxis=dict(gridcolor="#1f2937"), margin=dict(t=10, b=10), height=250
        )
        st.plotly_chart(fig_line, use_container_width=True)

elif submitted and not brand:
    st.warning("Please enter a brand name to run the analysis.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#4b5563;font-size:0.82rem;">Powered by <strong style="color:#00A651">Data Reply</strong> · Brand Listener v1.0 · Built with AWS Bedrock & Claude</p>',
    unsafe_allow_html=True
)
