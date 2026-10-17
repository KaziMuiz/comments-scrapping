import json
import os
import re
from collections import Counter

import pandas as pd

df = pd.read_csv("data/steam_reviews_5games.csv")
df["review"] = df["review"].fillna("")
df["len"] = df["review"].str.len()
df["hours"] = df["playtime_at_review_min"] / 60
text = df["review"].str.lower()

# ---------- The three themes used on the Findings page ----------
THEMES = {
    "cheating": r"\b(?:cheat\w*|hack\w*|aimbot\w*|wallhack\w*)",
    "servers_lag": r"\b(?:servers?|lag|laggy|ping|matchmaking|disconnect\w*)\b",
    "bugs_performance": r"\b(?:bugs?|buggy|crash\w*|glitch\w*|fps|stutter\w*|optimi[sz]ation|performance)\b",
}
for name, pattern in THEMES.items():
    df[name] = text.str.contains(pattern, regex=True)

# ---------- Problem themes (searched in NEGATIVE reviews) for the Action plan ----------
PROBLEM_THEMES = [
    {"key": "cheating", "label": "Cheating",
     "focus": "Stronger anti-cheat and faster bans",
     "pattern": THEMES["cheating"]},
    {"key": "servers_lag", "label": "Servers and lag",
     "focus": "More server capacity and better matchmaking",
     "pattern": THEMES["servers_lag"]},
    {"key": "bugs_performance", "label": "Bugs and performance",
     "focus": "Bug-fix patches and performance optimization",
     "pattern": THEMES["bugs_performance"]},
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

# ---------- Praise themes (searched in POSITIVE reviews) ----------
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

for t in PROBLEM_THEMES:
    df["problem_" + t["key"]] = text.str.contains(t["pattern"], regex=True)
for t in PRAISE_THEMES:
    df["praise_" + t["key"]] = text.str.contains(t["pattern"], regex=True)

STOP_WORDS = {
    "the", "and", "to", "of", "is", "it", "in", "this", "that", "for", "you",
    "with", "but", "on", "be", "are", "have", "was", "not", "its", "my", "so",
    "if", "they", "just", "can", "all", "your", "get", "there", "from", "when",
    "has", "one", "more", "too", "what", "would", "very", "than", "about",
    "only", "out", "like", "it's", "don't", "i'm", "you're", "game", "will",
    "really", "even", "much", "been", "their", "them", "were", "had", "did",
}


def top_words(texts, n=8):
    counts = Counter()
    for t in texts:
        for word in re.findall(r"[a-z']+", t.lower()):
            if word not in STOP_WORDS and len(word) > 2:
                counts[word] += 1
    return [[w, c] for w, c in counts.most_common(n)]


def num(x, digits=1):
    """A number the web page can read (no NaN)."""
    if pd.isna(x):
        return None
    return round(float(x), digits)


def is_neg(frame):
    return frame[frame["voted_up"] == False]


def is_pos(frame):
    return frame[frame["voted_up"] == True]


def theme_stats(frame, themes, prefix):
    n = len(frame)
    out = []
    for t in themes:
        c = int(frame[prefix + t["key"]].sum()) if n else 0
        out.append({"key": t["key"], "count": c, "percent": num(c / n * 100) if n else None})
    return out


# ---------- Checks ----------
print("Rows:", len(df))
print("Duplicate ids:", df["recommendationid"].duplicated().sum())
print("Empty reviews:", (df["len"] == 0).sum())
print("Missing playtime:", df["hours"].isna().sum())
print()

# ---------- Per game ----------
per_game = []
for game_name, g in df.groupby("game", sort=False):
    pos, neg = is_pos(g), is_neg(g)
    per_game.append({
        "game": game_name,
        "mode": g["mode"].iloc[0],
        "reviews": int(len(g)),
        "positive": int(len(pos)),
        "negative": int(len(neg)),
        "percent_positive": num(g["voted_up"].mean() * 100),
        "median_length": num(g["len"].median()),
        "median_length_positive": num(pos["len"].median()),
        "median_length_negative": num(neg["len"].median()),
        "median_hours_positive": num(pos["hours"].median()),
        "median_hours_negative": num(neg["hours"].median()),
        "theme_counts": {k: int(neg[k].sum()) for k in THEMES},
        "top_words_negative": top_words(neg["review"]),
        "problems": theme_stats(neg, PROBLEM_THEMES, "problem_"),
        "praise": theme_stats(pos, PRAISE_THEMES, "praise_"),
    })

print("Per game:")
print(pd.DataFrame(per_game)[["game", "mode", "reviews", "negative", "percent_positive", "median_length"]])
print()

# ---------- Review length ----------
med_pos = num(is_pos(df)["len"].median())
med_neg = num(is_neg(df)["len"].median())
print("Median length - positive:", med_pos, "| negative:", med_neg)
print()

# ---------- Themes by game type ----------
neg_all = is_neg(df)
by_mode = (neg_all.groupby("mode")[list(THEMES)].mean() * 100).round(1)
neg_counts = {k: int(v) for k, v in neg_all.groupby("mode").size().items()}
theme_counts = neg_all.groupby("mode")[list(THEMES)].sum().astype(int)
print("Percent of NEGATIVE reviews mentioning each theme:")
print(by_mode)
print("Number of NEGATIVE reviews per mode:", neg_counts)
print(theme_counts)
print()

# ---------- Hours played ----------
valid = df.dropna(subset=["hours"]).copy()
bins = [0, 10, 100, 1000, float("inf")]
labels = ["Under 10 hours", "10 to 100 hours", "100 to 1,000 hours", "Over 1,000 hours"]
valid["bucket"] = pd.cut(valid["hours"], bins=bins, labels=labels, right=False)
buckets = []
for label in labels:
    b = valid[valid["bucket"] == label]
    negative = int((b["voted_up"] == False).sum())
    buckets.append({
        "label": label,
        "reviews": int(len(b)),
        "negative": negative,
        "percent_negative": num(negative / len(b) * 100) if len(b) else None,
    })
playtime = {
    "buckets": buckets,
    "median_hours": {
        "positive": num(is_pos(valid)["hours"].median()),
        "negative": num(is_neg(valid)["hours"].median()),
    },
    "missing": int(df["hours"].isna().sum()),
}
print("Share of negative reviews by hours played:")
for b in buckets:
    print(" ", b["label"], "-", b["negative"], "of", b["reviews"], "negative (", b["percent_negative"], "%)")
print("Median hours played - positive:", playtime["median_hours"]["positive"],
      "| negative:", playtime["median_hours"]["negative"])
print()

# ---------- Action plan preview ----------
label_of = {t["key"]: t["label"] for t in PROBLEM_THEMES + PRAISE_THEMES}
print("Action plan preview (top problems and praise per game):")
for g in per_game:
    problems = sorted([p for p in g["problems"] if p["count"] > 0], key=lambda p: -p["count"])[:3]
    praise = sorted([p for p in g["praise"] if p["count"] > 0], key=lambda p: -p["count"])[:2]
    print(" ", g["game"], "(" + str(g["negative"]) + " negative reviews)")
    print("    Fix first:", "; ".join(label_of[p["key"]] + " " + str(p["count"]) for p in problems) or "none")
    print("    Praised:  ", "; ".join(label_of[p["key"]] + " " + str(p["count"]) for p in praise) or "none")
print()

# ---------- Save ----------
summary = {
    "total_reviews": int(len(df)),
    "per_game": per_game,
    "median_length_by_sentiment": {"positive": med_pos, "negative": med_neg},
    "negative_theme_percent_by_mode": by_mode.to_dict(orient="index"),
    "negative_reviews_by_mode": neg_counts,
    "negative_theme_counts_by_mode": theme_counts.to_dict(orient="index"),
    "playtime": playtime,
    "themes": {
        "problems": [{"key": t["key"], "label": t["label"], "focus": t["focus"]} for t in PROBLEM_THEMES],
        "praise": [{"key": t["key"], "label": t["label"]} for t in PRAISE_THEMES],
    },
}

targets = ["data/summary_5games.json"]
if os.path.isdir("docs"):
    targets.append("docs/summary_5games.json")
for path in targets:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Saved", path)