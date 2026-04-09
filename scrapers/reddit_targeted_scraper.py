import urllib.request
import urllib.parse
import json
import time
from collections import defaultdict

HEADERS = {"User-Agent": "brand-listener/1.0 (research)"}

def reddit_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def extract_comments(data, post_title="", subreddit=""):
    comments = []
    if isinstance(data, list):
        for item in data:
            comments.extend(extract_comments(item, post_title, subreddit))
    elif isinstance(data, dict):
        kind = data.get("kind")
        d = data.get("data", {})
        if kind == "Listing":
            for child in d.get("children", []):
                comments.extend(extract_comments(child, post_title, subreddit))
        elif kind == "t1":
            body = d.get("body", "").strip()
            if body and body not in ("[deleted]", "[removed]") and len(body) > 5:
                comments.append({
                    "author": d.get("author", ""),
                    "body": body,
                    "score": d.get("score", 0),
                    "post_title": post_title,
                    "subreddit": subreddit,
                })
            replies = d.get("replies", {})
            if isinstance(replies, dict):
                comments.extend(extract_comments(replies, post_title, subreddit))
    return comments

all_posts = []

# Collect posts from targeted subreddits
subs = ["curlyhair", "CurlyHairCare", "wavyhair", "NaturalHair", "finehair", "curlygirl"]
for sub in subs:
    try:
        url = f"https://www.reddit.com/r/{sub}/search.json?q=curlsmith&restrict_sr=1&limit=25&sort=top"
        data = reddit_get(url)
        posts = data["data"]["children"]
        for p in posts:
            d = p["data"]
            if d["num_comments"] > 2:
                all_posts.append({"subreddit": sub, "id": d["id"], "title": d["title"], "comments": d["num_comments"]})
        print(f"r/{sub}: {len(posts)} posts found")
        time.sleep(0.5)
    except Exception as e:
        print(f"r/{sub} error: {e}")

# Also general search
try:
    url = "https://www.reddit.com/search.json?q=curlsmith+hair&limit=50&sort=top&type=link"
    data = reddit_get(url)
    posts = data["data"]["children"]
    for p in posts:
        d = p["data"]
        if d["num_comments"] > 2:
            all_posts.append({"subreddit": d["subreddit"], "id": d["id"], "title": d["title"], "comments": d["num_comments"]})
    print(f"General search: {len(posts)} posts")
except Exception as e:
    print(f"General search error: {e}")

# Deduplicate posts
seen_ids = set()
unique_posts = []
for p in all_posts:
    if p["id"] not in seen_ids:
        seen_ids.add(p["id"])
        unique_posts.append(p)

unique_posts = sorted(unique_posts, key=lambda x: x["comments"], reverse=True)
print(f"\nUnique posts to fetch comments from: {len(unique_posts)}")
for p in unique_posts[:15]:
    print(f"  [{p['subreddit']}] {p['title'][:65]} ({p['comments']} comments)")

# Fetch comments from top 25 posts only
all_comments = []
for p in unique_posts[:25]:
    try:
        url = f"https://www.reddit.com/r/{p['subreddit']}/comments/{p['id']}.json?limit=200"
        data = reddit_get(url)
        comments = extract_comments(data, p["title"], p["subreddit"])
        # Only keep comments mentioning curlsmith
        relevant = [c for c in comments if "curlsmith" in c["body"].lower()]
        all_comments.extend(relevant)
        print(f"  [{p['subreddit']}] {p['title'][:50]} → {len(relevant)}/{len(comments)} curlsmith comments")
        time.sleep(0.5)
    except Exception as e:
        print(f"  Error {p['id']}: {e}")

print(f"\nTotal Curlsmith comments: {len(all_comments)}")
with open("reddit_curlsmith_filtered.json", "w") as f:
    json.dump(all_comments, f, indent=2)
print("Saved.")
