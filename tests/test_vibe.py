import logging

import pytest

from src.context import Moment
from src.vibe import SUPPORT_MESSAGE, needs_support, recommend_for_moment


def moment(**changes):
    values = dict(mood_card="rainy_window", energy_level="Low", goal="match", place="home", hour=23, weather="rainy")
    values.update(changes)
    return Moment(**values)


class NeverCalled:
    last_request_id = None

    def propose(self, *args):
        raise AssertionError("the reasoner should not be called")


def rule_ids(result):
    return [r.id for r in result.rules]


def test_rainy_night_offline_end_to_end():
    result = recommend_for_moment(moment())
    assert result.target == {"energy": 0.075, "valence": 0.25, "acousticness": 0.8}
    assert {"M-02", "M-05", "M-08", "M-09"} <= set(rule_ids(result))
    assert result.explanation.mode == "offline"
    picks = result.explanation.picks
    assert len(picks) == 5 and len(result.candidates) == 8
    assert sum(p.song["valence"] < 0.25 for p in picks) <= 2
    assert [p.song["valence"] for p in picks] == sorted(p.song["valence"] for p in picks)


def test_storm_at_the_gym_energizes():
    result = recommend_for_moment(moment(mood_card="storm", energy_level="Wired", goal="energize",
                                         place="gym", hour=18, weather="sunny"))
    assert {"M-04", "M-06"} <= set(rule_ids(result))
    energies = [p.song["energy"] for p in result.explanation.picks]
    assert energies == sorted(energies)
    assert sum(energies) / len(energies) > 0.7


def test_focus_prefers_instrumental_songs():
    result = recommend_for_moment(moment(mood_card="city_night", energy_level="Okay", goal="focus",
                                         place="work_study", hour=14, weather="cloudy"))
    assert "M-03" in rule_ids(result)
    instrumental = [s for s, _ in result.candidates if s["instrumentalness"] >= 0.5]
    assert len(instrumental) >= 3


def test_high_resting_heart_rate_calms_without_saying_the_number():
    result = recommend_for_moment(moment(mood_card="cozy_blanket", energy_level="Okay", hour=15,
                                         weather="cloudy", heart_rate=110))
    assert "hr_high_resting" in result.labels and "M-01" in rule_ids(result)
    energies = [p.song["energy"] for p in result.explanation.picks]
    assert energies == sorted(energies, reverse=True)
    assert all("110" not in p.reason for p in result.explanation.picks)


def test_crisis_note_shows_support_and_skips_the_ai():
    result = recommend_for_moment(moment(note="i want to die"), reasoner=NeverCalled())
    assert result.support_message == SUPPORT_MESSAGE
    assert result.explanation.mode == "offline"


@pytest.mark.parametrize("note, expected", [("I feel like I want to die", True), ("Self-harm thoughts", True),
                                            ("die hard fan of jazz", False), ("cozy please", False)])
def test_needs_support(note, expected):
    assert needs_support(note) is expected


def test_logs_have_every_step_but_no_raw_signals_or_note(caplog):
    caplog.set_level(logging.INFO, logger="vibematch")
    recommend_for_moment(moment(heart_rate=137, notifications=43, sleep_hours=4.25, note="secret note text"))
    text = caplog.text
    for step in ("inputs", "labels=", "rules=", "retrieved=", "mode="):
        assert step in text
    for leak in ("137", "=43", "4.25", "secret note text"):
        assert leak not in text
    assert "note_chars=16" in text


def test_bad_input_is_rejected_before_anything_runs():
    with pytest.raises(ValueError):
        recommend_for_moment(moment(mood_card="volcano"))
