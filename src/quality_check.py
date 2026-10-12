import pandas as pd

df = pd.read_csv("data/steam_reviews.csv")

print("Rows:", len(df))
print("Empty reviews:", df["review"].isna().sum())
print("Duplicate ids:", df["recommendationid"].duplicated().sum())

df["review_length"] = df["review"].fillna("").str.len()
print("Very short (under 10 characters):", (df["review_length"] < 10).sum())
print(df["review_length"].describe())

print("Average length by recommendation:")
print(df.groupby("voted_up")["review_length"].mean())