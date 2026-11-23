# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

My version, **VibeMatch 1.0**, is a small content-based recommender. It loads 18 songs from `data/songs.csv` and scores each one against a user's taste profile: favorite genre, favorite mood, target energy, and whether they like acoustic music. It then prints the top 5 with the reasons behind each score. I tested it on five profiles, including two edge cases, and ran one weight experiment. The biggest finding is that genre is weighted so heavily it can override the mood a user asked for. See the [model card](model_card.md) for the full evaluation.

---

## VibeMatch 2.0: songs for this moment

VibeMatch 2.0 recommends real songs for the moment you're in. You pick a mood picture, an energy level, and what you want from the music, and say where you are. It also uses the weather in your city, the time of day, and (simulated) phone signals: heart rate, notifications, and sleep. A **research-based manual** turns all of that into a target sound. VibeMatch then **retrieves** the 8 closest songs from a 152-song catalog, and Claude picks and orders 5 of them **using only those songs and the matching manual rules**. A check rejects anything Claude names that it wasn't given. With no API key, VibeMatch still works in offline mode.

### What's new compared with 1.0

| | 1.0 | 2.0 |
|---|---|---|
| Songs | 18 made-up songs | 152 real songs from the [Spotify Tracks Dataset](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset) ([how they were picked](data/CATALOG_SOURCE.md)) |
| Input | A fixed profile dict | Mood card, energy, goal, place, weather, time of day, simulated phone signals, optional note |
| Matching | Points for exact genre/mood labels | Distance in (energy, valence, acousticness) space, so near misses still count |
| Knowledge | None | [Music & mood manual](knowledge/music_mood_manual.md): 12 rules, each with evidence level and sources |
| AI | None | RAG: Claude (`claude-haiku-5-5`) picks from the retrieved songs and cites manual rule IDs |
| Interface | Command line | Streamlit page (`app.py`); the 1.0 command line still works |

### How it works

```
your moment (mood card, energy, goal, place, note, weather, time, phone signals)
   │
   ├─► context.py   turns it into coarse labels (low_mood, night, rain, hr_high_resting, …)
   │                and a starting point from what you said
   ├─► manual.py    picks the manual rules that match those labels (always M-00, M-10, M-11)
   │                their nudges move the target point (at most ±0.25 per axis in total)
   ├─► privacy.py   lets only the target sound go to the music source, and only labels go to the AI
   ├─► retrieval.py finds the 8 closest songs (max 1 per artist; songs outside a rule's
   │                preferred tempo/instrumental range rank lower)          ◄── retrieval
   ├─► explainer.py Claude picks and orders 5 of the 8, citing rule IDs     ◄── generation
   │                check: only retrieved songs and matched rules survive; ≥ 3 valid picks or
   │                fall back to offline; at most 2 very sad songs for a low mood; order follows the goal
   └─► app.py       shows the picks, reasons, target, labels, rules, and all 8 candidates
```

**Why this counts as RAG:** Claude never sees the whole catalog. Each request contains only the 8 songs retrieved for this moment and the manual rules that matched it, and the answer is accepted only if it sticks to them. Changing the moment changes what is retrieved, which changes what Claude can recommend.

The three parts most likely to change later are each a small interface: signal sources (phone signals are simulated today), the reasoner (`ClaudeReasoner` today, a local model later, with the template fallback already a second implementation), and the music source (`LocalCatalog` today, Spotify later).

### Guardrails and logging

- **Input checks:** mood card, energy, goal, place, and weather must be known values. Hour 0–23, heart rate 30–220, notifications 0–999, sleep 0–24 h, city ≤ 80 characters, note ≤ 200 characters.
- **Grounding check:** song IDs must be among the 8 retrieved and rule IDs among the matched rules. Duplicates are dropped and reasons are capped at 300 characters. Fewer than 3 valid picks means offline picks.
- **Failures fall back to offline mode:** no key, rejected key, rate limit, timeout, connection error, server error, refusal, cut-off answer, or unreadable JSON. The page always shows songs and says which mode it ran in.
- **Privacy:**

  | Data | Sent to Claude | Sent to the music source | Written to the log |
  |---|---|---|---|
  | Mood card, energy level, goal, place | Yes | No | Yes |
  | Weather category, time of day | Yes | No | Yes |
  | Heart rate, notifications, sleep | Only as labels ("heart rate up") | No | Only as labels |
  | City | No (sent only to Open-Meteo) | No | No |
  | Note text | Yes | No | Length only |
  | Target sound + preferred ranges | Yes | Yes (the only thing it gets) | Yes |

