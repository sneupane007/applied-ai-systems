# Live AI-mode runs

These are the 5 times VibeMatch ran in AI mode with a real Anthropic API key, all from the Streamlit page (`streamlit run app.py`). They are copied from `logs/vibematch.log`, which is gitignored, with only the Anthropic request IDs removed. The log never holds raw phone signals, the city, the prompt or note text, or individual plays, so nothing else needed removing.

Claude's answers vary from run to run, so these runs can't be reproduced exactly. To make new ones, put a key in `.env` (see [Setup and run](../README.md#setup-and-run)), run `streamlit run app.py`, and read `logs/vibematch.log`. The offline samples in the README do reproduce exactly with `python -m src.demo`.

## Summary

| Run | When | Code | Picks that were among the 8 retrieved | Where the picks ranked among the 8 | Song or rule IDs rejected | Claude call | Check notes |
|---|---|---|---|---|---|---|---|
| `0e7354bb` | 2026-11-22 23:15 | 2.0 | 5 of 5 | 1, 2, 3, 4, 5 | none | 6.5 s | — |
| `5b355ddc` | 2026-11-23 14:21 | 2.1 | 5 of 5 | 1, 2, 3, 5, 7 | none | 11.0 s | — |
| `043766da` | 2026-11-23 14:30 | 2.1 | 5 of 5 | 1, 2, 4, 5, 7 | none | 3.1 s | Reordered so energy steps up (M-10). |
| `36630dec` | 2026-11-23 14:38 | 2.1 | 5 of 5 | 1, 2, 4, 5, 7 | none | 7.0 s | — |
| `e4595b76` | 2026-11-23 15:30 | 2.1 | 5 of 5 | 1, 2, 3, 4, 8 | none | 5.4 s | — |

- **Grounded every time.** All 5 runs returned 5 picks, every pick was one of the 8 retrieved songs, every cited rule was one of the matched rules, and the log has no `rejected` line.
- **Not just the nearest songs.** In 4 of the 5 runs Claude picked the 7th or 8th candidate.
- **The set rules ran in code once.** In run `043766da` the code reordered Claude's set so energy steps up (M-10).
- **The prompt reader barely got tested.** In the 4 runs on 2.1, Claude read the prompt (`prompt=ai`), but the prompts were 3–13 characters and filled none of the settings (`from_prompt=[]`).
- **Nobody has rated these picks.** The log shows that they were grounded, not that they fit the moment.

## Each run

### `0e7354bb` · 2026-11-22 23:15 · 2.0 code

- **Moment:** Open road · energy Low · Match my mood · Home · morning · weather sunny · a 6-character note
- **Listening history:** none (2.0 had no history)
- **Labels:** clear, goal_match, home, morning
- **Matched rules:** M-00, M-08, M-09, M-10, M-11
- **Claude call:** 6546 ms

| # | Song | Genre | Rank among the 8 retrieved | Rules Claude cited |
|---|---|---|---|---|
| 1 | Beautiful Soul · Boyce Avenue | acoustic | 1 | M-10, M-00, M-11 |
| 2 | Talk It Out · dwsdmusic | chill | 2 | M-10, M-00, M-08 |
| 3 | Rocky Mountain High · John Denver | folk | 3 | M-10, M-00, M-09 |
| 4 | I Want You To Love Me · Fiona Apple | piano | 4 | M-10, M-00 |
| 5 | You're Still The One · Shania Twain | country | 5 | M-10, M-00, M-08 |

### `5b355ddc` · 2026-11-23 14:21 · 2.1 code

- **Moment:** mood card on Auto · energy Okay · Lift me up · Work / study · afternoon · weather sunny · a 13-character prompt, read by Claude, that filled no settings
- **Listening history:** demo persona `student`, strength 0.257
- **Labels:** afternoon, clear, goal_lift, work_study
- **Matched rules:** M-00, M-03, M-09, M-10, M-11
- **Claude call:** 10955 ms

| # | Song | Genre | Rank among the 8 retrieved | Rules Claude cited |
|---|---|---|---|---|
| 1 | The Calm Place · Zmeyev, Screen Jazzmaster, DreamBetter | chill | 5 | M-00, M-03, M-10 |
| 2 | Just the Two of Us · Grover Washington, Jr. | jazz | 3 | M-00, M-03, M-10 |
| 3 | 踊り子 · Vaundy | soul | 2 | M-00, M-03, M-09, M-10 |
| 4 | Almost Like Being In Love · Red Garland, Paul Chambers, Art Taylor | piano | 1 | M-00, M-03, M-10 |
| 5 | Lucky for You · Novo Amor, Gia Margaret | ambient | 7 | M-00, M-03, M-09, M-10 |

### `043766da` · 2026-11-23 14:30 · 2.1 code

- **Moment:** Sunny field · energy Low · Energize me · Gym · afternoon · weather sunny · a 13-character prompt, read by Claude, that filled no settings
- **Listening history:** demo persona `gym_goer`, strength 0.207
- **Labels:** afternoon, clear, goal_energize, gym
- **Matched rules:** M-00, M-04, M-09, M-10, M-11
- **Claude call:** 3147 ms

| # | Song | Genre | Rank among the 8 retrieved | Rules Claude cited |
|---|---|---|---|---|
| 1 | Talk It Out · dwsdmusic | chill | 5 | M-00, M-04, M-10 |
| 2 | Night Away (Dance) (feat. Tion Wayne) · A1 x J1, Tion Wayne | chill | 4 | M-04, M-10 |
| 3 | Why you gotta lie? · K1 | chill | 2 | M-00, M-04, M-10 |
| 4 | No Friends · Cadmium, Rosendale | edm | 1 | M-04, M-10 |
| 5 | Sweet Little Lies · bülow | indie | 7 | M-04, M-10 |

### `36630dec` · 2026-11-23 14:38 · 2.1 code

- **Moment:** Sunny field · energy Low · Energize me · Gym · afternoon · weather sunny · a 13-character prompt, read by Claude, that filled no settings
- **Listening history:** demo persona `student`, strength 0.186
- **Labels:** afternoon, clear, goal_energize, gym
- **Matched rules:** M-00, M-04, M-09, M-10, M-11
- **Claude call:** 6964 ms

| # | Song | Genre | Rank among the 8 retrieved | Rules Claude cited |
|---|---|---|---|---|
| 1 | Night Away (Dance) (feat. Tion Wayne) · A1 x J1, Tion Wayne | chill | 5 | M-00, M-04, M-10 |
| 2 | Ghalat Fehmi - From "Superstar" · Asim Azhar, Zenab Fatimah Sultan | pop | 2 | M-00, M-04, M-10 |
| 3 | Why you gotta lie? · K1 | chill | 4 | M-00, M-04, M-09, M-10 |
| 4 | No Friends · Cadmium, Rosendale | edm | 1 | M-00, M-04, M-10 |
| 5 | Pehla Pyaar · Armaan Malik, Vishal Mishra | pop | 7 | M-00, M-04, M-10 |

### `e4595b76` · 2026-11-23 15:30 · 2.1 code

- **Moment:** Open road · energy Low · Match my mood · Home · afternoon · weather unknown · a 3-character prompt, read by Claude, that filled no settings
- **Listening history:** demo persona `student`, strength 0.178
- **Labels:** afternoon, goal_match, home
- **Matched rules:** M-00, M-10, M-11
- **Claude call:** 5370 ms

| # | Song | Genre | Rank among the 8 retrieved | Rules Claude cited |
|---|---|---|---|---|
| 1 | Talk It Out · dwsdmusic | chill | 1 | M-00, M-10 |
| 2 | Kannazhaga - The Kiss of Love · Anirudh Ravichander, Dhanush, Shruti Haasan | hip-hop | 2 | M-00, M-10 |
| 3 | You're Still The One · Shania Twain | country | 3 | M-10, M-11 |
| 4 | Just the Two of Us (feat. Bill Withers) · Grover Washington, Jr., Bill Withers | jazz | 4 | M-10, M-11 |
| 5 | Rocky Mountain High · John Denver | folk | 8 | M-00, M-10 |

## Raw log lines

```text
2026-11-22 23:15:50,725 INFO run=0e7354bb inputs card=open_road energy=Low goal=match place=home time=morning weather=sunny note_chars=6
2026-11-22 23:15:50,725 INFO run=0e7354bb labels=['clear', 'goal_match', 'home', 'morning']
2026-11-22 23:15:50,725 INFO run=0e7354bb rules=['M-00', 'M-08', 'M-09', 'M-10', 'M-11'] nudges=['M-09 clear: valence +0.05'] base={'energy': 0.5, 'valence': 0.7, 'acousticness': 0.4} target={'energy': 0.5, 'valence': 0.75, 'acousticness': 0.4}
2026-11-22 23:15:50,725 INFO run=0e7354bb retrieved=[(29, 0.046), (39, 0.084), (58, 0.091), (4, 0.119), (65, 0.119), (60, 0.14), (63, 0.142), (49, 0.143)]
2026-11-22 23:15:57,272 INFO run=0e7354bb mode=ai latency_ms=6546 picks=[(29, ['M-10', 'M-00', 'M-11']), (39, ['M-10', 'M-00', 'M-08']), (58, ['M-10', 'M-00', 'M-09']), (4, ['M-10', 'M-00']), (65, ['M-10', 'M-00', 'M-08'])]
2026-11-23 14:21:57,406 INFO run=5b355ddc inputs card=None energy=Okay goal=lift place=work_study time=afternoon weather=sunny note_chars=13 prompt=ai from_prompt=[]
2026-11-23 14:21:57,406 INFO run=5b355ddc labels=['afternoon', 'clear', 'goal_lift', 'work_study']
2026-11-23 14:21:57,407 INFO run=5b355ddc history persona=student similar_plays=35.8 strength=0.257
2026-11-23 14:21:57,407 INFO run=5b355ddc rules=['M-00', 'M-03', 'M-09', 'M-10', 'M-11'] nudges=['M-09 clear: valence +0.05'] base={'energy': 0.4, 'valence': 0.501, 'acousticness': 0.68} target={'energy': 0.4, 'valence': 0.551, 'acousticness': 0.68}
2026-11-23 14:21:57,407 INFO run=5b355ddc retrieved=[(62, 0.208), (42, 0.238), (50, 0.292), (75, 0.298), (84, 0.307), (110, 0.311), (71, 0.316), (73, 0.371)]
2026-11-23 14:22:08,362 INFO run=5b355ddc mode=ai latency_ms=10955 picks=[(84, ['M-00', 'M-03', 'M-10']), (50, ['M-00', 'M-03', 'M-10']), (42, ['M-00', 'M-03', 'M-09', 'M-10']), (62, ['M-00', 'M-03', 'M-10']), (71, ['M-00', 'M-03', 'M-09', 'M-10'])]
2026-11-23 14:30:54,108 INFO run=043766da inputs card=sunny_field energy=Low goal=energize place=gym time=afternoon weather=sunny note_chars=13 prompt=ai from_prompt=[]
2026-11-23 14:30:54,108 INFO run=043766da labels=['afternoon', 'clear', 'goal_energize', 'gym']
2026-11-23 14:30:54,109 INFO run=043766da history persona=gym_goer similar_plays=21.6 strength=0.207
2026-11-23 14:30:54,109 INFO run=043766da rules=['M-00', 'M-04', 'M-09', 'M-10', 'M-11'] nudges=['M-04: energy +0.20', 'M-09 clear: valence +0.05'] base={'energy': 0.493, 'valence': 0.79, 'acousticness': 0.419} target={'energy': 0.693, 'valence': 0.84, 'acousticness': 0.419}
2026-11-23 14:30:54,110 INFO run=043766da retrieved=[(20, 0.113), (36, 0.17), (7, 0.176), (2, 0.202), (39, 0.235), (24, 0.251), (32, 0.255), (4, 0.256)]
2026-11-23 14:30:57,257 INFO run=043766da mode=ai latency_ms=3147 picks=[(39, ['M-00', 'M-04', 'M-10']), (2, ['M-04', 'M-10']), (36, ['M-00', 'M-04', 'M-10']), (20, ['M-04', 'M-10']), (32, ['M-04', 'M-10'])]
2026-11-23 14:30:57,257 INFO run=043766da check: Reordered so energy steps up (M-10).
2026-11-23 14:38:43,044 INFO run=36630dec inputs card=sunny_field energy=Low goal=energize place=gym time=afternoon weather=sunny note_chars=13 prompt=ai from_prompt=[]
2026-11-23 14:38:43,044 INFO run=36630dec labels=['afternoon', 'clear', 'goal_energize', 'gym']
2026-11-23 14:38:43,044 INFO run=36630dec history persona=student similar_plays=17.3 strength=0.186
2026-11-23 14:38:43,045 INFO run=36630dec rules=['M-00', 'M-04', 'M-09', 'M-10', 'M-11'] nudges=['M-04: energy +0.20', 'M-09 clear: valence +0.05'] base={'energy': 0.422, 'valence': 0.794, 'acousticness': 0.518} target={'energy': 0.622, 'valence': 0.844, 'acousticness': 0.518}
2026-11-23 14:38:43,045 INFO run=36630dec retrieved=[(20, 0.051), (7, 0.087), (4, 0.186), (36, 0.199), (2, 0.222), (39, 0.238), (24, 0.252), (1, 0.261)]
2026-11-23 14:38:50,009 INFO run=36630dec mode=ai latency_ms=6964 picks=[(2, ['M-00', 'M-04', 'M-10']), (7, ['M-00', 'M-04', 'M-10']), (36, ['M-00', 'M-04', 'M-09', 'M-10']), (20, ['M-00', 'M-04', 'M-10']), (24, ['M-00', 'M-04', 'M-10'])]
2026-11-23 15:30:55,727 INFO run=e4595b76 inputs card=open_road energy=Low goal=match place=home time=afternoon weather=unknown note_chars=3 prompt=ai from_prompt=[]
2026-11-23 15:30:55,727 INFO run=e4595b76 labels=['afternoon', 'goal_match', 'home']
2026-11-23 15:30:55,728 INFO run=e4595b76 history persona=student similar_plays=16.1 strength=0.178
2026-11-23 15:30:55,728 INFO run=e4595b76 rules=['M-00', 'M-10', 'M-11'] nudges=[] base={'energy': 0.462, 'valence': 0.65, 'acousticness': 0.461} target={'energy': 0.462, 'valence': 0.65, 'acousticness': 0.461}
2026-11-23 15:30:55,728 INFO run=e4595b76 retrieved=[(39, 0.042), (63, 0.057), (65, 0.078), (66, 0.082), (49, 0.082), (4, 0.102), (60, 0.129), (58, 0.13)]
2026-11-23 15:31:01,098 INFO run=e4595b76 mode=ai latency_ms=5370 picks=[(39, ['M-00', 'M-10']), (63, ['M-00', 'M-10']), (65, ['M-10', 'M-11']), (66, ['M-10', 'M-11']), (58, ['M-00', 'M-10'])]
```
