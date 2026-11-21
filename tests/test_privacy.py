import json

import pytest

from src.context import Moment, labels_for
from src.privacy import MUSIC_FIELDS, REASONER_FIELDS, _only, for_reasoner, music_intent

# Distinctive raw values so a leak would show up in the serialized payloads.
RAW = Moment(
    mood_card="rainy_window", energy_level="Low", goal="calm", place="home", hour=23,
    weather="rainy", heart_rate=137, notifications=43, sleep_hours=4.25,
    note="secret note text",
)


def test_reasoner_gets_labels_not_raw_signals():
    payload = for_reasoner(RAW, labels_for(RAW))
    text = json.dumps(payload)
    assert set(payload) == set(REASONER_FIELDS)
    for raw in ("137", "43", "4.25", "23"):
        assert raw not in text
    assert "hr_high_resting" in payload["labels"]
    assert payload["time_of_day"] == "night"


def test_music_source_gets_only_the_music_intent():
    intent = music_intent({"energy": 0.1, "valence": 0.25, "acousticness": 0.8}, [("tempo_bpm", 60.0, 80.0)])
    text = json.dumps(intent)
    assert set(intent) == set(MUSIC_FIELDS)
    for leak in ("secret", "hr_", "rain", "home", "137", "night"):
        assert leak not in text


def test_unlisted_fields_are_blocked():
    with pytest.raises(ValueError):
        _only({"target": {}, "heart_rate": 137}, MUSIC_FIELDS)
