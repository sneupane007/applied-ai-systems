"""What may leave the device, and where it may go.

Raw signals (heart rate, notification count, sleep hours, city, exact hour) never leave.
The reasoner (Claude today) gets coarse labels; the music source gets only the music intent.
"""
from typing import Dict, List, Tuple

from src.context import GOALS, MOOD_CARDS, PLACES, Moment, time_of_day

REASONER_FIELDS = ("mood", "energy_level", "goal", "place", "time_of_day", "weather", "labels", "note")
MUSIC_FIELDS = ("target", "prefer")


def _only(payload: Dict, allowed: Tuple[str, ...]) -> Dict:
    extra = set(payload) - set(allowed)
    if extra:
        raise ValueError(f"Not allowed to leave the device: {sorted(extra)}")
    return payload


def for_reasoner(moment: Moment, labels: List[str]) -> Dict:
    """What the AI may see about the listener."""
    return _only({
        "mood": MOOD_CARDS[moment.mood_card]["label"],
        "energy_level": moment.energy_level,
        "goal": GOALS[moment.goal],
        "place": PLACES[moment.place],
        "time_of_day": time_of_day(moment.hour),
        "weather": moment.weather or "unknown",
        "labels": list(labels),
        "note": moment.note,
    }, REASONER_FIELDS)


def music_intent(target: Dict[str, float], prefer: List[Tuple[str, float, float]]) -> Dict:
    """What the music source may see: the target sound and soft ranges, nothing about the listener."""
    return _only({
        "target": dict(target),
        "prefer": [(feature, low, high) for feature, low, high in prefer],
    }, MUSIC_FIELDS)