- **Safety:** if the note mentions self-harm or a crisis, the page shows support resources (988 in the US, findahelpline.com elsewhere). It uses offline picks and the note isn't sent anywhere. VibeMatch is not therapy.
- **Logging:** every run writes to `logs/vibematch.log` under a run ID. Each run records the inputs (as categories), labels, rules, nudges, target point, retrieved songs and distances, mode, latency, request ID, rejected IDs, and what the check changed. `tests/test_vibe.py` checks that raw signal numbers and note text never reach the log.

### Setup and run (2.0)

Tested with Python 3.14.6 on macOS.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: turn on AI mode (otherwise the app runs offline with template reasons)
cp .env.example .env               # then paste your Anthropic API key after ANTHROPIC_API_KEY=

streamlit run app.py               # opens http://localhost:8501
```

- **Tests:** `python -m pytest` runs 92 tests with no network access. Weather and Claude are mocked, and the Streamlit page is tested headlessly.
- **Rebuild the catalog (optional, downloads ~20 MB):** `python scripts/build_catalog.py`
- **The 1.0 command-line demo:** `python -m src.main`

Run commands from the project root, because paths like `data/catalog.csv` are relative.

### Sample run (offline mode)

Inputs: **Rainy window**, energy **Low**, goal **Match my mood**, **Home**, **night**, **rainy**, note "nothing too sad, just cozy".

```
labels:  goal_match, home, low_mood, night, rain
rules:   M-00, M-02 wind down, M-05 low mood, M-08 time of day, M-09 weather, M-10, M-11
nudges:  M-02 acoustic +0.05 · M-08 night energy -0.10 · M-09 rain energy -0.10, acoustic +0.15
target:  energy 0.075 · valence 0.25 · acoustic 0.80

1. In The End · Regnør (piano, energy 0.04, valence 0.15, 92 bpm)
2. Préludes / Book 1, L. 117: 8. La fille aux cheveux de lin · Claude Debussy, Jean-Rodolphe Kars (classical, energy 0.01, valence 0.22, 72 bpm)
3. Lonesome Town · Ricky Nelson (r-n-b, energy 0.19, valence 0.27, 77 bpm)
4. The Choice · Gustavo Santaolalla, Alan Umstead (ambient, energy 0.00, valence 0.35, 51 bpm)
5. At Dawn · Ever So Blue (piano, energy 0.03, valence 0.36, 116 bpm)

check: swapped 2 very sad songs for warmer ones (M-05) · reordered so valence steps up (M-10)
```

In AI mode, Claude writes a one-sentence reason for each pick and cites rules such as `M-05, M-09`; the same check then applies.

### Limitations of 2.0

- **AI mode hasn't been run live yet.** It's tested with a fake Claude client. A real run needs an API key, and the quality of `claude-haiku-5-5` at choosing picks and citing rules is unverified. Switching to `claude-opus-5-5` is one line in `src/explainer.py`.
- **Phone signals are simulated.** Real heart rate or notifications would need a phone app (e.g. HealthKit or Health Connect).
- **Small, mainstream catalog:** 152 songs with popularity ≥ 50. The features are Spotify's estimates and some genre labels are odd. Whether Spotify-derived data may be shared is unclear (see [CATALOG_SOURCE.md](data/CATALOG_SOURCE.md)).
- **The manual is a starting point.** Most figures come from abstracts and summaries, the exact nudges are our defaults, and people differ: weather and time affect people differently. Sensed signals mostly show *how worked-up* someone is, not whether they feel good or bad.
- **Not therapy or medical advice.**

---

## VibeMatch 2.1: your prompt and your listening history

In 2.1 you can just type what you want to hear ("rainy night, need to focus, no lyrics"). VibeMatch reads the prompt into the same choices the page offers. It also uses a **listening history** to learn what *you* usually play in moments like this one: this time of day, this weather, this place. The mood cards and the energy, goal, and place controls are now optional. Anything you set yourself wins over the prompt. Each pick has an **Open in Spotify** link.

The histories are **made-up demo data** for three personas (student, gym-goer, night owl). See [HISTORY_SOURCE.md](data/HISTORY_SOURCE.md) for how they were generated and which patterns were planted.

### What's new compared with 2.0

| | 2.0 | 2.1 |
|---|---|---|
| Main input | Mood card (required) + controls + optional note | A typed prompt; the mood card, energy, goal, and place are optional overrides |
| The note / prompt | Only Claude read it, at the last step | It's read **before** retrieval, so it changes which songs are found |
| Memory | None | Demo listening history (song, time, weather, place, finished or skipped) |
| Retrieval | 8 nearest songs | 16 nearest, then re-ranked on the device (familiar songs up, songs you usually skip down, genres you named), keep 8 |
| Spotify | Data source only | "Open in Spotify" link for every pick; optional embedded players |

### How it works

```
prompt ─► crisis check first (a hit means: no Claude, keywords only, support message)
       ─► intent.py   prompt → mood card, energy, goal, place, weather, no lyrics, nothing too sad,
       │              genres to like/avoid   (Claude reads it; keywords when offline or on any failure)
       │              only fills what you left on Auto; every value must be a known choice
