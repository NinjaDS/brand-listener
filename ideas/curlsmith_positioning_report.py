"""
curlsmith_positioning_report.py
Generates the brand positioning report MD from positioning_data.json
"""

import json
from datetime import datetime

with open("reports/curlsmith/positioning_data.json") as f:
    data = json.load(f)

assoc = data["brand_associations"]
scores = data["attribute_scores"]
attributes = data["attributes"]
proximity = data["proximity_matrix"]
substitution = data["substitution_risk"]

def bar(val, max_val=10, width=10):
    filled = round((val / max_val) * width)
    return "█" * filled + "░" * (width - filled)

lines = []
lines.append("# Curlsmith — Brand Positioning Report")
lines.append(f"\n**Generated:** April 09, 2026  ")
lines.append("**Source:** Reddit (487 comments, 6 subreddits) + competitive analysis  ")
lines.append("**Method:** Association inventory · Attribute scorecard · Perceptual mapping · Whitespace analysis\n")
lines.append("---\n")

# ── 1. Association Inventory ──────────────────────────────────────────────────
lines.append("## 1. Brand Association Inventory\n")
lines.append("What does 'Curlsmith' mean in the minds of Reddit users?\n")
lines.append("| Association | Mentions | % of Comments | Strength |")
lines.append("|-------------|---------|--------------|---------|")
for label, d in sorted(assoc.items(), key=lambda x: -x[1]["count"]):
    strength = "Strong" if d["pct"] >= 20 else ("Moderate" if d["pct"] >= 10 else "Weak")
    lines.append(f"| {label} | {d['count']} | {d['pct']}% | {strength} |")

lines.append("\n### Top Association Evidence\n")
for label, d in sorted(assoc.items(), key=lambda x: -x[1]["count"])[:5]:
    lines.append(f"**{label}**")
    for ev in d["evidence"]:
        lines.append(f"> *\"{ev.strip()}\"*")
    lines.append("")

lines.append("### Key Insight")
lines.append("""
Curlsmith's strongest mental association is **moisture and hydration** (37% of comments) — not curl definition or hold, which is surprising for a styling brand. This suggests users have adopted Curlsmith primarily as a **treatment/conditioning brand** rather than a pure styler. The bond repair range dominates product-level discussion (21%).

The **formula change concern** (6%) is small in volume but disproportionately high in emotional intensity — these comments are among the most upvoted negative posts.
""")

lines.append("---\n")

# ── 2. Attribute Scorecard ────────────────────────────────────────────────────
lines.append("## 2. Competitive Attribute Scorecard\n")
lines.append("Scores derived from Reddit sentiment analysis (1–10 scale)\n")
lines.append("![Attribute Scorecard](charts/attribute_scorecard.png)\n")
lines.append("| Attribute | Curlsmith | Innersense | Ouidad | DevaCurl |")
lines.append("|-----------|-----------|-----------|--------|---------|")
for i, attr in enumerate(attributes):
    lines.append(f"| {attr} | {scores['Curlsmith'][i]} | {scores['Innersense'][i]} | {scores['Ouidad'][i]} | {scores['DevaCurl'][i]} |")

lines.append("\n### Curlsmith Strengths vs Competitors")
lines.append("- **Product Range (8.5)** — broadest lineup of the four brands; users appreciate having a full routine in one brand")
lines.append("- **Availability (8.0)** — easy to find online and in stores; beats Innersense and Ouidad on accessibility")
lines.append("- **Moisture/Hydration (7.8)** — core brand strength, well recognised")
lines.append("")
lines.append("### Curlsmith Weaknesses vs Competitors")
lines.append("- **Brand Trust (6.0)** — lowest of the group, driven by post-acquisition sentiment and formula change complaints")
lines.append("- **Price/Value (5.5)** — perceived as expensive relative to results, especially post-2022")
lines.append("- **Hold Strength (6.5)** — frequently compared unfavourably to Ouidad and DevaCurl for definition")

lines.append("\n---\n")

# ── 3. Proximity Matrix ───────────────────────────────────────────────────────
lines.append("## 3. Competitive Proximity Matrix\n")
lines.append("How similar is Curlsmith's positioning to each competitor? (cosine similarity of attribute scores)\n")
lines.append("| Brand Pair | Similarity Score | Substitution Risk |")
lines.append("|-----------|----------------|-----------------|")
for pair, risk_text in substitution.items():
    brands_in_pair = pair.split(" → ")
    sim_key_options = [f"{brands_in_pair[0]} vs {brands_in_pair[1]}", f"{brands_in_pair[1]} vs {brands_in_pair[0]}"]
    sim = next((v for k, v in proximity.items() if k in sim_key_options), "—")
    lines.append(f"| {pair} | {sim} | {risk_text} |")

