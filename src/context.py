"""Turn what the listener says (and the simulated phone signals) into labels and a target point."""
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.manual import MAX_NUDGE, Nudge

AXES = ("energy", "valence", "acousticness")

MOOD_CARDS = {
    "sunny_field":   {"emoji": "☀️", "label": "Sunny field",   "valence": 0.85, "energy": 0.55, "acousticness": 0.5},
    "party_lights":  {"emoji": "🎉", "label": "Party lights",  "valence": 0.85, "energy": 0.90, "acousticness": 0.2},
    "open_road":     {"emoji": "🛣️", "label": "Open road",     "valence": 0.70, "energy": 0.70, "acousticness": 0.4},
    "cozy_blanket":  {"emoji": "🛋️", "label": "Cozy blanket",  "valence": 0.65, "energy": 0.25, "acousticness": 0.7},
    "city_night":    {"emoji": "🌃", "label": "City at night", "valence": 0.45, "energy": 0.60, "acousticness": 0.3},
    "foggy_morning": {"emoji": "🌫️", "label": "Foggy morning", "valence": 0.40, "energy": 0.30, "acousticness": 0.6},
    "rainy_window":  {"emoji": "🌧️", "label": "Rainy window",  "valence": 0.25, "energy": 0.25, "acousticness": 0.6},
    "storm":         {"emoji": "⛈️", "label": "Storm",         "valence": 0.20, "energy": 0.85, "acousticness": 0.2},
}
ENERGY_LEVELS = {"Drained": 0.1, "Low": 0.3, "Okay": 0.5, "Good": 0.7, "Wired": 0.9}
GOALS = {
    "match": "Match my mood",
    "lift": "Lift me up",
    "calm": "Calm me down",
    "focus": "Help me focus",
    "energize": "Energize me",
}
PLACES = {"home": "Home", "commute": "Commuting", "work_study": "Work / study", "gym": "Gym", "out": "Out"}
WEATHER = ("sunny", "cloudy", "foggy", "rainy", "snowy", "stormy")
WEATHER_LABELS = {"rainy": "rain", "stormy": "rain", "snowy": "snow", "sunny": "clear"}

NOTE_MAX = 200
HR_RESTING_HIGH = 100     # bpm, away from the gym
HR_ACTIVE = 110           # bpm, at the gym
MANY_NOTIFICATIONS = 10
SHORT_SLEEP_HOURS = 6


@dataclass
class Moment:
    """Everything the listener tells the app, plus the simulated phone signals."""
    mood_card: str
    energy_level: str
    goal: str
    place: str
    hour: int  # local hour, 0-23
    weather: Optional[str] = None
    heart_rate: Optional[int] = None
    notifications: Optional[int] = None
    sleep_hours: Optional[float] = None
    note: str = ""


def validate(moment: Moment) -> None:
    """Raise ValueError if any input is unknown or out of range."""
    if moment.mood_card not in MOOD_CARDS:
        raise ValueError(f"Unknown mood card: {moment.mood_card}")
    if moment.energy_level not in ENERGY_LEVELS:
        raise ValueError(f"Unknown energy level: {moment.energy_level}")
    if moment.goal not in GOALS:
        raise ValueError(f"Unknown goal: {moment.goal}")
    if moment.place not in PLACES:
        raise ValueError(f"Unknown place: {moment.place}")
    if not 0 <= moment.hour <= 23:
        raise ValueError(f"Hour must be 0-23, got {moment.hour}")
    if moment.weather is not None and moment.weather not in WEATHER:
        raise ValueError(f"Unknown weather: {moment.weather}")
    if moment.heart_rate is not None and not 30 <= moment.heart_rate <= 220:
        raise ValueError("Heart rate must be 30-220 bpm")
    if moment.notifications is not None and not 0 <= moment.notifications <= 999:
        raise ValueError("Notifications must be 0-999")
    if moment.sleep_hours is not None and not 0 <= moment.sleep_hours <= 24:
        raise ValueError("Sleep hours must be 0-24")
    if len(moment.note) > NOTE_MAX:
        raise ValueError(f"Note must be {NOTE_MAX} characters or fewer")


def time_of_day(hour: int) -> str:
    if 5 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 16:
        return "afternoon"
    if 17 <= hour <= 21:
        return "evening"
    return "night"


def base_point(moment: Moment) -> Dict[str, float]:
    """Starting point from what the listener said: the mood card, with energy averaged with the energy level."""
    card = MOOD_CARDS[moment.mood_card]
    return {
        "energy": round((card["energy"] + ENERGY_LEVELS[moment.energy_level]) / 2, 3),
        "valence": card["valence"],
        "acousticness": card["acousticness"],
    }


def labels_for(moment: Moment) -> List[str]:
    """Coarse labels the manual's rules match on. Raw signal numbers stay here."""
    base = base_point(moment)
    labels = {f"goal_{moment.goal}", moment.place, time_of_day(moment.hour)}
    if base["valence"] < 0.35:
        labels.add("tense_mood" if base["energy"] > 0.65 else "low_mood")
    if moment.weather in WEATHER_LABELS:
        labels.add(WEATHER_LABELS[moment.weather])
    if moment.heart_rate is not None:
        if moment.place == "gym" and moment.heart_rate >= HR_ACTIVE:
            labels.add("hr_active")
        elif moment.place != "gym" and moment.heart_rate >= HR_RESTING_HIGH:
            labels.add("hr_high_resting")
    if moment.notifications is not None and moment.notifications >= MANY_NOTIFICATIONS:
        labels.add("notifications_many")
    if moment.sleep_hours is not None and moment.sleep_hours < SHORT_SLEEP_HOURS:
        labels.add("sleep_short")
    return sorted(labels)


def apply_nudges(base: Dict[str, float], nudges: List[Nudge]) -> Dict[str, float]:
    """Add up the manual's nudges, cap each axis at ±0.25, and keep values within 0-1."""
    target = {}
    for axis in AXES:
        shift = sum(n.delta for n in nudges if n.axis == axis)
        shift = max(-MAX_NUDGE, min(MAX_NUDGE, shift))
        target[axis] = round(min(1.0, max(0.0, base[axis] + shift)), 3)
    return target
