import requests

URL = "https://store.steampowered.com/appreviews/730"
params = {"json": 1, "language": "english", "num_per_page": 100, "cursor": "*"}

response = requests.get(URL, params=params, timeout=10)
data = response.json()

print("Cursor for next page:", data["cursor"])
print("Reviews received:", len(data["reviews"]))

first = data["reviews"][0]
print("Fields in one review:", list(first.keys()))
print("Recommended?:", first["voted_up"])
print("Text:", first["review"][:100])