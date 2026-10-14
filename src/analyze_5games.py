import json
import pandas as pd

df = pd.read_csv("data/steam_reviews_5games.csv")
df["review"] = df["review"].fillna("")
df["len"] = df["review"].str.len()
text = df["review"].str.lower()

THEMES = {
    "cheating": r"\b(?:cheat\w*|hack\w*|aimbot\w*|wallhack\w*)",
    "servers_lag": r"\b(?:servers?|lag|laggy|ping|matchmaking|disconnect\w*)\b",
    "bugs_performance": r"\b(?:bugs?|buggy|crash\w*|glitch\w*|fps|stutter\w*|optimi[sz]ation|performance)\b",
}
for name, pattern in THEMES.items():
    df[name] = text.str.contains(pattern, regex=True)

print("Rows:", len(df))
print("Duplicate ids:", df["recommendationid"].duplicated().sum())
print("Empty reviews:", (df["len"] == 0).sum())
print()

per_game = df.groupby("game").agg(
    reviews=("review", "size"),
    percent_positive=("voted_up", lambda s: round(s.mean() * 100, 1)),
    median_length=("len", "median"),
)
print("Per game:")
print(per_game)
print()

med_pos = float(df[df["voted_up"] == True]["len"].median())
med_neg = float(df[df["voted_up"] == False]["len"].median())
print("Median length - positive:", med_pos, "| negative:", med_neg)
print()

neg = df[df["voted_up"] == False]
by_mode = (neg.groupby("mode")[list(THEMES)].mean() * 100).round(1)
print("Percent of NEGATIVE reviews mentioning each theme:")
print(by_mode)

neg_counts = {k: int(v) for k, v in neg.groupby("mode").size().items()}
theme_counts = neg.groupby("mode")[list(THEMES)].sum().astype(int)
print()
print("Number of NEGATIVE reviews per mode:", neg_counts)
print("Number of NEGATIVE reviews mentioning each theme:")
print(theme_counts)

summary = {
    "total_reviews": int(len(df)),
    "per_game": per_game.reset_index().to_dict(orient="records"),
    "median_length_by_sentiment": {"positive": med_pos, "negative": med_neg},
    "negative_theme_percent_by_mode": by_mode.to_dict(orient="index"),
    "negative_reviews_by_mode": neg_counts,
    "negative_theme_counts_by_mode": theme_counts.to_dict(orient="index"),
}
with open("data/summary_5games.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, default=float)
print()
print("Saved data/summary_5games.json")