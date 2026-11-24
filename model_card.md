# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

---

## 2. Intended Use  

**Goal:** VibeMatch suggests the 5 songs from a small catalog that best fit one listener's taste. It predicts which songs the listener is most likely to enjoy based on each song's genre, mood, energy, and how acoustic it sounds.

**Intended use:** Classroom exploration of how a content-based recommender turns data into ranked suggestions, and where it goes wrong. It assumes a user's taste can be described as one favorite genre, one favorite mood, a target energy level, and whether they like acoustic music.

**Not intended for:** Real listeners or a real music app. The catalog has only 18 made-up songs, the system doesn't learn from listening history, and every user gets the same fixed weights. It also shouldn't be used to decide which artists or genres get promoted, because its biases (see section 6) favor some genres over others.

---

## 3. How the Model Works  

VibeMatch gives every song in the catalog points, then lists the songs with the most points first.

- **Same genre as your favorite:** 2 points.
- **Same mood as your favorite:** 1 point.
- **Energy close to what you want:** up to 1 point. A perfect match gets the full point, and the further the song's energy is from your target, in either direction, the fewer points it gets. A song can be "too intense" just as easily as "too calm".
- **Acoustic fit:** half a point if the song is acoustic and you like acoustic music, or if it isn't and you don't.

The best possible score is 4.5. Each song comes with a list of reasons, like "genre match (+2.0)", so you can see exactly where its points came from.

**Changes from the starter logic:** The starter code returned the first five songs in the file with a placeholder explanation. I added the scoring and ranking, the reasons list, and the acoustic preference. The starter `UserProfile` already had a `likes_acoustic` field, but nothing used it.

---

## 4. Data  

- **Size:** 18 songs in `data/songs.csv`: the 10 starter songs plus 8 I added.
- **Genres and moods:** 15 genres and 14 moods. Lofi has 3 songs, pop has 2, and every other genre has just 1.
- **Features:** Each song has genre, mood, energy, tempo, valence, danceability, and acousticness. VibeMatch scores only genre, mood, energy, and acousticness.
- **What I added:** Songs in hip hop, bluegrass, classical, metal, edm, r&b, blues, and trip hop, with new moods like sad, angry, romantic, and euphoric. Two of them, *Back Porch Reel* and *Static Lullaby*, were picked so that loud songs aren't always electronic and quiet songs aren't always acoustic.
- **Limits:** All songs and numbers are made up. They don't come from real audio analysis.
- **Missing parts of taste:** Lyrics and language, artist popularity, release year, listening history, and the fact that most people like more than one genre. Because most genres have only one song, a fan of anything except lofi or pop runs out of genre matches after a single song.

---

## 5. Strengths  

- **Consistent tastes work well.** When all of a user's preferences point the same way, the results look right. Chill Lofi got three lofi songs, then calm ambient and jazz. Deep Intense Rock got *Storm Runner*, the only rock song, at #1 with a near-perfect score.
- **Opposite listeners get opposite lists.** The High-Energy Pop and Chill Lofi lists share no songs at all.
- **Energy works in both directions.** A calm listener isn't pushed toward loud songs just because loud songs have "higher" numbers.
- **Every score is explained.** When a result looks wrong, like *Gym Hero* for a happy pop fan, the reasons show exactly why it happened.

---

## 6. Limitations and Bias 

The biggest weakness is that genre is worth so much that it can override what the user actually asked for. A genre match alone (+2.0) is worth as much as a perfect mood match and a perfect energy match put together. In the "Sad but Hyped" test, the user asked for sad music and got *Neon Euphoria*, a euphoric EDM track, at #1, while the only sad song in the catalog came 5th. This creates a small filter bubble: users always get their one genre first, and because 12 of the 15 genres have just one song, the rest of the list gets filled with the same few loud songs. *Sunrise City*, *Gym Hero*, and *Storm Runner* each show up in 3 of the 5 test lists. Labels must also match exactly, so a pop fan gets no genre credit for "indie pop".

---

## 7. Evaluation  

