import pytest

from src.context import Moment, apply_nudges, base_point, labels_for, time_of_day, validate
from src.manual import Nudge, load_manual, match_rules, nudges_for


def moment(**changes):
    values = dict(mood_card="rainy_window", energy_level="Low", goal="match", place="home", hour=23)
    values.update(changes)
    return Moment(**values)


def test_base_point_averages_card_energy_with_energy_level():
    assert base_point(moment()) == {"energy": 0.275, "valence": 0.25, "acousticness": 0.6}


def test_low_mood_and_tense_mood_are_separate():
    assert "low_mood" in labels_for(moment())
    tense = labels_for(moment(mood_card="storm", energy_level="Wired"))
    assert "tense_mood" in tense and "low_mood" not in tense


def test_time_of_day_buckets():
    assert [time_of_day(h) for h in (8, 14, 19, 23, 3)] == ["morning", "afternoon", "evening", "night", "night"]


def test_heart_rate_means_different_things_at_the_gym():
    assert "hr_high_resting" in labels_for(moment(heart_rate=110))
    at_gym = labels_for(moment(place="gym", heart_rate=130))
    assert "hr_active" in at_gym and "hr_high_resting" not in at_gym


def test_phone_signals_become_coarse_labels():
    labels = labels_for(moment(notifications=12, sleep_hours=5.0, weather="stormy"))
    assert {"notifications_many", "sleep_short", "rain"} <= set(labels)
    calm_day = labels_for(moment(notifications=2, sleep_hours=8.0, weather="cloudy"))
    assert not {"notifications_many", "sleep_short", "rain"} & set(calm_day)


def test_worked_example_from_the_plan():
    # Rainy window + Low energy + home + 11 pm + rain -> energy 0.075, valence 0.25, acoustic 0.80
    m = moment(weather="rainy")
    labels = labels_for(m)
    rules = match_rules(load_manual(), labels)
    target = apply_nudges(base_point(m), nudges_for(rules, labels))
    assert target == {"energy": 0.075, "valence": 0.25, "acousticness": 0.8}


def test_nudges_are_capped_and_clamped():
    base = {"energy": 0.1, "valence": 0.5, "acousticness": 0.95}
    nudges = [Nudge("X", "energy", -0.2), Nudge("Y", "energy", -0.2), Nudge("Z", "acousticness", 0.2)]
    target = apply_nudges(base, nudges)
    assert target["energy"] == 0.0          # -0.4 capped to -0.25, then clamped at 0
    assert target["acousticness"] == 1.0    # clamped at 1
    assert target["valence"] == 0.5


@pytest.mark.parametrize("change", [
    {"mood_card": "volcano"}, {"energy_level": "Hyper"}, {"goal": "party"}, {"place": "moon"},
    {"hour": 24}, {"weather": "hail"}, {"heart_rate": 300}, {"notifications": -1},
    {"sleep_hours": 30}, {"note": "x" * 201},
])
def test_validate_rejects_bad_input(change):
    with pytest.raises(ValueError):
        validate(moment(**change))


def test_validate_accepts_good_input():
    validate(moment(weather="sunny", heart_rate=72, notifications=3, sleep_hours=7.5, note="cozy please"))


def test_without_a_card_the_start_is_history_then_neutral():
    usual = {"energy": 0.2, "valence": 0.3, "acousticness": 0.9}
    assert base_point(Moment(hour=9), usual) == usual
    assert base_point(Moment(hour=9, energy_level="Wired"), usual)["energy"] == 0.55
    assert base_point(Moment(hour=9)) == {"energy": 0.5, "valence": 0.5, "acousticness": 0.5}


def test_auto_fields_are_valid_and_add_no_labels():
    m = Moment(hour=9, goal="match")
    validate(m)
    assert labels_for(m) == ["goal_match", "morning"]
