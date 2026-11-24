"""Find the songs closest to the target sound (the retrieval step of RAG).

MusicSource is the swap point: LocalCatalog reads data/catalog.csv today; a Spotify
source could replace it later, as long as it accepts the same music intent.
"""
import math
from typing import Dict, List, Optional, Protocol, Tuple

from src.recommender import load_songs

CATALOG_PATH = "data/catalog.csv"
DISTANCE_WEIGHTS = {"energy": 1.0, "valence": 1.0, "acousticness": 0.5}
RANGE_WEIGHT = 0.5  # penalty per unit a song falls outside a preferred range
RANGE_SCALE = {"tempo_bpm": 100.0}  # tempo gaps count per 100 bpm; other features are already 0-1
DEFAULT_K = 8


class MusicSource(Protocol):
    def search(self, intent: Dict, k: int = DEFAULT_K) -> List[Tuple[Dict, float]]: ...


def distance(song: Dict, intent: Dict) -> float:
    """Weighted distance to the target, plus a penalty that grows the further a song falls outside a preferred range."""
    target = intent["target"]
    d = math.sqrt(sum(w * (song[axis] - target[axis]) ** 2 for axis, w in DISTANCE_WEIGHTS.items()))
    gap = sum(max(low - song[feature], song[feature] - high, 0.0) / RANGE_SCALE.get(feature, 1.0)
              for feature, low, high in intent.get("prefer", []))
    return d + RANGE_WEIGHT * gap


class LocalCatalog:
    """Songs from a CSV in the data/songs.csv format (instrumentalness optional)."""

    def __init__(self, path: str = CATALOG_PATH, songs: Optional[List[Dict]] = None):
        self.songs = songs if songs is not None else load_songs(path)
        for song in self.songs:
            song["instrumentalness"] = float(song.get("instrumentalness") or 0.0)

    def search(self, intent: Dict, k: int = DEFAULT_K, max_per_artist: int = 1) -> List[Tuple[Dict, float]]:
        """The k closest songs, with at most max_per_artist songs per artist."""
        ranked = sorted(self.songs, key=lambda song: distance(song, intent))
        results, per_artist = [], {}
        for song in ranked:
            if per_artist.get(song["artist"], 0) >= max_per_artist:
                continue
            per_artist[song["artist"]] = per_artist.get(song["artist"], 0) + 1
            results.append((song, round(distance(song, intent), 3)))
            if len(results) == k:
                break
        return results
