# Where `listening_history.csv` comes from

**This data is made up.** No real person's listening is in it. `python -m scripts.make_demo_history` (seed 42) generates it from `data/catalog.csv` so VibeMatch can show how listening history changes recommendations.

## Columns

| Column | Meaning |
|---|---|
| `persona` | `student`, `gym_goer`, or `night_owl` |
| `played_at` | Local date and time, minutes precision (2026-10-01 to 2026-11-11) |
| `song_id` | `id` in `data/catalog.csv` |
| `place` | One of the app's places: `home`, `commute`, `work_study`, `gym`, `out` |
| `weather` | One of the app's weather categories. Each persona has its own daily weather draw (sunny 33%, cloudy 30%, rainy 22%, foggy 6%, stormy 5%, snowy 4%) |
| `completed` | `1` = listened to the end, `0` = skipped |

## How it was built

Each persona has a few habits: which days, which start hours, a place, the weather it needs (if any), the chance of a session on a matching day, and a target sound (energy, valence, acousticness, plus optional soft ranges like the manual's). A session is 4–8 plays a few minutes apart.

- 85% of plays are drawn from the 15 catalog songs nearest the habit's sound (using the same distance as retrieval). 15% are random.
- The chance of finishing a song is `0.95 − 1.5 × distance` (kept between 0.10 and 0.95), so songs far from the habit are usually skipped.

## Planted patterns

| Persona | Habit | Target sound (energy · valence · acoustic) |
|---|---|---|
| student (398 plays) | Weekday afternoons, work / study, prefers instrumental | 0.25 · 0.45 · 0.75 |
| | Weekday 8 am commute | 0.70 · 0.75 · 0.25 |
| | Rainy or stormy nights at home | 0.15 · 0.30 · 0.85 |
| | Other nights at home | 0.45 · 0.60 · 0.50 |
| gym_goer (237 plays) | Mon/Tue/Thu/Fri evenings at the gym, 120–140 bpm | 0.88 · 0.60 · 0.08 |
| | Sunny weekend mornings out | 0.75 · 0.85 · 0.30 |
| | Weekday 8 am commute | 0.65 · 0.70 · 0.20 |
| night_owl (290 plays) | Late nights at home (11 pm – 1 am) | 0.40 · 0.30 · 0.50 |
| | Rainy, stormy, or foggy afternoons at home | 0.25 · 0.20 · 0.75 |
| | Weekend evenings out | 0.65 · 0.45 · 0.25 |

`tests/test_history.py` checks that VibeMatch recovers some of these patterns. That check is circular on purpose: it shows the code finds patterns that are known to be there, not that real listeners behave this way.
