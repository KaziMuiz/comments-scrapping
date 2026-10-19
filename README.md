# Steam Review Analysis

**What do players write when they recommend a game, and when they don't?**

This project collects 2000 recent English reviews from five Steam games, studies what players say in positive and negative reviews, and turns the findings into a fix-first list for developers and an expectations guide for new players. It also includes a live tool that runs the same analysis on any Steam game.

Built for a Big Data Analytics assignment.

**Live dashboard:** https://kazimuiz.github.io/comments-scrapping/

The dashboard has these pages: The question, The data, Findings, Action plan, Try any game, Explore, Cautions and Q&A. The published page shows the research. The **Try any game** tool needs the project's Python server (see [Run it yourself](#run-it-yourself)), because GitHub Pages can only host fixed pages.

---

## Why this is useful

A developer cannot read thousands of reviews, and a new player does not want to. This project reads them and shows:

- **For a developer:** which problems come up most in a game's negative reviews, with counts, percentages, a suggested focus and example comments.
- **For a player:** what players praise most and what they complain about most.

The suggestions come from how often players mention each problem. They show where complaints concentrate. They do not prove that fixing a problem would raise ratings.

## Research question and guesses

The question: **do players who recommend a game write about different things than players who don't, and does that differ between multiplayer and single-player games?**

Four guesses were written before looking at the data:

| # | Guess | Result |
|---|---|---|
| 1 | Negative reviews are longer than positive ones | **Supported.** The median negative review has 69.5 characters, against 27 for positive reviews. |
| 2 | Multiplayer players complain about cheating and servers more than single-player players do | **Supported.** Cheating appears in 56 of 242 multiplayer negative reviews (23.1%) against 1 of 70 single-player ones (1.4%). Servers and lag: 24 against 1. |
| 3 | Single-player players complain about bugs and performance more than multiplayer players do | **Inconclusive.** 6 of 70 single-player negative reviews against 11 of 242 multiplayer ones. Too few reviews to call a difference. |
| 4 | Players with more hours played are more likely to leave a negative review | **[FILL IN from the Findings page: supported, not supported or inconclusive, with the numbers shown there]** |

### What the action plan shows

- **Counter-Strike 2:** cheating is the clear leader, in 37 of 102 negative reviews (36%). Price and purchases (8) and servers and lag (4) follow far behind.
- **Apex Legends:** no single problem stands out. Servers and lag, price and purchases, and updates and content are tied at 20 of 140 negative reviews (14%) each.
- **Elden Ring, Cyberpunk 2077 and Stardew Valley:** these games have few negative reviews (38, 27 and 5), so their rankings are rough. The dashboard says so on the page.

Share of reviews that recommend each game in the sample: Stardew Valley 98.8%, Cyberpunk 2077 93.2%, Elden Ring 90.5%, Counter-Strike 2 74.5%, Apex Legends 65.0%.

## Screenshots

![The question page](screenshots/question.png)
![Findings page](screenshots/findings.png)
![Action plan page](screenshots/action-plan.png)
![Try any game page](screenshots/try-any-game.png)

## Data

**Source:** Steam's public review endpoint, `https://store.steampowered.com/appreviews/<game ID>`. It needs no API key.

**Games (400 reviews each):**

| Game | Steam app ID | Type used in the analysis |
|---|---|---|
| Counter-Strike 2 | 730 | multiplayer |
| Apex Legends | 1172470 | multiplayer |
| Elden Ring | 1245620 | single-player |
| Cyberpunk 2077 | 1091500 | single-player |
| Stardew Valley | 413150 | single-player |

The "multiplayer" and "single-player" labels are simplified.

**Collected:** October 2026, the 400 most recent English reviews for each game (`filter=recent`, `language=english`).

**How the collection works**

1. The script asks for 100 reviews at a time and follows Steam's cursor to the next batch.
2. It pauses between requests, and waits and retries if Steam answers "too many requests" or does not answer.
3. Duplicates are removed using each review's unique ID.
4. Each game is saved to its own file as soon as it finishes, so a failure never loses finished work.
5. A game that returns fewer reviews than expected is not saved, so incomplete data never slips in.