### Profiles tested

I ran five profiles through `python -m src.main` and looked at the top 5 for each. Three are "normal" listeners. Two are edge cases meant to trick the scoring.

| Profile | Genre | Mood | Energy | Likes acoustic |
|---|---|---|---|---|
| High-Energy Pop (default) | pop | happy | 0.8 | no |
| Chill Lofi | lofi | chill | 0.35 | yes |
| Deep Intense Rock | rock | intense | 0.9 | no |
| Sad but Hyped (edge case: conflicting) | edm | sad | 0.9 | no |
| Genre Not in Catalog (edge case) | k-pop | happy | 0.8 | no |

```
=== High-Energy Pop ===
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

```
=== Chill Lofi ===
Profile: {'favorite_genre': 'lofi', 'favorite_mood': 'chill', 'target_energy': 0.35, 'likes_acoustic': True}

Top recommendations:

1. Library Rain by Paper Lanterns (lofi, chill)
   Score: 4.50
   Because: genre match (+2.0), mood match (+1.0), energy closeness (+1.00), acoustic fit (+0.5)

2. Midnight Coding by LoRoom (lofi, chill)
   Score: 4.43
   Because: genre match (+2.0), mood match (+1.0), energy closeness (+0.93), acoustic fit (+0.5)

3. Focus Flow by LoRoom (lofi, focused)
   Score: 3.45
   Because: genre match (+2.0), energy closeness (+0.95), acoustic fit (+0.5)

4. Spacewalk Thoughts by Orbit Bloom (ambient, chill)
   Score: 2.43
   Because: mood match (+1.0), energy closeness (+0.93), acoustic fit (+0.5)

5. Coffee Shop Stories by Slow Stereo (jazz, relaxed)
   Score: 1.48
   Because: energy closeness (+0.98), acoustic fit (+0.5)
```

```
=== Deep Intense Rock ===
Profile: {'favorite_genre': 'rock', 'favorite_mood': 'intense', 'target_energy': 0.9, 'likes_acoustic': False}

Top recommendations:

1. Storm Runner by Voltline (rock, intense)
   Score: 4.49
   Because: genre match (+2.0), mood match (+1.0), energy closeness (+0.99), acoustic fit (+0.5)

2. Gym Hero by Max Pulse (pop, intense)
   Score: 2.47
   Because: mood match (+1.0), energy closeness (+0.97), acoustic fit (+0.5)

3. Neon Euphoria by Pulsewave (edm, euphoric)
   Score: 1.45
   Because: energy closeness (+0.95), acoustic fit (+0.5)

4. Iron Verdict by Grave Static (metal, angry)
   Score: 1.43
   Because: energy closeness (+0.93), acoustic fit (+0.5)

5. Sunrise City by Neon Echo (pop, happy)
   Score: 1.42
   Because: energy closeness (+0.92), acoustic fit (+0.5)
```

```
=== Sad but Hyped ===
Profile: {'favorite_genre': 'edm', 'favorite_mood': 'sad', 'target_energy': 0.9, 'likes_acoustic': False}

Top recommendations:

1. Neon Euphoria by Pulsewave (edm, euphoric)
   Score: 3.45
   Because: genre match (+2.0), energy closeness (+0.95), acoustic fit (+0.5)

2. Storm Runner by Voltline (rock, intense)
   Score: 1.49
   Because: energy closeness (+0.99), acoustic fit (+0.5)

3. Gym Hero by Max Pulse (pop, intense)
   Score: 1.47
   Because: energy closeness (+0.97), acoustic fit (+0.5)

4. Iron Verdict by Grave Static (metal, angry)
   Score: 1.43
   Because: energy closeness (+0.93), acoustic fit (+0.5)

5. Empty Station Blues by Hollis Grey (blues, sad)
   Score: 1.43
   Because: mood match (+1.0), energy closeness (+0.43)
```

```
=== Genre Not in Catalog ===
Profile: {'favorite_genre': 'k-pop', 'favorite_mood': 'happy', 'target_energy': 0.8, 'likes_acoustic': False}

