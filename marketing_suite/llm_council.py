"""
LLM Council — AI Jury using AWS Bedrock (Claude Sonnet 4).
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

MODEL_ID = "us.anthropic.claude-sonnet-4-6"

JURORS = {
    "Sceptic": "You are a sceptical marketing analyst. You question assumptions, highlight risks, and look for red flags in brand data.",
    "Optimist": "You are an optimistic brand strategist. You highlight strengths, opportunities, and positive trends in brand data.",
    "Strategist": "You are a seasoned business strategist. You focus on competitive positioning, market opportunities, and strategic actions.",
    "Consumer": "You are a typical consumer. You speak from the perspective of the target audience, focusing on experience and emotion.",
    "Analyst": "You are a data-driven analyst. You focus on numbers, trends, and quantitative evidence in brand performance.",
}


def _build_prompt(brand_name: str, awareness: Dict, posts_sample: List[Dict], question: str) -> str:
    sample_texts = "\n".join(
        f"- {p.get('text', '')[:200]}" for p in posts_sample[:3]
    )
    return f"""Brand: {brand_name}

Brand Awareness Metrics:
- Mention Volume: {awareness.get('mention_volume', 0)}
- Avg Engagement: {awareness.get('avg_engagement', 0)}
- Awareness Score: {awareness.get('awareness_score', 0)}/100
- Sentiment: {awareness.get('sentiment_share', {})}
- Top Themes: {', '.join(awareness.get('top_themes', []))}

Sample Posts:
{sample_texts if sample_texts.strip() else '(no posts available)'}

Question: {question}

Please provide your perspective in 2-3 sentences."""


def convene_council(
    brand_name: str,
    awareness_dict: Dict[str, Any],
    posts_sample: List[Dict],
    question: str,
) -> Dict[str, Any]:
    """
    Convene LLM Council of 5 jurors and produce a synthesised verdict.
    """
    try:
        import boto3  # type: ignore
        bedrock = boto3.client("bedrock-runtime")
    except Exception as e:
        return {
            "jurors": {},
            "verdict": {
                "verdict": "Council unavailable",
                "confidence": 0,
                "dissent": "",
                "summary": "Bedrock not configured",
            },
            "error": str(e),
        }

    juror_verdicts: Dict[str, str] = {}

    for juror_name, system_prompt in JURORS.items():
        try:
            prompt = _build_prompt(brand_name, awareness_dict, posts_sample, question)
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
                "system": system_prompt,
            })
            response = bedrock.invoke_model(modelId=MODEL_ID, body=body)
            result = json.loads(response["body"].read())
            verdict_text = result["content"][0]["text"]
            juror_verdicts[juror_name] = verdict_text
            logger.info(f"Juror {juror_name} responded")
        except Exception as e:
            logger.warning(f"Juror {juror_name} failed: {e}")
            juror_verdicts[juror_name] = f"(unavailable: {e})"

    # Judge synthesis
    try:
        juror_summary = "\n\n".join(
            f"**{name}**: {text}" for name, text in juror_verdicts.items()
        )
        judge_prompt = f"""You are a Chief Judge synthesising the perspectives of 5 expert jurors about the brand '{brand_name}'.

Juror Perspectives:
{juror_summary}

Synthesise these into a single JSON response with these keys:
- verdict: one-sentence overall verdict
- confidence: integer 0-100
- dissent: any major disagreements between jurors (one sentence)
- summary: 2-3 sentence executive summary

Respond with ONLY valid JSON."""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "messages": [{"role": "user", "content": judge_prompt}],
            "system": "You are a Chief Judge. Always respond with valid JSON only.",
        })
        response = bedrock.invoke_model(modelId=MODEL_ID, body=body)
        result = json.loads(response["body"].read())
        raw = result["content"][0]["text"].strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        verdict = json.loads(raw)
    except Exception as e:
        logger.warning(f"Judge synthesis failed: {e}")
        verdict = {
            "verdict": "Synthesis unavailable",
            "confidence": 0,
            "dissent": "",
            "summary": str(e),
        }

    return {
        "jurors": juror_verdicts,
        "verdict": verdict,
    }
