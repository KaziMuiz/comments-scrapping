import os
import time
import requests
import pandas as pd

GAMES = [
    {"name": "Counter-Strike 2", "app_id": 730, "mode": "multiplayer"},
    {"name": "Apex Legends", "app_id": 1172470, "mode": "multiplayer"},
    {"name": "Elden Ring", "app_id": 1245620, "mode": "single-player"},
    {"name": "Cyberpunk 2077", "app_id": 1091500, "mode": "single-player"},
    {"name": "Stardew Valley", "app_id": 413150, "mode": "single-player"},
]
PER_GAME = 400
PAUSE = 2

os.makedirs("data/games", exist_ok=True)


def get_page(url, params):
    for attempt in range(1, 6):
        try:
            response = requests.get(url, params=params, timeout=30)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            wait = 20 * attempt
            print(f"  No answer from Steam. Waiting {wait} seconds, then retrying...")
            time.sleep(wait)
            continue

        if response.status_code == 429:
            wait = 30 * attempt
            print(f"  Steam says slow down (429). Waiting {wait} seconds...")
            time.sleep(wait)
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError("Steam kept refusing or not answering. Wait a while and run again.")


def collect_reviews(app_id, target):
    url = f"https://store.steampowered.com/appreviews/{app_id}"
    reviews = []
    seen_ids = set()
    cursor = "*"
    pages_without_new = 0

    while len(reviews) < target:
        params = {"json": 1, "language": "english", "filter": "recent", "num_per_page": 100, "cursor": cursor}
        data = get_page(url, params)

        page = data.get("reviews", [])
        if not page:
            print("  No more reviews from Steam, stopping.")
            break

        before = len(reviews)
        for r in page:
            if r["recommendationid"] not in seen_ids:
                seen_ids.add(r["recommendationid"])
                reviews.append(r)
        print("  collected so far:", len(reviews))

        if len(reviews) == before:
            pages_without_new += 1
            if pages_without_new >= 3:
                print("  Only repeats coming back, stopping.")
                break
        else:
            pages_without_new = 0

        new_cursor = data.get("cursor")
        if not new_cursor or new_cursor == cursor:
            print("  Cursor did not move, stopping.")
            break
        cursor = new_cursor
        time.sleep(PAUSE)

    return reviews[:target]


for game in GAMES:
    path = f"data/games/{game['app_id']}.csv"
    if os.path.exists(path):
        print("Already saved, skipping:", game["name"])
        continue

    print("Collecting:", game["name"])
    reviews = collect_reviews(game["app_id"], PER_GAME)

    if len(reviews) < PER_GAME:
        print("  WARNING: only got", len(reviews), "reviews. Not saving, try again later.")
        time.sleep(10)
        continue

    rows = []
    for r in reviews:
        rows.append({
            "game": game["name"],
            "mode": game["mode"],
            "recommendationid": r["recommendationid"],
            "review": r["review"],
            "voted_up": r["voted_up"],
            "votes_up": r["votes_up"],
            "timestamp_created": r["timestamp_created"],
            "playtime_at_review_min": r["author"].get("playtime_at_review"),
        })
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
    print("  Saved", len(rows), "reviews to", path)
    time.sleep(10)

frames = [pd.read_csv(f"data/games/{g['app_id']}.csv") for g in GAMES
          if os.path.exists(f"data/games/{g['app_id']}.csv")]
df = pd.concat(frames, ignore_index=True)
df.to_csv("data/steam_reviews_5games.csv", index=False, encoding="utf-8")
print("Combined file saved:", df.shape)