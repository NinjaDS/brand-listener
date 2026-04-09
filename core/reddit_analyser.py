import json
import re
from collections import defaultdict, Counter

with open("reddit_curlsmith_comments.json") as f:
    comments = json.load(f)

# Filter to comments that actually mention Curlsmith
curlsmith_comments = [c for c in comments if "curlsmith" in c["body"].lower()]
print(f"Total comments: {len(comments)}")
print(f"Curlsmith-specific comments: {len(curlsmith_comments)}")

# ── Age signal detection ──────────────────────────────────────────────────────
age_patterns = [
    (r"\bi[\'']?m\s+(\d{1,2})\b", "stated_age"),
    (r"\b(\d{1,2})\s*y/?o\b", "stated_age"),
    (r"\bage\s+(\d{1,2})\b", "stated_age"),
    (r"\b(\d{1,2})\s*year[s]?\s*old\b", "stated_age"),
    (r"\bteenager\b|\bteen\b|\bhigh school\b", "teen"),
    (r"\bcollege\b|\buniversity\b|\buni\b|\bfreshman\b|\bsophomore\b|\bjunior\b|\bsenior\b.*\bcollege\b", "college"),
    (r"\b20s\b|\bin my 20\b|\bearly 20\b|\bmid 20\b|\blate 20\b", "20s"),
    (r"\b30s\b|\bin my 30\b|\bearly 30\b|\bmid 30\b|\blate 30\b", "30s"),
    (r"\b40s\b|\bin my 40\b|\bearly 40\b|\bmid 40\b|\blate 40\b", "40s"),
    (r"\b50s\b|\bin my 50\b|\bover 50\b", "50s+"),
    (r"\bmy daughter\b|\bmy kid\b|\bmy child\b|\bmy son\b|\bmy toddler\b", "parent"),
    (r"\bpostpartum\b|\bpregnant\b|\bnewborn\b|\bbaby\b.*\bhair\b", "parent"),
    (r"\bmenopause\b|\bperimenopause\b", "40s+"),
]

age_buckets = defaultdict(list)
stated_ages = []

for c in curlsmith_comments:
    body = c["body"].lower()
    matched = False
    for pattern, bucket in age_patterns:
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            if bucket == "stated_age":
                age = int(m.group(1))
                if 10 <= age <= 70:
                    stated_ages.append(age)
                    if age < 20:
                        age_buckets["Under 20"].append(c)
                    elif age < 30:
                        age_buckets["20s"].append(c)
                    elif age < 40:
                        age_buckets["30s"].append(c)
                    elif age < 50:
                        age_buckets["40s"].append(c)
                    else:
                        age_buckets["50s+"].append(c)
                    matched = True
            else:
                age_buckets[bucket].append(c)
                matched = True

print("\n── Age signals found ──")
for bucket, items in sorted(age_buckets.items()):
    print(f"  {bucket}: {len(items)} mentions")

if stated_ages:
    print(f"\nStated ages: {sorted(stated_ages)}")
    print(f"Avg stated age: {sum(stated_ages)/len(stated_ages):.1f}")

# ── What are they saying about Curlsmith? ────────────────────────────────────
print("\n── What they're saying ──")

# Sentiment keywords
positive_kw = ["love", "holy grail", "amazing", "excellent", "great", "best", "perfect",
               "obsessed", "game changer", "works", "recommend", "favorite", "incredible",
               "transformed", "soft", "defined", "moistur", "hydrat", "thank you curlsmith"]
negative_kw = ["hate", "terrible", "awful", "disappointing", "doesn't work", "stopped working",
               "bad", "sticky", "crunchy", "greasy", "buildup", "buildup", "waste",
               "not worth", "overrated", "changed formula", "reformulated", "discontinu"]
topic_kw = {
    "Hold/Gel": ["gel", "hold", "cast", "scrunch", "crunch"],
    "Moisture/Hydration": ["moisture", "moistur", "hydrat", "dry", "frizz", "frizzy"],
    "Scalp/Hair Health": ["scalp", "hair loss", "shedding", "grow", "health"],
    "Curly Hair Method": ["cgm", "curly girl", "curly method", "co-wash", "cowash", "porosity"],
    "Specific Products": ["wave maker", "curl defining", "weightless", "hydro style", "styling cream"],
    "Price/Value": ["price", "expensive", "worth", "money", "cheap", "affordable", "cost"],
    "Formula Change": ["reformulat", "changed formula", "old formula", "new formula", "different now"],
}

pos_count = 0
neg_count = 0
topic_counts = defaultdict(int)
sentiments = []

for c in curlsmith_comments:
    body = c["body"].lower()
    is_pos = any(kw in body for kw in positive_kw)
    is_neg = any(kw in body for kw in negative_kw)
    if is_pos and not is_neg:
        sentiments.append("positive")
        pos_count += 1
    elif is_neg and not is_pos:
        sentiments.append("negative")
        neg_count += 1
    else:
        sentiments.append("neutral")
    for topic, kws in topic_kw.items():
        if any(kw in body for kw in kws):
            topic_counts[topic] += 1

print(f"\nSentiment breakdown ({len(curlsmith_comments)} Curlsmith comments):")
print(f"  Positive: {pos_count} ({pos_count/len(curlsmith_comments)*100:.0f}%)")
print(f"  Negative: {neg_count} ({neg_count/len(curlsmith_comments)*100:.0f}%)")
print(f"  Neutral:  {len(curlsmith_comments)-pos_count-neg_count} ({(len(curlsmith_comments)-pos_count-neg_count)/len(curlsmith_comments)*100:.0f}%)")

print(f"\nTopics discussed:")
for topic, cnt in sorted(topic_counts.items(), key=lambda x: -x[1]):
    print(f"  {topic}: {cnt}")

# ── Print sample comments ──────────────────────────────────────────────────────
print("\n── Sample Positive Comments ──")
pos_comments = [c for c, s in zip(curlsmith_comments, sentiments) if s == "positive"]
for c in sorted(pos_comments, key=lambda x: x["score"], reverse=True)[:5]:
    print(f"  [{c['subreddit']}] score:{c['score']} | {c['body'][:200].strip()}")
    print()

print("── Sample Negative Comments ──")
neg_comments = [c for c, s in zip(curlsmith_comments, sentiments) if s == "negative"]
for c in sorted(neg_comments, key=lambda x: x["score"], reverse=True)[:5]:
    print(f"  [{c['subreddit']}] score:{c['score']} | {c['body'][:200].strip()}")
    print()

# Save analysis
result = {
    "total_comments": len(comments),
    "curlsmith_comments": len(curlsmith_comments),
    "sentiment": {"positive": pos_count, "negative": neg_count, "neutral": len(curlsmith_comments)-pos_count-neg_count},
    "age_buckets": {k: len(v) for k, v in age_buckets.items()},
    "stated_ages": stated_ages,
    "topics": dict(topic_counts),
    "top_positive": [{"score": c["score"], "subreddit": c["subreddit"], "body": c["body"][:300]} for c in sorted(pos_comments, key=lambda x: x["score"], reverse=True)[:10]],
    "top_negative": [{"score": c["score"], "subreddit": c["subreddit"], "body": c["body"][:300]} for c in sorted(neg_comments, key=lambda x: x["score"], reverse=True)[:10]],
}
with open("reddit_curlsmith_analysis.json", "w") as f:
    json.dump(result, f, indent=2)
print("\nSaved analysis to reddit_curlsmith_analysis.json")