lines.append("\n### Key Finding")
lines.append("""
**Innersense is Curlsmith's most dangerous competitor.** Near-identical positioning (clean ingredients, moisture-first, premium pricing) means users switch between the two frequently. Reddit threads often frame it as a direct choice — and post-acquisition, Innersense is winning that comparison on trust.

Ouidad competes on performance (especially hold/definition for type 3-4 curls) but occupies a more salon-centric channel, reducing direct substitution risk for the mass online buyer.
""")

lines.append("---\n")

# ── 4. Perceptual Map ─────────────────────────────────────────────────────────
lines.append("## 4. Perceptual Map\n")
lines.append("**Axes:** Price Positioning (expensive → affordable) × Expert Credibility (mass → specialist)\n")
lines.append("![Perceptual Map](charts/perceptual_map.png)\n")
lines.append("### Reading the Map")
lines.append("""
- **Curlsmith** sits in the mid-premium / good-credibility zone — but has drifted toward the centre since the Helen of Troy acquisition weakened its expert positioning
- **Innersense** occupies the premium clean-beauty expert space — Curlsmith's closest threat and aspirational territory
- **Ouidad** owns the premium/specialist quadrant — high trust, salon heritage, strong curl expertise
- **SheaMoisture & Cantu** dominate affordable/accessible — Curlsmith does not compete here
- **Whitespace opportunity:** Accessible expert positioning (top-right) — expert-level results at a more accessible price. Currently no brand clearly owns this space
""")

lines.append("---\n")

# ── 5. Whitespace Assessment ──────────────────────────────────────────────────
lines.append("## 5. Whitespace Assessment\n")
lines.append("### Unclaimed Territory in the Market\n")
lines.append("| Whitespace | Current Gap | Why it Matters |")
lines.append("|-----------|------------|---------------|")
lines.append("| **Accessible expert** | No brand combines specialist credibility with mass accessibility | Huge reddit cohort wants 'Ouidad results at SheaMoisture prices' |")
lines.append("| **Postpartum hair recovery** | No curly brand owns this moment | High emotional purchase trigger; multiple Reddit mentions |")
lines.append("| **Kids/mixed-texture hair** | Parents have no trusted curly brand for children | Parents are actively asking Reddit for recommendations |")
lines.append("| **Men with curls** | Almost zero brand attention | Multiple Reddit threads on men's curl care with no brand stepping up |")
lines.append("| **Hormone-related curl change** | Menopause, pregnancy, BC pill changes cause curl pattern shifts | High-anxiety purchase moment, no brand addressing this directly |")
lines.append("")

lines.append("---\n")

# ── 6. Positioning Recommendation ────────────────────────────────────────────
lines.append("## 6. Positioning Recommendation\n")
lines.append("### Current Positioning (as perceived on Reddit)")
lines.append("> *\"A premium curl care brand with a strong moisture and bond-repair reputation — but with trust concerns following its acquisition, and unclear differentiation vs Innersense.\"*\n")

lines.append("### Recommended Positioning")
lines.append("> *\"The curl expert that actually works for real life — not just salon days.\"*\n")

lines.append("### Rationale")
lines.append("""
1. **Own the 'real life' angle** — Reddit shows users frustrated with products that only work when applied perfectly. Curlsmith's broad range and ease-of-use scores position it to win the 'everyday curl' space

2. **Rebuild trust through transparency** — the Helen of Troy acquisition damage is recoverable. A direct communication campaign (\"what changed, what didn't, what we're doing about it\") would directly address the #1 negative driver

3. **Lean into the whitespace** — postpartum and hormone-related hair change is an emotionally charged, underserved segment with genuine need. A targeted sub-range or content series would create strong brand loyalty at a key life moment

4. **Counter Innersense on trust, not ingredients** — don't out-clean Innersense (they own that). Instead, compete on consistency, range depth, and real-world proof (before/after UGC campaigns)

5. **Stop competing on hold** — Ouidad and DevaCurl own the definition/hold perception. Curlsmith's moisture and repair strengths are more differentiated; double down there
""")

lines.append("---\n")
lines.append("*Analysis based on 487 real Reddit comments. Attribute scores are sentiment-derived estimates, not survey data.*")

report = "\n".join(lines)
with open("reports/curlsmith/brand_positioning_report.md", "w") as f:
    f.write(report)
print(f"Report written: {len(report)} chars")
