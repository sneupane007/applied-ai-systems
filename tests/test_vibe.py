import logging

import pytest

from src.context import Moment
from src.history import load_history, plays_for
from src.vibe import SUPPORT_MESSAGE, needs_support, recommend_for_moment


def moment(**changes):
    values = dict(mood_card="rainy_window", energy_level="Low", goal="match", place="home", hour=23, weather="rainy")
    values.update(changes)
    return Moment(**values)


class NeverCalled:
    last_request_id = None

    def propose(self, *args):
        raise AssertionError("the reasoner should not be called")

    def parse(self, *args):
        raise AssertionError("the prompt parser should not be called")


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
    result = recommend_for_moment(moment(note="i want to die"), reasoner=NeverCalled(), parser=NeverCalled())
    assert result.support_message == SUPPORT_MESSAGE
    assert result.explanation.mode == "offline"
    assert result.prompt_mode == "keywords"


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


def test_a_prompt_alone_works_offline():
    result = recommend_for_moment(Moment(hour=14, weather="cloudy", note="need to focus, no lyrics"))
    assert result.from_prompt == ["goal"] and result.moment.goal == "focus"
    assert "M-03" in rule_ids(result) and "no_lyrics" in result.labels
    assert result.base == {"energy": 0.5, "valence": 0.5, "acousticness": 0.5}  # no card, no history: neutral
    assert sum(s["instrumentalness"] >= 0.5 for s, _ in result.candidates) >= 3
    assert len(result.explanation.picks) == 5


def test_your_own_choices_win_over_the_prompt():
    result = recommend_for_moment(Moment(hour=18, goal="calm", place="home", note="pump me up at the gym"))
    assert result.moment.goal == "calm" and result.moment.place == "home"
    assert result.from_prompt == [] and result.intent.place == "gym"


def test_history_pulls_a_stated_mood_toward_the_usual_sound():
    result = recommend_for_moment(moment(mood_card="party_lights", energy_level="Wired", hour=22, weather="rainy"),
                                  history=plays_for(load_history(), "student"))
    assert 0 < result.history.strength < 0.4
    assert result.stated["energy"] > result.base["energy"]  # the student plays quiet songs on rainy nights


def test_logs_have_no_prompt_text_or_play_history(caplog):
    caplog.set_level(logging.INFO, logger="vibematch")
    recommend_for_moment(moment(note="secret prompt words"), history=plays_for(load_history(), "night_owl"))
    text = caplog.text
    assert "persona=night_owl" in text and "similar_plays=" in text and "prompt=keywords" in text
    for leak in ("secret prompt words", "2026-10-", "played_at"):
        assert leak not in text
