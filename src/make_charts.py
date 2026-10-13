import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("data/summary.json", encoding="utf-8") as f:
    s = json.load(f)

os.makedirs("charts", exist_ok=True)
GREEN, RED = "#2e7d32", "#c62828"


def save(name):
    plt.tight_layout()
    plt.savefig(f"charts/{name}.png", dpi=150)
    plt.close()


# Chart 1: how many positive vs negative reviews
plt.figure(figsize=(5, 4))
plt.bar(["Positive", "Negative"], [s["positive"], s["negative"]], color=[GREEN, RED])
plt.title("Reviews by recommendation")
plt.ylabel("Number of reviews")
save("reviews_by_recommendation")

# Chart 2: typical (median) review length
plt.figure(figsize=(5, 4))
plt.bar(["Positive", "Negative"],
        [s["median_length"]["positive"], s["median_length"]["negative"]],
        color=[GREEN, RED])
plt.title("Median review length")
plt.ylabel("Characters")
save("median_review_length")

# Chart 3: share of reviews that mention cheating
plt.figure(figsize=(5, 4))
plt.bar(["Positive", "Negative"],
        [s["cheat_mention_percent"]["positive"], s["cheat_mention_percent"]["negative"]],
        color=[GREEN, RED])
plt.title("Reviews that mention cheating")
plt.ylabel("Percent of reviews")
save("cheating_mentions")

# Chart 4: top words in negative reviews
words = s["top_words"]["negative"]
labels = [w for w, c in words][::-1]
counts = [c for w, c in words][::-1]
plt.figure(figsize=(6, 4))
plt.barh(labels, counts, color=RED)
plt.title("Top words in negative reviews")
plt.xlabel("Times used")
save("top_words_negative")

print("Saved 4 charts in the charts folder")