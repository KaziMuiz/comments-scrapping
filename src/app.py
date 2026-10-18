"""Local server for the Steam review project.

Run it from the main project folder:   py src/app.py
Then open:                             http://127.0.0.1:8000

It does two jobs:
  1. Shows the dashboard from the docs folder.
  2. Answers /api/analyze for ANY Steam game: it reads the game's most recent
     English reviews, finds the problems players mention most, and returns
     counts, percentages and a few short example comments.
"""
import json
import mimetypes
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
CACHE_DIR = os.path.join(ROOT, "data", "live")
HOST, PORT = "127.0.0.1", 8000
ALLOWED_COUNTS = (200, 400, 1000)
CACHE_SECONDS = 6 * 3600
PAUSE = 1.5

# ---------- Themes (the same ones used for the five-game analysis) ----------
PROBLEM_THEMES = [
    {"key": "cheating", "label": "Cheating",
     "focus": "Stronger anti-cheat and faster bans",
     "pattern": r"\b(?:cheat\w*|hack\w*|aimbot\w*|wallhack\w*)"},
    {"key": "servers_lag", "label": "Servers and lag",
     "focus": "More server capacity and better matchmaking",
     "pattern": r"\b(?:servers?|lag|laggy|ping|matchmaking|disconnect\w*)\b"},
    {"key": "bugs_performance", "label": "Bugs and performance",
     "focus": "Bug-fix patches and performance optimization",
     "pattern": r"\b(?:bugs?|buggy|crash\w*|glitch\w*|fps|stutter\w*|optimi[sz]ation|performance)\b"},
    {"key": "monetization", "label": "Price and purchases",
     "focus": "Review pricing and in-game purchases",
     "pattern": r"\b(?:price\w*|expensive|overpriced|microtransactions?|paywall\w*|pay[- ]to[- ]win|p2w|battle ?pass|skins?|dlc|refund\w*|greedy|cash ?grab)\b"},
    {"key": "toxicity", "label": "Toxic players",
     "focus": "Better reporting and moderation tools",
     "pattern": r"\b(?:toxic\w*|racis\w*|rude|smurf\w*|trolls?|griefers?|harass\w*|insults?|abusive|slurs?)\b"},
    {"key": "content_updates", "label": "Updates and content",
     "focus": "More frequent content and clearer update plans",
     "pattern": r"\b(?:updates?|patch(?:es)?|seasons?|repetitive|boring|grind\w*|stale|dead game)\b"},
    {"key": "difficulty_controls", "label": "Difficulty and controls",
     "focus": "Difficulty options and control polish",
     "pattern": r"\b(?:difficult\w*|too hard|controls?|camera|clunky|unresponsive)\b"},
    {"key": "balance", "label": "Balance",
     "focus": "Balance changes and clearer patch notes",
     "pattern": r"\b(?:balanc\w*|nerf\w*|buff\w*|meta|overpowered|unfair|op)\b"},
]
PRAISE_THEMES = [
    {"key": "fun_gameplay", "label": "Fun and gameplay",
     "pattern": r"\b(?:fun|addict\w*|enjoy\w*|gameplay|masterpiece|relaxing|cozy|chill)\b"},
    {"key": "story_world", "label": "Story and world",
     "pattern": r"\b(?:story\w*|world|lore|characters?|atmosphere|narrative|quests?|exploration)\b"},
    {"key": "visuals_sound", "label": "Visuals and sound",
     "pattern": r"\b(?:graphics|visuals?|art|music|soundtrack|sound|beautiful|stunning|aesthetic)\b"},
    {"key": "value_price", "label": "Value for money",
     "pattern": r"\b(?:worth|value|cheap|free|bargain)\b"},
]


class GameError(Exception):
    """An error with a message that is safe to show to the user."""


# ---------- Finding the game ----------
def parse_game_input(text):
    """Returns (app_id, None) for a link or number, or (None, name) for a name."""
    text = (text or "").strip()
    match = re.search(r"/app/(\d+)", text)
    if match:
        return int(match.group(1)), None
    if text.isdigit():
        return int(text), None
    return None, text


