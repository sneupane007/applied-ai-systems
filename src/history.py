"""Listening history: what a listener played before, and when, where, and in what weather.

The history never leaves the device. It pulls the starting point toward what this listener usually
plays in a similar moment, and re-ranks retrieved songs (familiar songs up, often-skipped songs down).
"""
import csv
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from src.context import AXES, time_of_day

HISTORY_PATH = "data/listening_history.csv"
PERSONAS = {"student": "Student", "gym_goer": "Gym-goer", "night_owl": "Night owl"}
MAX_STRENGTH = 0.4    # history moves the starting point at most 40% of the way
HALF_STRENGTH_AT = 20  # similar plays needed for half of MAX_STRENGTH
OFTEN_SKIPPED = 2
FAMILIAR_BONUS = 0.05
SKIP_PENALTY = 0.10
LIKED_GENRE_BONUS = 0.05
AVOIDED_GENRE_PENALTY = 0.30


@dataclass
class Play:
    persona: str
    played_at: datetime
    song_id: int
    place: str
    weather: str
    completed: bool


@dataclass
class HistoryProfile:
    similar_plays: float  # a play matching all of time of day, weather, and place counts as 1
    strength: float       # 0 to MAX_STRENGTH
    centroid: Optional[Dict[str, float]] = None
    familiar: Set[int] = field(default_factory=set)
    skipped: Set[int] = field(default_factory=set)

    def summary(self) -> str:
        """A coarse description, the only part of the history the AI may see."""
        if not self.centroid:
            return "no similar past plays"
        words = [_level(self.centroid["energy"], "low energy", "high energy"),
                 _level(self.centroid["valence"], "darker", "brighter"),
                 _level(self.centroid["acousticness"], "electronic", "acoustic")]
        words = [w for w in words if w]
        return f"{round(self.similar_plays)} similar past plays, usually " + (", ".join(words) or "middle of the road")


def _level(value: float, low: str, high: str) -> str:
    return low if value < 0.4 else high if value > 0.6 else ""


def load_history(path: str = HISTORY_PATH) -> List[Play]:
    with open(path, newline="") as f:
        return [Play(row["persona"], datetime.fromisoformat(row["played_at"]), int(row["song_id"]),
                     row["place"], row["weather"], row["completed"] == "1")
                for row in csv.DictReader(f)]


def plays_for(plays: List[Play], persona: str) -> List[Play]:
    return [p for p in plays if p.persona == persona]


def profile_for(plays: List[Play], songs_by_id: Dict[int, Dict], hour: int,
                weather: Optional[str], place: Optional[str]) -> HistoryProfile:
    """Weight each finished play by how many of time of day, weather, and place match the moment.

    The weight is the match count squared (1, 4, 9), so plays that match more of the moment count
    much more than plays that share only, say, the place.
    """
    now = time_of_day(hour)
    totals, weight_sum = dict.fromkeys(AXES, 0.0), 0.0
    familiar, skips, finishes = set(), Counter(), Counter()
    for play in plays:
        if play.song_id not in songs_by_id:
            continue
        if not play.completed:
            skips[play.song_id] += 1
            continue
        finishes[play.song_id] += 1
        matches = (time_of_day(play.played_at.hour) == now) + (play.weather == weather) + (play.place == place)
        if matches >= 2:
            familiar.add(play.song_id)
        weight_sum += matches ** 2
        for axis in AXES:
            totals[axis] += matches ** 2 * songs_by_id[play.song_id][axis]

    skipped = {song_id for song_id, n in skips.items() if n >= OFTEN_SKIPPED and n > finishes[song_id]}
    if weight_sum == 0:
        return HistoryProfile(0.0, 0.0, None, set(), skipped)
    n = weight_sum / 9
    centroid = {axis: round(totals[axis] / weight_sum, 3) for axis in AXES}
    return HistoryProfile(round(n, 1), round(MAX_STRENGTH * n / (n + HALF_STRENGTH_AT), 3), centroid, familiar, skipped)


def blend(stated: Dict[str, float], profile: Optional[HistoryProfile]) -> Dict[str, float]:
    """Move the stated point toward the history centroid by the profile's strength."""
    if not profile or not profile.centroid:
        return dict(stated)
    s = profile.strength
    return {axis: round((1 - s) * stated[axis] + s * profile.centroid[axis], 3) for axis in AXES}


def rerank(candidates: List[Tuple[Dict, float]], profile: Optional[HistoryProfile],
           genres_like=(), genres_avoid=()) -> List[Tuple[Dict, float]]:
    """Adjust retrieval distances locally (familiar, often skipped, liked/avoided genres) and re-sort."""
    adjusted = []
    for song, dist in candidates:
        if profile:
            if song["id"] in profile.familiar:
                dist -= FAMILIAR_BONUS
            if song["id"] in profile.skipped:
                dist += SKIP_PENALTY
        if song.get("genre") in genres_like:
            dist -= LIKED_GENRE_BONUS
        if song.get("genre") in genres_avoid:
            dist += AVOIDED_GENRE_PENALTY
        adjusted.append((song, round(max(0.0, dist), 3)))
    return sorted(adjusted, key=lambda pair: pair[1])