**Files**

| File | What it holds |
|---|---|
| `data/steam_reviews_5games.csv` | The main dataset: 2000 reviews |
| `data/games/` | One file per game, as collected |
| `data/summary_5games.json` | The analysis results the dashboard reads |
| `data/steam_reviews.csv` | A first pilot: 2000 Counter-Strike 2 reviews collected with Steam's default ordering |

**Columns:** `game`, `mode`, `recommendationid`, `review`, `voted_up` (recommends the game), `votes_up` (helpful votes), `timestamp_created`, `playtime_at_review_min`.

No usernames or Steam IDs are saved.

**Notes on the collection**

- **Dota 2 was planned first**, but with Steam's default settings it returned almost no reviews, so Apex Legends replaced it. The most-recent filter was then used for every game.
- **The pilot dataset shows how much the collection method matters.** With Steam's default ordering the Counter-Strike 2 sample was about 52% positive and the reviews were much longer. The recent-reviews sample is 74.5% positive.
- **Steam lists this review endpoint as deprecated.** It worked when the data was collected. The saved files keep the results reproducible.

## Method

- **Length:** the median review length (the middle review), because a few very long reviews would pull an average up.
- **Themes:** keyword groups checked in every review.
  - Problems (searched in negative reviews): cheating, servers and lag, bugs and performance, price and purchases, toxic players, updates and content, difficulty and controls, balance.
  - Praise (searched in positive reviews): fun and gameplay, story and world, visuals and sound, value for money.
- **Hours played:** reviews are grouped as under 10 hours, 10 to 100, 100 to 1,000 and over 1,000.
- **The live tool** reads the most recent English reviews for any game (200, 400 or 1000), applies the same themes, and shows counts, percentages and a few short example comments.

## Limitations

- The sample is the most recent reviews, not a random sample of all reviews. It describes what recent reviewers say, not what every player thinks.
- Themes are found by matching keywords. They count mentions, not meaning: "the anti-cheat is great" and "cheaters ruined it" both count as cheating, and a review that only mentions an update can be counted under updates and content.
- Only 312 of the 2000 reviews are negative, and only 70 of those are single-player, so single-player percentages rest on very few reviews.
- The two game types cover two and three games, so some differences may belong to individual games.
- Hours-played groups mix games with very different players, so that pattern describes this sample, not a rule.
- The action plan ranks problems by how often players mention them. It does not show that a fix would raise ratings.
- 2000 reviews is small by big data standards. What carries over is the method: paging with a cursor, removing duplicates, saving checkpoints and summarizing into a small file. With millions of reviews the same steps would run on a distributed tool such as Spark.

## Run it yourself

You need Python and an internet connection.

```
py -m pip install -r requirements.txt
```

**Collect the reviews** (takes several minutes, because the script pauses between requests):

```
py src/steam_multi_scraper.py
```

**Run the analysis** (writes the summary file the dashboard reads):

```
py src/analyze_5games.py
```

**Start the dashboard and the live tool:**

```
py src/app.py
```

Then open http://127.0.0.1:8000 and use the **Try any game** page. Paste a Steam link, a game ID or a game name. Results for a game are saved for six hours in `data/live/`, which Git ignores.

## Project structure

```
src/
  steam_multi_scraper.py   collects 400 reviews for each of five games
  analyze_5games.py        themes, per-game results, hours played, summary file
  app.py                   local server: dashboard plus the live analysis tool
  (earlier scripts)        pilot scraper, quality check, word analysis, charts
docs/                      the dashboard (published with GitHub Pages)
data/                      datasets and results
charts/                    charts from the pilot dataset
```

## Notes

- All reviews are public Steam reviews, collected for coursework. Steam and the game names belong to their owners.
- The scripts pause between requests to stay polite to Steam's servers.
- A Hacker News practice script, `src/hello_api.py`, is left from an early learning step and is not part of the analysis.