history ─► history.py past plays weighted by how much they match now (time of day, weather, place;
       │              weight = matches²) → your usual sound here
       ├─► starting point: your mood card pulled up to 40% toward your usual sound
       │                   (no mood card: start from your usual sound; no history either: the middle)
       ├─► manual rules and nudges, as in 2.0 → target sound
       ├─► retrieval: 16 nearest songs → re-rank on device → 8 candidates
       └─► Claude picks 5 (it also sees a one-line history summary and which candidates you've played)
           → grounding check, as in 2.0 → picks with Spotify links
```

**Why it doesn't need the AI to read every song:** retrieval narrows 152 songs to 8 using plain arithmetic on energy, valence, and acousticness. The prompt and the history move the *target* of that search. Claude only chooses among the 8 it's given. The same setup would work with a catalog of millions.

**How much history counts:** each finished play gets a weight from how many of the three context fields match the moment (1, 4, or 9). The weights are added up and divided by 9, so a play that matches all three counts as one "similar play". With `n` similar plays, history moves your starting point by `0.4 × n / (n + 20)`. So 20 similar plays move it 20% of the way, and it never moves more than 40%. Mood labels such as "low mood" come only from what you say, never from your history.

**Example (offline, prompt "rainy night, need to focus", weather rainy, night):**

| History | Reads as | Target (energy · valence · acoustic) | Top pick |
|---|---|---|---|
| None | goal: focus | 0.30 · 0.50 · 0.65 | The Calm Place |
| Student | 31 similar plays, usually low energy, darker, acoustic | 0.07 · 0.37 · 0.92 | The Choice |
| Gym-goer | 3 similar plays, usually high energy, brighter, electronic | 0.48 · 0.60 · 0.28 | Just the Two of Us |
| Night owl | 23 similar plays, usually darker | 0.20 · 0.30 · 0.72 | The Calm Place (then Weightless) |

### Spotify

Spotify blocked new apps from its Audio Features, Recommendations, Related Artists, and some other Web API endpoints on 27 Nov 2024 ([Spotify's announcement](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api)). Without audio features, Spotify can't tell a new app how energetic or acoustic a song is, so it can't be the engine that finds songs. VibeMatch keeps using the Hugging Face copy of those features for ranking. It uses Spotify only to *play* songs: the catalog now has each song's `track_id`, which gives a link (`open.spotify.com/track/<id>`) and an optional embedded player. No Spotify account, key, or login is needed. I didn't check Spotify's current development-mode or quota rules. They would matter only for a later step that imports your real listening history.

### Privacy in 2.1

| Data | Sent to Claude | Sent to the music source | Written to the log |
|---|---|---|---|
| Prompt text | Yes, to read it and to pick songs (never if it mentions a crisis) | No | Length only |
| What the prompt was read as | Yes | No | Which fields it filled |
| Listening history (plays, times, places) | No | No | No |
| History summary ("23 similar past plays, usually darker") | Yes | No | Play count and strength only |
| Which of the 8 candidates you've played before | Yes (song IDs) | No | No |
| Re-ranking by history and genres | No (done on the device) | No | The re-ranked candidates |
| Spotify players | No | No | No. The toggle is off by default; when on, your browser loads Spotify's player, so Spotify sees which songs are shown |

Everything in the 2.0 table still applies.

### Run it

The setup is the same as 2.0 (`streamlit run app.py`). To regenerate the demo histories, run `python -m scripts.make_demo_history`. `python -m pytest` runs 127 tests with no network: Claude, the prompt reader, and the weather are faked or turned off.

### Limitations of 2.1

- **The histories are synthetic.** The tests show VibeMatch finds the patterns we planted, which says nothing about real listeners.
- **The 40% cap, the `n + 20` curve, and the re-rank amounts are my defaults, not research.**
- **Weather and time can be counted twice.** The manual's weather and time-of-day nudges still apply on top of history that already reflects them. A possible fix is to skip M-08/M-09 when history has enough similar plays.
- **With no mood card, even a few similar plays set the starting point.** For example, the gym-goer has 3 on rainy nights.
- **Keyword reading is shallow.** It catches common phrases and simple negations ("no country", "nothing too sad"). It misses most other phrasing, and "chill" is read as a mood, not the genre.
- **Claude reading the prompt hasn't been run live.** It's tested with a fake client only, as with AI mode in 2.0.
- **The app doesn't learn from new plays or skips yet.** History is read-only.

---

## How The System Works

### How real recommenders work (and what mine does)

Big platforms like Spotify and YouTube mix two ideas. **Collaborative filtering** uses other people's behavior: if listeners who share your history also love a song you haven't heard, it gets suggested to you. **Content-based filtering** uses the songs themselves (genre, mood, tempo, energy, how acoustic they sound) and finds tracks similar to what you already like. Real systems feed in explicit signals (likes, saves, playlist adds), implicit signals (skips, replays, how long you listen), and audio features. They score a huge pool of candidates and then rank the best few. My version is a small **content-based** recommender only. There are no other users to learn from, so it compares each song's attributes to one user's taste profile. It prioritizes **genre** first, **mood** second, and then how **close** the song's energy is to what the user wants.

### Features used

**`Song`**

- `genre`: pop, lofi, rock, etc.
- `mood`: happy, chill, intense, etc.
- `energy`: 0.0 (calm) to 1.0 (intense)
- `acousticness`: 0.0 (electronic) to 1.0 (acoustic)
- `id`, `title`, `artist`: for display only, not scored

`tempo_bpm`, `valence`, and `danceability` are loaded but not scored. In this catalog, tempo and danceability rise and fall with energy (correlations of 0.92 and 0.72), so scoring them would mostly count energy twice.

**`UserProfile`**

- `favorite_genre`
- `favorite_mood`
- `target_energy`: a number from 0.0 to 1.0
- `likes_acoustic`: True or False

### Catalog

`data/songs.csv` has 18 songs: the 10 starter songs plus 8 I added (hip hop, bluegrass, classical, metal, edm, r&b, blues, trip hop) to cover genres and moods the starter file didn't have. Two of them break the "loud means electronic" pattern: *Back Porch Reel* is high energy but acoustic, and *Static Lullaby* is low energy but electronic.

### Default taste profile

```python
user_prefs = {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.8, "likes_acoustic": False}
```

### Algorithm Recipe

**Scoring rule (judges one song):**

| Check | Points |
|---|---|
| Song's genre equals the user's favorite genre | +2.0 |
| Song's mood equals the user's favorite mood | +1.0 |
| Energy closeness: `1 - abs(song energy - target energy)` | 0.0 to +1.0 |
| Acoustic fit: the song is acoustic (acousticness ≥ 0.5) and the user likes acoustic, or the song isn't and the user doesn't | +0.5 |

The highest possible score is 4.5. Every check that adds points also adds a reason, such as `genre match (+2.0)`, so the user can see why a song was picked. Genre is worth twice as much as mood because genre changes the whole sound of a song, while the same mood can show up in any genre. Energy uses closeness instead of "higher is better", so a song that is too intense loses points the same way as a song that is too calm.

**Ranking rule (orders the whole catalog):** score every song, sort from highest to lowest score, and return the top `k` (default 5). Songs with equal scores keep their order from the CSV.

### Data flow

```
User prefs ──► for each song in songs.csv: score_song(prefs, song) → (score, reasons)
           ──► sort every song by score, highest first
           ──► return the top k songs with their scores and reasons
```

### Biases I expect

- **Genre outweighs everything else.** A song in the right genre but the wrong mood can beat a song with the right mood and energy in a nearby genre. In a dry run of the pop/happy profile, *Gym Hero* (pop, intense) came 2nd, ahead of *Rooftop Lights* (indie pop, happy).
- **Exact labels only.** "indie pop" is not "pop", and "chill", "relaxed", and "peaceful" are all different moods. Labels that are close get no credit.
- **Uneven catalog.** Lofi has 3 songs, but 12 of the 15 genres have only one. A lofi fan gets several genre matches. A metal fan gets one, and the rest of their list is filled in by energy alone.
- **Middle-energy users get flatter results.** A user who wants energy 0.5 is never more than 0.47 away from any song in this catalog, while a user who wants 0.95 can be 0.77 away. For middle users, energy separates songs less, so genre decides even more.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output of `python -m src.main` with the default pop/happy profile:

```
Loading songs from data/songs.csv...
Loaded songs: 18

Profile: {'favorite_genre': 'pop', 'favorite_mood': 'happy', 'target_energy': 0.8, 'likes_acoustic': False}

Top recommendations:

1. Sunrise City by Neon Echo (pop, happy)
   Score: 4.48
   Because: genre match (+2.0), mood match (+1.0), energy closeness (+0.98), acoustic fit (+0.5)

2. Gym Hero by Max Pulse (pop, intense)
   Score: 3.37
   Because: genre match (+2.0), energy closeness (+0.87), acoustic fit (+0.5)

3. Rooftop Lights by Indigo Parade (indie pop, happy)
   Score: 2.46
   Because: mood match (+1.0), energy closeness (+0.96), acoustic fit (+0.5)

4. Concrete Crown by Lyric Theory (hip hop, confident)
   Score: 1.48
   Because: energy closeness (+0.98), acoustic fit (+0.5)

5. Night Drive Loop by Neon Echo (synthwave, moody)
   Score: 1.45
   Because: energy closeness (+0.95), acoustic fit (+0.5)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

- **Weight shift (genre 2.0 → 1.0, energy max 1.0 → 2.0):** The pop fan's list improved: *Rooftop Lights* (happy) moved above *Gym Hero* (intense). The "Sad but Hyped" list got worse, because the only sad song dropped out of the top 5. The other three profiles kept the same order. I put the original weights back afterward.
- **Different types of users:** I ran High-Energy Pop, Chill Lofi, and Deep Intense Rock, plus two edge cases: "Sad but Hyped" (edm, sad, energy 0.9) and "Genre Not in Catalog" (k-pop). Users whose preferences all agree got sensible lists. The conflicting user got a euphoric song at #1. The k-pop user, with no genre matches at all, got a more sensible list than the pop fan.
- **Expanding the dataset:** In the starter songs, energy and acousticness were almost perfectly linked (correlation −0.99), so the acoustic preference barely mattered. Adding 8 songs, including a loud acoustic one and a quiet electronic one, brought that down to −0.71, so the acoustic preference now changes the rankings.

Full outputs and profile-by-profile comparisons are in section 7 of the [model card](model_card.md).

---

## Limitations and Risks

- **Tiny, made-up catalog:** 18 songs, and 12 of the 15 genres have only one song.
- **Genre dominates:** A +2.0 genre match can beat a song with the right mood and energy. That's why *Gym Hero* beats *Rooftop Lights* for a happy pop fan.
- **Exact labels only:** "indie pop" gets no credit for "pop", and "chill" gets none for "relaxed".
- **Same songs everywhere:** *Sunrise City*, *Gym Hero*, and *Storm Runner* each appear in 3 of the 5 test lists.
- **Missing signals:** It doesn't use lyrics, language, popularity, or listening history, and each user can have only one favorite genre and mood.

More detail is in section 6 of the [model card](model_card.md).

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

✏️ *Draft. Rewrite in your own words.*

A recommender doesn't "know" music. It turns each song into a few labels and numbers, compares them to labels and numbers describing the user, and adds up points. Ranking is just sorting those totals. What makes it feel smart is the explanation: seeing "genre match (+2.0), mood match (+1.0)" makes a simple sum look like a judgment. Real platforms do the same basic thing at a much bigger scale, adding signals like skips, replays, and what other users with similar taste listen to.

Bias comes in through choices that look harmless. One weight (+2.0 for genre) meant a listener who asked for sad music got a euphoric song first. A catalog where most genres have one song means fans of those genres get worse lists than lofi or pop fans. Exact label matching means anyone whose taste falls between categories, like "indie pop", gets less credit. In a real app, the same kinds of choices could decide which artists get heard and which get buried.



