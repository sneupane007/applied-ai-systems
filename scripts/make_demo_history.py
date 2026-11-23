"""Write data/listening_history.csv: six weeks of made-up plays for three demo listeners.

Usage (from the project root):
    python -m scripts.make_demo_history

The data is synthetic (seed 42). Each persona has a few habits: when, where, in what weather, and
what it sounds like. Songs are drawn from the catalog songs nearest each habit's sound, plus some
random exploration, and songs far from the habit are more likely to be skipped.
See data/HISTORY_SOURCE.md for the planted patterns.
"""
import csv
import random
from datetime import date, datetime, timedelta

from src.context import WEATHER
from src.recommender import load_songs
from src.retrieval import CATALOG_PATH, distance

OUT_PATH = "data/listening_history.csv"
SEED = 42
START = date(2026, 10, 1)
DAYS = 42
WEATHER_ODDS = {"sunny": 0.33, "cloudy": 0.30, "rainy": 0.22, "foggy": 0.06, "snowy": 0.04, "stormy": 0.05}
NEAREST = 15        # habit songs are drawn from this many nearest songs
EXPLORE = 0.15      # share of plays picked at random from the whole catalog
PLAYS_PER_SESSION = (4, 8)
WEEKDAYS = {0, 1, 2, 3, 4}
WEEKEND = {5, 6}
ALL_DAYS = WEEKDAYS | WEEKEND
WET = {"rainy", "stormy"}

# Each habit: days of the week, possible start hours, place, weather it needs (None = any),
# chance of a session on a matching day, target sound, and soft ranges (as in the manual).
PERSONAS = {
    "student": [
        dict(days=WEEKDAYS, hours=[13, 14, 15], place="work_study", weather=None, chance=0.8,
             target={"energy": 0.25, "valence": 0.45, "acousticness": 0.75},
             prefer=[("instrumentalness", 0.5, 1.0)]),
        dict(days=WEEKDAYS, hours=[8], place="commute", weather=None, chance=0.7,
             target={"energy": 0.70, "valence": 0.75, "acousticness": 0.25}, prefer=[]),
        dict(days=ALL_DAYS, hours=[21, 22, 23], place="home", weather=WET, chance=0.9,
             target={"energy": 0.15, "valence": 0.30, "acousticness": 0.85}, prefer=[]),
        dict(days=ALL_DAYS, hours=[21, 22], place="home", weather=set(WEATHER) - WET, chance=0.4,
             target={"energy": 0.45, "valence": 0.60, "acousticness": 0.50}, prefer=[]),
    ],
    "gym_goer": [
        dict(days={0, 1, 3, 4}, hours=[18, 19], place="gym", weather=None, chance=0.85,
             target={"energy": 0.88, "valence": 0.60, "acousticness": 0.08},
             prefer=[("tempo_bpm", 120.0, 140.0)]),
        dict(days=WEEKEND, hours=[9, 10], place="out", weather={"sunny"}, chance=0.9,
             target={"energy": 0.75, "valence": 0.85, "acousticness": 0.30}, prefer=[]),
        dict(days=WEEKDAYS, hours=[8], place="commute", weather=None, chance=0.5,
             target={"energy": 0.65, "valence": 0.70, "acousticness": 0.20}, prefer=[]),
    ],
    "night_owl": [
        dict(days=ALL_DAYS, hours=[23, 0, 1], place="home", weather=None, chance=0.8,
             target={"energy": 0.40, "valence": 0.30, "acousticness": 0.50}, prefer=[]),
        dict(days=ALL_DAYS, hours=[14, 15, 16], place="home", weather=WET | {"foggy"}, chance=0.8,
             target={"energy": 0.25, "valence": 0.20, "acousticness": 0.75}, prefer=[]),
        dict(days=WEEKEND, hours=[20, 21], place="out", weather=None, chance=0.5,
             target={"energy": 0.65, "valence": 0.45, "acousticness": 0.25}, prefer=[]),
    ],
}


def completion_chance(dist: float) -> float:
    """Songs close to the habit are usually finished; far ones are usually skipped."""
    return min(0.95, max(0.1, 0.95 - 1.5 * dist))


def session(rng, songs, habit, day, weather):
    intent = {"target": habit["target"], "prefer": habit["prefer"]}
    nearest = sorted(songs, key=lambda s: distance(s, intent))[:NEAREST]
    played_at = datetime(day.year, day.month, day.day, rng.choice(habit["hours"]), rng.randrange(0, 20))
    rows = []
    for _ in range(rng.randint(*PLAYS_PER_SESSION)):
        song = rng.choice(songs) if rng.random() < EXPLORE else rng.choice(nearest)
        completed = rng.random() < completion_chance(distance(song, intent))
        rows.append((played_at, song["id"], habit["place"], weather, int(completed)))
        played_at += timedelta(minutes=rng.randint(2, 5))
    return rows


def main() -> None:
    rng = random.Random(SEED)
    songs = load_songs(CATALOG_PATH)
    for song in songs:
        song["instrumentalness"] = float(song.get("instrumentalness") or 0.0)

    rows = []
    for persona, habits in PERSONAS.items():
        for offset in range(DAYS):
            day = START + timedelta(days=offset)
            weather = rng.choices(list(WEATHER_ODDS), weights=list(WEATHER_ODDS.values()))[0]
            for habit in habits:
                if day.weekday() not in habit["days"]:
                    continue
                if habit["weather"] is not None and weather not in habit["weather"]:
                    continue
                if rng.random() < habit["chance"]:
                    rows += [(persona, *row) for row in session(rng, songs, habit, day, weather)]

    rows.sort(key=lambda r: (list(PERSONAS).index(r[0]), r[1]))
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["persona", "played_at", "song_id", "place", "weather", "completed"])
        for persona, played_at, song_id, place, weather, completed in rows:
            writer.writerow([persona, played_at.isoformat(timespec="minutes"), song_id, place, weather, completed])

    print(f"Wrote {len(rows)} plays to {OUT_PATH}")
    for persona in PERSONAS:
        mine = [r for r in rows if r[0] == persona]
        print(f"  {persona}: {len(mine)} plays, {sum(r[5] for r in mine)} completed")


if __name__ == "__main__":
    main()
