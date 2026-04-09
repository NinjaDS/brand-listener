import urllib.request
import urllib.parse
import json
import time
import re
from datetime import datetime

HEADERS = {"User-Agent": "brand-listener/1.0 (research)"}

def reddit_search(query, limit=100):
    url = f"https://www.reddit.com/search.json?q={urllib.parse.quote(query)}&limit={limit}&sort=new&type=link"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get_comments(subreddit, post_id, limit=100):
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit={limit}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def extract_comments(comment_data):
    """Recursively extract all comments from Reddit comment tree."""
    comments = []
    if not isinstance(comment_data, list):
        return comments
    for item in comment_data:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        data = item.get("data", {})
        if kind == "Listing":
            comments.extend(extract_comments(data.get("children", [])))
        elif kind == "t1":  # comment
            body = data.get("body", "").strip()
            author = data.get("author", "")
            score = data.get("score", 0)
            if body and body != "[deleted]" and body != "[removed]" and len(body) > 10:
                comments.append({
                    "author": author,
                    "body": body,
                    "score": score,
                    "created": data.get("created_utc", 0),
                })
            # recurse into replies
            replies = data.get("replies", {})
            if isinstance(replies, dict):
                comments.extend(extract_comments(replies.get("data", {}).get("children", [])))
    return comments

print("Searching Reddit for 'curlsmith'...")
data = reddit_search("curlsmith", limit=100)
posts = data["data"]["children"]
print(f"Found {len(posts)} posts\n")

# Show top posts by comment count
posts_sorted = sorted(posts, key=lambda x: x["data"]["num_comments"], reverse=True)
print("Top posts by comments:")
for p in posts_sorted[:10]:
    d = p["data"]
    print(f"  [{d['subreddit']}] {d['title'][:65]:<65} — {d['num_comments']} comments  id:{d['id']}")

# Collect comments from top posts
print("\nCollecting comments from top posts...")
all_comments = []
seen_post_ids = set()

for p in posts_sorted[:15]:
    d = p["data"]
    if d["num_comments"] < 2:
        continue
    if d["id"] in seen_post_ids:
        continue
    seen_post_ids.add(d["id"])
    try:
        comment_data = get_comments(d["subreddit"], d["id"], limit=100)
        comments = extract_comments(comment_data)
        for c in comments:
            c["post_title"] = d["title"]
            c["subreddit"] = d["subreddit"]
        all_comments.extend(comments)
        print(f"  [{d['subreddit']}] {d['title'][:55]} — {len(comments)} comments fetched")
        time.sleep(0.8)
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nTotal comments collected: {len(all_comments)}")

# Save raw comments
with open("reddit_curlsmith_comments.json", "w") as f:
    json.dump(all_comments, f, indent=2)

print("Saved to reddit_curlsmith_comments.json")
