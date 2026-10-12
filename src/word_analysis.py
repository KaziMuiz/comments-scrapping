import re
from collections import Counter
import pandas as pd

df = pd.read_csv("data/steam_reviews.csv")

STOP_WORDS = {"the", "and", "to", "of", "is", "it", "in", "this", "that", "for",
              "you", "with", "but", "on", "be", "are", "have", "was", "not",
              "its", "my", "so", "if", "they", "just", "can", "all", "your",
              "get", "there", "from", "when", "has", "one", "more", "too",
              "what", "would", "very", "than", "about", "only", "out", "like",
              "it's", "don't", "i'm", "you're", "game", "will", "will"}

def top_words(texts, n=10):
    counts = Counter()
    for text in texts.fillna(""):
        for word in re.findall(r"[a-z']+", text.lower()):
            if word not in STOP_WORDS and len(word) > 2:
                counts[word] += 1
    return counts.most_common(n)

print("Top words in POSITIVE reviews:")
print(top_words(df[df["voted_up"] == True]["review"]))

print("Top words in NEGATIVE reviews:")
print(top_words(df[df["voted_up"] == False]["review"]))