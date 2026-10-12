import json
import re
from collections import Counter
import pandas as pd

df = pd.read_csv("data/steam_reviews.csv")
df["review"] = df["review"].fillna("")
df["len"] = df["review"].str.len()
df["cheat"] = df["review"].str.lower().str.contains("cheat")
dates = pd.to_datetime(df["timestamp_created"], unit="s")

STOP_WORDS = {"the", "and", "to", "of", "is", "it", "in", "this", "that", "for",
              "you", "with", "but", "on", "be", "are", "have", "was", "not",
              "its", "my", "so", "if", "they", "just", "can", "all", "your",
              "get", "there", "from", "when", "has", "one", "more", "too",
              "what", "would", "very", "than", "about", "only", "out", "like",
              "it's", "don't", "i'm", "you're", "game", "will"}

def top_words(texts, n=10):
    counts = Counter()
    for text in texts:
        for word in re.findall(r"[a-z']+", text.lower()):
            if word not in STOP_WORDS and len(word) > 2:
                counts[word] += 1
    return counts.most_common(n)

pos = df[df["voted_up"] == True]
neg = df[df["voted_up"] == False]

summary = {
    "game": "Counter-Strike 2 (Steam app 730)",
    "total_reviews": int(len(df)),
    "positive": int(len(pos)),
    "negative": int(len(neg)),
    "date_from": str(dates.min().date()),
    "date_to": str(dates.max().date()),
    "median_length": {"positive": float(pos["len"].median()),
                      "negative": float(neg["len"].median())},
    "cheat_mention_percent": {"positive": round(float(pos["cheat"].mean() * 100), 1),
                              "negative": round(float(neg["cheat"].mean() * 100), 1)},
    "top_words": {"positive": top_words(pos["review"]),
                  "negative": top_words(neg["review"])},
}

with open("data/summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("Saved data/summary.json")