import time
import requests

URL = "https://store.steampowered.com/appreviews/730"
TARGET = 2000

reviews = []
seen_ids = set()
cursor = "*"

while len(reviews) < TARGET:
    params = {"json": 1, "language": "english", "num_per_page": 100, "cursor": cursor}
    data = requests.get(URL, params=params, timeout=10).json()

    page = data["reviews"]
    if not page:
        print("No more reviews, stopping.")
        break

    for r in page:
        if r["recommendationid"] not in seen_ids:
            seen_ids.add(r["recommendationid"])
            reviews.append(r)

    cursor = data["cursor"]
    print("Collected so far:", len(reviews))
    time.sleep(1)

reviews = reviews[:TARGET]
print("Done. Total reviews:", len(reviews))
import pandas as pd

rows = []
for r in reviews:
    rows.append({
        "recommendationid": r["recommendationid"],
        "review": r["review"],
        "voted_up": r["voted_up"],
        "votes_up": r["votes_up"],
        "timestamp_created": r["timestamp_created"],
        "playtime_at_review_min": r["author"].get("playtime_at_review"),
    })

df = pd.DataFrame(rows)
df.to_csv("data/steam_reviews.csv", index=False, encoding="utf-8")
print("Saved:", df.shape)