def search_game(term):
    resp = requests.get(
        "https://store.steampowered.com/api/storesearch/",
        params={"term": term, "l": "english", "cc": "US"},
        timeout=20,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    apps = [i for i in items if i.get("type", "app") == "app"] or items
    if not apps:
        raise GameError('No Steam game was found for "' + term + '". Try pasting the game\'s Steam link instead.')
    return int(apps[0]["id"]), apps[0].get("name") or term


def game_name(app_id):
    try:
        resp = requests.get(
            "https://store.steampowered.com/api/appdetails",
            params={"appids": app_id, "filters": "basic"},
            timeout=20,
        )
        data = resp.json().get(str(app_id), {})
        if data.get("success"):
            return data["data"]["name"]
    except Exception:
        pass
    return "Steam app " + str(app_id)


# ---------- Reading reviews ----------
def get_page(url, params):
    for attempt in range(1, 5):
        try:
            resp = requests.get(url, params=params, timeout=30)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            time.sleep(5 * attempt)
            continue
        if resp.status_code == 429:
            time.sleep(15 * attempt)
            continue
        resp.raise_for_status()
        return resp.json()
    raise GameError("Steam is not answering right now. Wait a minute and try again.")


def fetch_reviews(app_id, target):
    url = "https://store.steampowered.com/appreviews/" + str(app_id)
    reviews, seen, cursor, stale = [], set(), "*", 0
    while len(reviews) < target:
        data = get_page(url, {"json": 1, "language": "english", "filter": "recent",
                              "num_per_page": 100, "cursor": cursor})
        page = data.get("reviews", [])
        if not page:
            break
        before = len(reviews)
        for r in page:
            rid = r.get("recommendationid")
            if rid not in seen:
                seen.add(rid)
                reviews.append(r)
        stale = stale + 1 if len(reviews) == before else 0
        new_cursor = data.get("cursor")
        if stale >= 3 or not new_cursor or new_cursor == cursor:
            break
        cursor = new_cursor
        time.sleep(PAUSE)
    return reviews[:target]


# ---------- Analysis ----------
def excerpt(review, limit=220):
    text = " ".join((review.get("review") or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def theme_block(themes, group):
    out = []
    for t in themes:
        rx = re.compile(t["pattern"])
        hits = [r for r in group if rx.search((r.get("review") or "").lower())]
        usable = [r for r in hits if 30 <= len((r.get("review") or "").strip()) <= 600]
        usable.sort(key=lambda r: -(r.get("votes_up") or 0))
        out.append({
            "key": t["key"],
            "label": t["label"],
            "focus": t.get("focus"),
            "count": len(hits),
            "percent": round(len(hits) / len(group) * 100, 1) if group else None,
            "examples": [excerpt(r) for r in usable[:3]],
        })
    out.sort(key=lambda x: -x["count"])
    return out


def analyze(reviews):
    pos = [r for r in reviews if r.get("voted_up")]
    neg = [r for r in reviews if not r.get("voted_up")]
    return {
        "reviews_read": len(reviews),
        "positive": len(pos),
        "negative": len(neg),
        "percent_positive": round(len(pos) / len(reviews) * 100, 1) if reviews else None,
        "problems": theme_block(PROBLEM_THEMES, neg),
        "praise": theme_block(PRAISE_THEMES, pos),
    }


# ---------- Saved copies, so a repeated search is instant ----------
def cache_path(app_id, n):
    return os.path.join(CACHE_DIR, str(app_id) + "_" + str(n) + ".json")


def read_cache(app_id, n):
    path = cache_path(app_id, n)
    try:
        if time.time() - os.path.getmtime(path) < CACHE_SECONDS:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    return None


def write_cache(app_id, n, result):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_path(app_id, n), "w", encoding="utf-8") as f:
            json.dump(result, f)
    except OSError:
        pass


def run_analysis(query, n, refresh=False):
    if n not in ALLOWED_COUNTS:
        raise GameError("Choose 200, 400 or 1000 reviews.")
    app_id, term = parse_game_input(query)
    name = None
    if term is not None:
        if not term:
            raise GameError("Type a game name, paste a Steam link, or enter a game ID.")
        app_id, name = search_game(term)

    if not refresh:
        cached = read_cache(app_id, n)
        if cached:
            cached["cached"] = True
            return cached

    reviews = fetch_reviews(app_id, n)
    if not reviews:
        raise GameError("Steam returned no English reviews for this game (app " + str(app_id) + ").")
    result = analyze(reviews)
    result["game"] = {"name": name or game_name(app_id), "app_id": app_id}
    result["requested"] = n
    if len(reviews) < min(n, 100):
        result["warning"] = "Steam returned only " + str(len(reviews)) + " English reviews, so treat these numbers as rough."
    elif len(reviews) < n:
        result["warning"] = "Steam returned " + str(len(reviews)) + " reviews, fewer than the " + str(n) + " requested."
    result["ok"] = True
    result["cached"] = False
    write_cache(app_id, n, result)
    return result


# ---------- The web server ----------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("  " + (fmt % args) + "\n")

    def send_bytes(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, obj, status=200):
        self.send_bytes(json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8", status)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/analyze":
            return self.handle_analyze(parse_qs(parsed.query))
        return self.serve_static(parsed.path)

    def handle_analyze(self, params):
        query = (params.get("q") or [""])[0]
        try:
            n = int((params.get("n") or ["400"])[0])
        except ValueError:
            n = 0
        refresh = (params.get("refresh") or ["0"])[0] == "1"
        try:
            self.send_json(run_analysis(query, n, refresh))
        except GameError as e:
            self.send_json({"ok": False, "error": str(e)})
        except requests.exceptions.RequestException as e:
            self.send_json({"ok": False, "error": "Could not reach Steam (" + e.__class__.__name__ + "). Check your internet and try again."})
        except Exception as e:  # keep the server alive whatever happens
            self.send_json({"ok": False, "error": "Something went wrong: " + str(e)})

    def serve_static(self, url_path):
        rel = url_path.lstrip("/") or "index.html"
        full = os.path.normpath(os.path.join(DOCS, rel))
        if not full.startswith(DOCS + os.sep) or not os.path.isfile(full):
            return self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "application/javascript"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as f:
            self.send_bytes(f.read(), ctype)


def main():
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError:
        print("Port", PORT, "is already in use. Close the other preview (Ctrl + C in its terminal) and try again.")
        return
    print("Steam review project is running.")
    print("Open this address in your browser:  http://" + HOST + ":" + str(PORT))
    print("Press Ctrl + C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()