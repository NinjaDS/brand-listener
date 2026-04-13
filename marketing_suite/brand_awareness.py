"""
Brand awareness computation from a list of posts.
"""

from __future__ import annotations
import math
from typing import List, Dict, Any

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "AI & Technology": ["ai", "technology", "digital", "automation", "platform", "data"],
    "ESG & Sustainability": ["sustainability", "climate", "green", "environment", "eco"],
    "Brand & Marketing": ["brand", "campaign", "marketing", "launch", "awareness", "creative"],
    "Product & Innovation": ["product", "innovation", "new", "launch", "collection", "design"],
    "Community & Culture": ["community", "culture", "diversity", "inclusion", "people", "team"],
    "Customer Experience": ["customer", "experience", "service", "review", "quality", "satisfaction"],
    "Partnerships & Events": ["partner", "event", "conference", "collaboration", "sponsor"],
    "Financial & Growth": ["growth", "revenue", "sales", "profit", "investment", "expand"],
}

POSITIVE_WORDS = [
    "great", "excellent", "love", "amazing", "best", "fantastic", "good", "awesome",
    "wonderful", "brilliant", "happy", "positive", "recommend", "impressive", "outstanding",
]
NEGATIVE_WORDS = [
    "bad", "terrible", "worst", "hate", "awful", "poor", "disappointing", "negative",
    "fail", "problem", "issue", "broken", "wrong", "complaint", "unhappy",
]


def _sentiment(text: str) -> str:
    t = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


def compute_awareness(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute brand awareness metrics from a list of posts.
    """
    mention_volume = len(posts)

    if not posts:
        return {
            "mention_volume": 0,
            "avg_engagement": 0.0,
            "sentiment_share": {"positive": 0.0, "negative": 0.0, "neutral": 100.0},
            "top_themes": [],
            "awareness_score": 0.0,
            "trajectory": "stable",
        }

    # Engagement
    engagements = [
        (p.get("likes") or 0) + (p.get("comments_count") or 0)
        for p in posts
    ]
    avg_engagement = sum(engagements) / len(engagements)

    # Sentiment
    sentiments = [_sentiment(p.get("text", "") + " " + p.get("title", "")) for p in posts]
    pos_pct = round(sentiments.count("positive") / len(sentiments) * 100, 1)
    neg_pct = round(sentiments.count("negative") / len(sentiments) * 100, 1)
    neu_pct = round(100 - pos_pct - neg_pct, 1)

    # Themes
    theme_scores: Dict[str, int] = {t: 0 for t in TOPIC_KEYWORDS}
    for p in posts:
        combined = (p.get("text", "") + " " + p.get("title", "")).lower()
        for theme, keywords in TOPIC_KEYWORDS.items():
            theme_scores[theme] += sum(1 for kw in keywords if kw in combined)
    top_themes = sorted(theme_scores, key=lambda t: theme_scores[t], reverse=True)[:3]

    # Awareness score: 40% volume, 40% engagement, 20% sentiment
    vol_score = min(mention_volume / 50, 1.0) * 100  # cap at 50 posts = 100
    eng_score = min(avg_engagement / 100, 1.0) * 100  # cap at 100 eng = 100
    sent_score = pos_pct  # % positive
    awareness_score = round(0.4 * vol_score + 0.4 * eng_score + 0.2 * sent_score, 2)

    return {
        "mention_volume": mention_volume,
        "avg_engagement": round(avg_engagement, 2),
        "sentiment_share": {
            "positive": pos_pct,
            "negative": neg_pct,
            "neutral": neu_pct,
        },
        "top_themes": top_themes,
        "awareness_score": awareness_score,
        "trajectory": "stable",
    }
