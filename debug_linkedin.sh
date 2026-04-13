#!/bin/bash
cd /Users/kumaresaperumal/Ideas/brand-listener
source venv/bin/activate
python - <<'EOF'
from linkdapi import LinkdAPI
import json, time

client = LinkdAPI("li-8OP0EoHZ73zTLBCZgiZ1fNt4Ix-y18IF5yoxpAWfWVy1GTjuIWjTH-IA9rA45IP5UrnbEDzrx7mLo6aNv3mFgdIIJ-lo7Q")

for keyword in ["Curlsmith hair", "Lands End clothing", "Curlsmith"]:
    print(f"\n=== search_posts: '{keyword}' ===")
    resp = client.search_posts(keyword=keyword, sort_by="date_posted")
    print(f"  success: {resp.get('success')}")
    posts = resp.get("data", {}).get("posts", [])
    print(f"  posts returned: {len(posts)}")
    if posts:
        print(f"  first post text: {posts[0].get('text','')[:100]}")
    time.sleep(5)
EOF
