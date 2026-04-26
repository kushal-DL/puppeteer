"""Check PR #7 comments."""
import urllib.request, json, os

token = os.environ["GITHUB_TOKEN"]
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

# Issue comments
req = urllib.request.Request(
    "https://api.github.com/repos/kushal-sharma-24/silver-pancake/issues/7/comments",
    headers=headers,
)
comments = json.loads(urllib.request.urlopen(req).read())
print(f"Issue comments ({len(comments)}):")
for c in comments:
    user = c["user"]["login"]
    ts = c["created_at"]
    body = c["body"][:120]
    print(f"  [{user}] {ts}: {body}")

# Review comments
req2 = urllib.request.Request(
    "https://api.github.com/repos/kushal-sharma-24/silver-pancake/pulls/7/comments",
    headers=headers,
)
rev_comments = json.loads(urllib.request.urlopen(req2).read())
print(f"\nReview comments ({len(rev_comments)}):")
for c in rev_comments:
    user = c["user"]["login"]
    ts = c["created_at"]
    body = c["body"][:120]
    print(f"  [{user}] {ts}: {body}")