Top recommendations:

1. Sunrise City by Neon Echo (pop, happy)
   Score: 2.48
   Because: mood match (+1.0), energy closeness (+0.98), acoustic fit (+0.5)

2. Rooftop Lights by Indigo Parade (indie pop, happy)
   Score: 2.46
   Because: mood match (+1.0), energy closeness (+0.96), acoustic fit (+0.5)

3. Concrete Crown by Lyric Theory (hip hop, confident)
   Score: 1.48
   Because: energy closeness (+0.98), acoustic fit (+0.5)

4. Night Drive Loop by Neon Echo (synthwave, moody)
   Score: 1.45
   Because: energy closeness (+0.95), acoustic fit (+0.5)

5. Storm Runner by Voltline (rock, intense)
   Score: 1.39
   Because: energy closeness (+0.89), acoustic fit (+0.5)
```

### Why "Gym Hero" keeps showing up for Happy Pop listeners

*Gym Hero* is labeled "pop", and the recommender gives 2 points just for matching the genre. That's twice what it gives for matching "happy". *Gym Hero* is an intense workout song, not a happy one, but its pop label alone is worth more than *Rooftop Lights*' happy mood, because *Rooftop Lights* is labeled "indie pop" and gets no genre credit. So the system decides "pop, wrong mood" is a better fit than "happy, almost pop". Most people would disagree.

### Why a song ranked first: *Neon Euphoria* for "Sad but Hyped"

*Neon Euphoria* scored 3.45: +2.0 for being EDM, +0.95 because its energy (0.95) is very close to 0.9, and +0.5 for not being acoustic. The only sad song, *Empty Station Blues*, scored just 1.43: +1.0 for the mood, but only +0.43 for energy (0.33 is far from 0.9) and nothing for acoustic fit, because it is an acoustic song. The genre bonus alone was bigger than everything the sad song earned.

### Comparing the profiles

- **High-Energy Pop vs. Chill Lofi:** The lists share no songs. Pop gets upbeat electronic songs near 0.8 energy, and lofi gets quiet acoustic songs near 0.35. This makes sense because all four preferences flip.
- **High-Energy Pop vs. Deep Intense Rock:** Both lists have *Gym Hero* at #2, for different reasons. The pop fan gets it for the genre, the rock fan for the "intense" mood. Both users want loud, non-acoustic music, so their lists overlap.
- **High-Energy Pop vs. Sad but Hyped:** Both want high energy, but the pop fan's top songs are actually happy, while the sad fan's #1 is euphoric. When the mood can't be matched, the genre and energy points take over.
- **High-Energy Pop vs. Genre Not in Catalog:** These two profiles differ only in genre. Without the +2.0 pop bonus, *Gym Hero* drops off the list and *Rooftop Lights* moves up to #2. This shows the genre bonus is the only thing keeping *Gym Hero* near the top for the pop fan.
- **Chill Lofi vs. Deep Intense Rock:** The lists share no songs and sit at opposite ends of the energy scale (0.28 to 0.42 for lofi, 0.82 to 0.97 for rock). This is what you'd expect from opposite listeners.
- **Chill Lofi vs. Sad but Hyped:** The lofi list holds together well because genre, mood, energy, and acoustic preference all point the same way. The sad fan's preferences pull against each other, so their list is a mix of songs that each match only one thing.
- **Chill Lofi vs. Genre Not in Catalog:** The lofi fan gets three genre matches because lofi has the most songs, and the top score is 4.50. The k-pop fan gets none, and the top score is 2.48. How good your list can be depends on how many songs your genre has.
- **Deep Intense Rock vs. Sad but Hyped:** Four of the five songs are the same in both lists (*Storm Runner*, *Gym Hero*, *Neon Euphoria*, *Iron Verdict*), because both users want energy 0.9 and nothing acoustic. The genre match decides which of them is #1: *Storm Runner* for rock, *Neon Euphoria* for EDM. Past the genre match, energy is doing almost all the work.
- **Deep Intense Rock vs. Genre Not in Catalog:** After *Storm Runner*, the rock list is a grab bag of loud songs (pop, edm, metal) that only match on energy. The k-pop list at least keeps "happy" songs in its top 2, because mood is the strongest signal left.
- **Sad but Hyped vs. Genre Not in Catalog:** Neither user has a perfect song. The sad fan's genre exists, so the +2.0 pushes a euphoric song to #1. The k-pop fan's genre doesn't exist, so mood decides and the list feels more reasonable. Oddly, having your genre in the catalog made the result worse here.

### What surprised me

- The k-pop listener, whose favorite genre isn't in the catalog at all, got a more sensible list than the pop listener.
- For "Sad but Hyped", the only sad song came last in the top 5, behind three songs that aren't sad at all.
- Three songs (*Sunrise City*, *Gym Hero*, *Storm Runner*) each appeared in 3 of the 5 lists.

For the Chill Lofi profile the results feel right: two chill lofi tracks, then a focused lofi track, then ambient and jazz. That's what I'd want for studying. The High-Energy Pop list feels a little off, because *Gym Hero* at #2 is a workout song, not a happy one.

### Experiment: weight shift (genre halved, energy doubled)

I changed genre from +2.0 to +1.0 and the energy maximum from +1.0 to +2.0, then reran all five profiles. The highest possible score stays 4.5 (1.0 + 1.0 + 2.0 + 0.5). Every song still scored between 0.56 and 4.50, so the math stayed valid. Afterward I put the original weights back.

| Profile | Original top 5 | Experiment top 5 | Better or just different? |
|---|---|---|---|
| High-Energy Pop | Sunrise City, **Gym Hero**, **Rooftop Lights**, Concrete Crown, Night Drive Loop | Sunrise City, **Rooftop Lights**, **Gym Hero**, Concrete Crown, Night Drive Loop | **Better.** The happy song now beats the intense one. |
| Sad but Hyped | Neon Euphoria, Storm Runner, Gym Hero, Iron Verdict, **Empty Station Blues** | Neon Euphoria, Storm Runner, Gym Hero, Iron Verdict, **Sunrise City** | **Worse.** The only sad song dropped out and a happy song took its place. |
| Chill Lofi, Deep Intense Rock, Genre Not in Catalog | (same order in both runs) | (same order in both runs) | **Same.** Only the scores changed. |

Making energy stronger fixed the *Gym Hero* problem for the pop fan, but it hurt the user whose mood and energy disagree, because energy now outweighs mood even more. The change made the results different, not better overall. Each profile needs a different balance, which a single set of weights can't give everyone.

---

## 8. Future Work  

1. **Partial credit for related labels.** Group genres and moods into families (pop and indie pop; chill, relaxed, and peaceful) and give partial points for a near match, so a near miss isn't scored like a total miss. Also let users pick more than one favorite genre.
2. **Weights that fit the user.** The experiment showed that one set of weights can't work for everyone: halving genre helped the pop fan but hurt the "Sad but Hyped" fan. Learning weights from each user's likes and skips would fix that better than any fixed numbers.
3. **More variety in the top 5.** Limit how many songs from one genre or artist can appear, so the same few loud songs (*Gym Hero*, *Storm Runner*) don't fill every high-energy list.

---

## 9. Personal Reflection  

**Biggest learning moment:** Seeing "Sad but Hyped" get a euphoric song at #1. I chose the weights thinking genre was the strongest signal, but I hadn't thought about what happens when a user's genre exists and their mood doesn't. One number (+2.0) decided what that user heard.

**How AI helped, and when I had to double-check:** The AI assistant helped me research how real platforms recommend music, generate new songs for the CSV, write the scoring code, and come up with edge-case profiles I wouldn't have thought of. I still had to check its work. When it analyzed the starter data, it found that acousticness and energy were almost perfectly linked (−0.99), so the acoustic preference would barely matter until we added songs that broke that pattern. It also wrote one comparison in this model card that didn't match the real output. That was caught only because every claim was checked against a fresh run before committing. The lesson for me: always compare the AI's description of results to the actual results.

**What surprised me:** How much four simple rules can feel like a real recommendation. The reasons ("genre match, mood match, energy close") make it seem thoughtful, even though the system knows nothing about music. I was also surprised that the k-pop user, whose genre isn't in the catalog at all, got a more sensible list than the pop fan.

**How it changed how I see music apps:** Now when an app keeps suggesting the same kind of song, I wonder which weight is doing it.

**What I'd try next:** Add partial credit for related genres and moods, then add a simple collaborative filter using a few made-up users' likes, to see how the lists change compared to content alone.

---

## 10. VibeMatch 2.0 (context-aware, RAG)

Sections 1–9 describe VibeMatch 1.0. This section covers 2.0, which runs in `app.py`; the 1.0 command-line app is unchanged.

**Intended use.** A class project that shows how an AI can recommend music for the moment you're in, while keeping personal data on your device. It's for exploring and learning, not for real listeners' wellbeing. It is **not therapy or medical advice**, and its phone signals are simulated.

**How it works.**
1. Your moment (mood card, energy level, goal, place, weather, time of day, simulated heart rate, notifications, and sleep) becomes coarse labels and a starting point.
2. Rules from the [music & mood manual](knowledge/music_mood_manual.md) that match those labels nudge the point by at most ±0.25 per axis.
3. The 8 closest of 152 real songs are retrieved.
4. Claude (`claude-haiku-5-5`) picks and orders 5 of them, citing rule IDs.
5. A check keeps only retrieved songs and matched rules, caps very sad songs at 2 for a low mood, and orders the set along the goal.
6. If anything fails, template reasons are used instead.

**Data.** 152 songs from the Spotify Tracks Dataset on Hugging Face: 18 genres, popularity ≥ 50, 38 songs per valence/energy quadrant, seed 42. See [CATALOG_SOURCE.md](data/CATALOG_SOURCE.md). The features (energy, valence, acousticness, instrumentalness) are Spotify's model estimates.

**The manual and its evidence.** 12 rules, each labeled `strong`, `moderate`, `limited`, or `design rule`, with sources.
- Strong: music lowers stress (de Witte et al. 2020).
- Moderate:
  - sleep music at 60–80 bpm
  - lyrics hurting focus (Vasilev et al. 2018)
  - 120–140 bpm for workouts
  - short sleep lowering mood (Palmer et al. 2024)
  - time-of-day and weather effects that are small and personal (Golder & Macy 2011; Denissen et al. 2008; Klimstra et al. 2011)
- Limited: how to handle low mood (Garrido & Schubert 2013) and tension (Sharman & Dingle 2015).
- Most figures were taken from abstracts and summaries, not full papers.

**Evaluation.**
- 93 automated tests at the time (128 after 2.1), with no network. They cover rule parsing and matching, the worked example (target energy 0.075, valence 0.25, acoustic 0.80), privacy allow-lists, retrieval, the weather code mapping and failures, the grounding check (unknown song and rule IDs rejected, fewer than 3 valid picks falls back), and the full pipeline for rainy night, gym, focus, high resting heart rate, and crisis notes.
- The tests also check that the logs never contain raw signals or note text, and that the Streamlit page works in a headless run.
- One live Open-Meteo call (Boston) matched the code's expectations.
- **When 2.0 was written, AI mode had not been run against the real Claude API.** Section 12.1 reports the live runs since.

**What tuning showed.** At first, songs outside a preferred range lost a flat 0.15. In the focus scenario that left only 1 instrumental song among the 8 candidates, so Claude couldn't follow the "avoid lyrics" rule. Raising the flat penalty fixed focus but broke calming: songs with energy up to 0.56 got in just because their tempo was in range. A penalty that grows with *how far* outside the range a song falls fixed both. Focus got 4 of 8 instrumental, and the calm set stayed at energy 0.24–0.38.

**Biases and risks.**
- "Rain means mellow" and similar nudges are defaults that won't fit everyone. Some people feel better in the rain.
- Popularity ≥ 50 favors mainstream artists.
- Some genre labels in the dataset are odd.
- Sensed signals mostly show *how worked-up* someone is, not whether they feel good or bad, so the system relies on what you say.
- Emotion inference is error-prone in general (EU AI Act, Recital 44). The page shows every label and rule it used so you can see and override them.

**Privacy.**
- Raw signals, the city, and the exact hour never reach Claude or the music source.
- Claude sees coarse labels, your choices, and your note.
- The music source sees only the target sound.
- If a note mentions self-harm or a crisis, the app shows support resources (988 in the US), uses offline picks, and doesn't send the note anywhere.

## 11. VibeMatch 2.1 (prompt + listening history)

**What changed.**
- The typed prompt is now the main input. It's read into the page's own choices (mood card, energy, goal, place, weather) plus "no lyrics", "nothing too sad", and genres to like or avoid. Claude reads it, with keyword matching as the fallback.
- A listening history (song, time, weather, place, finished or skipped) pulls the starting point toward what this listener usually plays in a similar moment, by at most 40%.
- Retrieved songs are re-ranked on the device: familiar songs move up, songs this listener usually skips move down, and named genres move up or down.
- Each pick links to Spotify through the `track_id` now kept in the catalog.

**Data.** The three listening histories (student, gym-goer, night owl; 925 plays over six weeks) are synthetic. They come from planted habits, seed 42 ([HISTORY_SOURCE.md](data/HISTORY_SOURCE.md)). The catalog is unchanged apart from the new `track_id` column. A diff confirmed the 152 songs and every other value are identical.

**Evaluation.**
- 128 automated tests in total, with no network.
- The new tests check:
  - The history recovers the planted patterns: student rainy nights at energy < 0.3 and acoustic > 0.7, more acoustic than sunny nights; gym evenings at energy > 0.7.
  - History strength is 0 with no similar plays and grows with more of them, but stays under 40%.
  - The re-rank bonus and penalties work.
  - The same prompt and moment give each persona different picks.
  - The keyword reader handles negation ("nothing too sad" isn't a sad mood; "no country" avoids country).
  - Claude's reading is limited to known values and falls back to keywords on any error.
  - Your own settings win over the prompt.
  - Crisis prompts never reach either reader's AI path.
  - Logs hold neither the prompt text nor the play history.
- **This evaluation is partly circular.** It shows the code finds patterns we put there, not that real listeners have them.
- Claude reading the prompt has had 4 live runs, but those prompts were 3–13 characters and filled none of the settings, so it is still effectively untested live.

**What tuning showed.** At first each play was weighted by its match count (1–3). Plays that shared only the place ("home") then drowned out the weather: the student's rainy nights and sunny nights came out almost the same (acoustic 0.72 vs 0.66). Squaring the weight (1, 4, 9) separated them (acoustic 0.79 vs 0.66, energy 0.26 vs 0.36).

**Biases and risks.**
- History reinforces habits. A listener who always plays sad songs on rainy afternoons gets more of them, and familiar songs get a bonus. The manual's set rules (at most 2 very sad songs for a low mood or "nothing too sad") still apply. The 40% cap keeps what you say in charge.
- The manual's weather and time nudges apply on top of history that already reflects them.
- With no mood card, a handful of loosely similar plays can set the starting point.
- The keyword reader understands only common English phrases.

**Privacy.**
- The history never leaves the device.
- Claude sees a one-line summary ("23 similar past plays, usually darker") and which of the 8 candidates were played before.
- The music source still sees only the target sound, because re-ranking happens locally.
- Spotify players are off by default. When they're on, the browser loads Spotify's player, so Spotify sees which songs are shown.

---

## 12. Reflection and Ethics (VibeMatch 2.0 and 2.1)

Sections 1–9 reflect on 1.0. This section answers the final-project questions for 2.0 and 2.1. The facts and figures were checked against the code, the tests, `python -m src.demo`, and the live runs in `logs/vibematch.log`.

### 12.1 Limitations and biases

- **AI mode has only 5 live runs, and nobody has rated them.** The log holds 5 runs of the Streamlit page with a real key (1 on 2.0, 4 on 2.1). Each returned 5 picks from the 8 retrieved songs and cited only matched rules, but nobody has judged whether the picks fit the moment. The reasons Claude writes aren't logged or checked. Every run is in [assets/live_runs.md](assets/live_runs.md).
- **The grounding check verifies IDs, not words.** It guarantees that every song and rule Claude names was in its input. A reason sentence could still describe a song wrongly (for example, call a song acoustic when it isn't), and the check wouldn't catch it.
- **Fewer than 5 songs can come back.** The check accepts 3 or more valid picks. When a simulated AI answer named one song that wasn't retrieved, the listener got 4 songs, not 5.
- **The crisis check is a keyword list.** It has 11 English phrases, so it misses paraphrases and other languages, and quoting a lyric could set it off. It correctly ignores "die hard fan of jazz", but no list catches everything.
- **The catalog has gaps and leans mainstream.** It has 152 songs, all with popularity ≥ 50, so less-known artists are left out. Only 4 songs have energy ≥ 0.9, so a maximum-energy workout tops out at 0.91. The features are Spotify's model estimates, and some genre labels are odd.
- **The manual's defaults won't fit everyone.** The nudge sizes are hand-set. "Rain means mellow" and "night means quieter" come from small effects that differ from person to person, and some people want the opposite.
- **Signals show arousal, not feeling.** A high heart rate says someone is worked up, not whether they're excited or anxious, so the system relies on the mood card the listener picks.

See also "Biases and risks" in sections 10 (2.0) and 11 (2.1).

### 12.2 Could VibeMatch be misused, and how would I prevent it?

| Misuse | What already prevents it | What I'd add before real users |
|---|---|---|
| Using inferred mood to target people when they're low (ads, "keep listening" nudges) | Raw signals never leave the device, and Claude sees only coarse labels. There's no engagement goal, only the goal the listener picks. Every label and rule is shown on the page. | A written promise that labels are never stored, sold, or used for ads, and a "delete my data" control |
| Treating VibeMatch as a mental-health tool | The crisis check shows 988 and findahelpline.com and skips the AI for those notes. Every page says it is not therapy. | A better crisis classifier, with the keyword list kept as a backstop, reviewed by someone with clinical expertise |
| Prompt injection through the note ("ignore your rules…") | The system prompt treats the note as a preference, not an instruction. Output is structured JSON, every song and rule ID must come from the input (README guardrail row 6), and reasons are capped at 300 characters. | Check reason text against the song's features, and filter unsafe text before it is shown |
| Building a profile of someone from the logs | Logs hold categories and the note's length only, never raw signals, the city, or note text (tested). `logs/` is gitignored. | A retention limit and log rotation |
| Running up API costs with a leaked key | The key lives in `.env`, which is gitignored. Each request has a 20 s timeout and at most 2 retries. | Per-user rate limits and a spending cap, if it were ever deployed |

### 12.3 What surprised me while testing reliability

- **Retrieval did exactly what I asked, and that was wrong for the person.** For a low mood on a rainy night, 4 of the 5 songs nearest to the target were very sad (valence under 0.25). Without the M-05 rule in code, a listener who wrote "nothing too sad" would have got mostly very sad songs.
- **Fixing one scenario broke another.** A bigger flat penalty fixed the focus scenario but let louder songs into the calm one. Only a penalty that grows with distance fixed both (section 10, "What tuning showed").
- **A guardrail changed the size of the answer.** When a simulated AI answer made up one song ID, the check dropped it correctly, but the listener then saw 4 songs instead of 5.
- **The hardest crisis test was the false positive.** Making sure "die hard fan of jazz" does *not* trigger the support message mattered as much as catching "I want to die".
- **Live, Claude didn't just take the closest songs, and the grounding check never fired.** In 4 of 5 live runs it chose the 7th or 8th of the 8 candidates, and it never named a song or rule it wasn't given. The only correction the code made live was to the order: once, it reordered Claude's set so energy steps up (M-10).

### 12.4 Collaboration with AI

**How I used AI.** I built VibeMatch 2.0 and 2.1 with Claude Code (Claude Opus 5.5) as a pair programmer. Every 2.0 and 2.1 commit has a `Co-Authored-By: Claude Opus 5.5` line.
- **Design.** I pasted the assignment and asked for directions. Claude offered three: a RAG concierge, an agentic playlist builder, and an evaluation-only system. I picked RAG and then pushed the idea further myself: mood picture cards, weather, place, and time; a "personal AI engine" that knows my data while the music platform doesn't; and a manual the AI reviews before every pick. Before approving the plan, I reviewed it in Lavish over three rounds.
- **Research.** I asked Claude to search for what affects emotions and what music helps. That became the manual's 12 rules, each with an evidence level and sources.
- **Code, tests, and docs.** Claude wrote the modules, their tests, and the docs, and in 2.1 the prompt reader and the listening history.
- **Checking.** I checked its work by running the tests and the demo, comparing what the docs claimed with real output, and running the page in AI mode.

For 1.0, I used an AI assistant to research recommenders, add songs, and write the scoring code (section 9). I kept it to the assignment: I told it not to do anything the assignment didn't ask for. When it added songs, I asked whether the assignment called for that. It did (Phase 2), and Claude pointed out the one choice that was its own: two songs picked to break the "loud means electronic" pattern.

**Suggestions I accepted**
- **Enforcing my privacy rule in code.** The rule came from me: "The AI engine will know all my data, but a music streaming platform such as spotify, will not know the exact personal data." Claude turned it into allow-lists in `privacy.py`. Each destination gets a fixed list of fields, and any other field raises an error. I accepted this because it enforces my requirement that personal data stays with the engine, and the tests check it.
- **Scaling back my first idea.** I first wanted live Spotify data and automatic location. Claude checked and pushed back: Spotify had closed its audio-features endpoints to new apps, and automatic location isn't reliable. It suggested a public dataset of real songs and a typed-in city, and I accepted that smaller scope. The same finding shaped 2.1: VibeMatch links to and embeds Spotify tracks but never calls Spotify's API.

**Suggestions I revised**
- **How the work was committed.** Claude built all of 2.0 before committing anything. I asked for "one [commit] for each of the dev progress you have made… such that when AI want to make changes in a certain part, it will know which particular commit made a certain error and what to look for." Claude then split the work into 12 commits, each tested on its own, and 2.1 followed the same rule (9 commits).
- **Reviewing the plan before building.** When Claude first asked me to approve its plan, I turned it down so I could review it in Lavish. My comments there changed the design: they added the personal-engine privacy layer and the research manual.

Claude also corrected itself once. Its first retrieval design gave songs outside a preferred range a flat 0.15 penalty, and its own focus test showed that this left only 1 instrumental song among 8 candidates. It changed the penalty to grow with distance (section 10). The tests caught this, not me. In 1.0, a profile comparison the AI wrote didn't match the real output; checking every claim against a fresh run caught it (section 9).

### 12.5 Future improvements

1. **Rate the live picks.** Run the three demo moments, the guardrail cases, and some real prompts in AI mode, then have a few people rate the picks in a table: does each song fit the moment, and would they skip any? Log Claude's reasons so they can be checked too.
2. **Check Claude's reasons, not just its IDs.** Reject a reason that contradicts the song's features, such as "acoustic" for a song with acousticness under 0.5.
3. **Top up to 5 songs** from the retrieved candidates when the grounding check drops some.
4. **Replace the crisis keyword list** with a classifier that handles paraphrases and other languages, and keep the list as a backstop.
5. **Learn the nudges for each listener** from likes and skips, instead of one default for everyone.
6. **Use real signals and a bigger catalog** through the existing interfaces: phone signals read on the device, and a Spotify `MusicSource`.
