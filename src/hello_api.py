import requests

BASE = "https://hacker-news.firebaseio.com/v0"

top_ids = requests.get(f"{BASE}/topstories.json", timeout=10).json()
print("Number of top stories:", len(top_ids))

first_id = top_ids[0]
story = requests.get(f"{BASE}/item/{first_id}.json", timeout=10).json()
print("Title:", story["title"])
print("Number of comments:", story.get("descendants"))
print("Fields available:", list(story.keys()))
print("Top-level comments (kids):", len(story["kids"]))