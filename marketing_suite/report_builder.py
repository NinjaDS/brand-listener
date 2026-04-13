"""
Report builder for the Brand Ops Marketing Suite.
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def build_report(
    brand_config: Dict[str, Any],
    linkedin_posts: List[Dict],
    reddit_posts: List[Dict],
    awareness: Dict[str, Any],
    council_result: Dict[str, Any],
    workspace: Any,  # Path or str
) -> str:
    brand_name = brand_config.get("brand", "Unknown Brand")
    competitors = brand_config.get("competitors", [])
    topic = brand_config.get("topic", "")
    timestamp = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    ts_file = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

    lines: List[str] = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines += [
        f"# 🏷️ Brand Intelligence Report: {brand_name}",
        f"**Generated:** {timestamp}  ",
        f"**Topic:** {topic}  ",
        f"**Region:** {brand_config.get('country', 'N/A')}",
        "",
        "---",
        "",
    ]

    # ── Brand Awareness Scorecard ────────────────────────────────────────────
    sa = awareness.get("sentiment_share", {})
    lines += [
        "## 📊 Brand Awareness Scorecard",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Mention Volume | {awareness.get('mention_volume', 0)} |",
        f"| Avg Engagement | {awareness.get('avg_engagement', 0)} |",
        f"| Awareness Score | **{awareness.get('awareness_score', 0)}/100** |",
        f"| Trajectory | {awareness.get('trajectory', 'stable')} |",
        f"| Sentiment (Pos/Neg/Neu) | {sa.get('positive', 0)}% / {sa.get('negative', 0)}% / {sa.get('neutral', 0)}% |",
        f"| Top Themes | {', '.join(awareness.get('top_themes', []))} |",
        "",
    ]

    # ── LinkedIn Intelligence ────────────────────────────────────────────────
    lines += ["## 💼 LinkedIn Intelligence", ""]
    if linkedin_posts:
        top5 = sorted(linkedin_posts, key=lambda p: p.get("score", 0), reverse=True)[:5]
        for i, post in enumerate(top5, 1):
            eng = post.get("engagements", {}) or {}
            likes = post.get("likes", 0)
            comments = post.get("comments_count", 0)
            lines += [
                f"### Post {i}",
                f"> {post.get('text', '')[:300]}",
                f"",
                f"- **Likes:** {likes} | **Comments:** {comments} | **Total Engagement:** {likes + comments}",
                f"- **Date:** {post.get('date', 'N/A')}",
                f"- **URL:** {post.get('url', 'N/A')}",
                "",
            ]
    else:
        lines += ["*No LinkedIn posts retrieved.*", ""]

    # ── Reddit Intelligence ──────────────────────────────────────────────────
    if reddit_posts:
        lines += ["## 🟠 Reddit Intelligence", ""]
        top5r = sorted(reddit_posts, key=lambda p: p.get("score", 0), reverse=True)[:5]
        for i, post in enumerate(top5r, 1):
            lines += [
                f"### r/{post.get('subreddit', 'unknown')} — Post {i}",
                f"> {post.get('title', '')[:200]}",
                f"",
                f"- **Score:** {post.get('score', 0)} | **Comments:** {post.get('comments_count', 0)}",
                f"- **Date:** {post.get('date', 'N/A')}",
                f"- **URL:** {post.get('url', 'N/A')}",
                "",
            ]

    # ── LLM Council Verdict ──────────────────────────────────────────────────
    lines += ["## 🧠 LLM Council Verdict", ""]
    verdict = council_result.get("verdict", {})
    if isinstance(verdict, dict):
        lines += [
            f"**Verdict:** {verdict.get('verdict', 'N/A')}  ",
            f"**Confidence:** {verdict.get('confidence', 0)}/100  ",
            f"**Dissent:** {verdict.get('dissent', 'None')}  ",
            "",
            f"**Summary:** {verdict.get('summary', 'N/A')}",
            "",
        ]
    else:
        lines += [str(verdict), ""]

    jurors = council_result.get("jurors", {})
    if jurors:
        lines += ["### Juror Perspectives", ""]
        for name, text in jurors.items():
            lines += [f"**{name}:** {text}", ""]

    if "error" in council_result:
        lines += [f"*Council note: {council_result['error']}*", ""]

    # ── Competitor Snapshot ──────────────────────────────────────────────────
    lines += ["## 🔍 Competitor Snapshot", ""]
    if competitors:
        lines += ["| Competitor | Notes |", "|------------|-------|"]
        for comp in competitors:
            lines.append(f"| {comp} | Monitoring required |")
        lines.append("")
    else:
        lines += ["*No competitors configured.*", ""]

    # ── Recommendations ──────────────────────────────────────────────────────
    score = awareness.get("awareness_score", 0)
    lines += ["## 💡 Recommendations", ""]
    if score < 20:
        lines += [
            "1. **Boost LinkedIn presence** — post frequency is low; aim for 3–5 posts/week.",
            "2. **Launch community engagement** — respond to mentions and build conversation.",
            "3. **Invest in content** — produce thought leadership content aligned to top themes.",
        ]
    elif score < 50:
        lines += [
            "1. **Amplify top-performing content** — identify what drives engagement and double down.",
            "2. **Competitor differentiation** — create content that directly contrasts with competitors.",
            "3. **Partnerships** — explore co-marketing with aligned brands to extend reach.",
        ]
    else:
        lines += [
            "1. **Maintain momentum** — consistent posting cadence is working, keep it up.",
            "2. **Deepen community** — leverage loyal audience for advocacy and UGC.",
            "3. **Expand internationally** — strong domestic awareness creates a platform for global growth.",
        ]
    lines += ["", "---", f"*Report generated by Brand Ops Marketing Suite · {timestamp}*"]

    markdown = "\n".join(lines)

    # Save
    workspace_path = Path(str(workspace))
    report_file = workspace_path / f"report_{ts_file}.md"
    with open(report_file, "w") as f:
        f.write(markdown)

    return markdown
