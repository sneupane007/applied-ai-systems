import pytest

from src.manual import (
    EVIDENCE_LEVELS,
    MAX_NUDGE,
    load_manual,
    match_rules,
    nudges_for,
    preferences_for,
    prompt_text,
)

RULES = load_manual()
RAINY_NIGHT = ["goal_match", "home", "low_mood", "night", "rain"]


def ids(rules):
    return [rule.id for rule in rules]


def test_manual_has_all_twelve_rules_in_order():
    assert ids(RULES) == [f"M-{i:02d}" for i in range(12)]


def test_every_rule_is_complete():
    for rule in RULES:
        assert rule.title and rule.why and rule.guidance and rule.sources and rule.avoid
        assert rule.evidence in EVIDENCE_LEVELS
        assert rule.always or rule.when, f"{rule.id} never turns on"


def test_nudges_stay_within_bounds():
    for rule in RULES:
        for nudge in rule.nudges:
            assert abs(nudge.delta) <= MAX_NUDGE


def test_always_on_rules_are_core_sequencing_and_privacy():
    assert ids(r for r in RULES if r.always) == ["M-00", "M-10", "M-11"]


def test_rainy_night_at_home_matches_expected_rules():
    matched = ids(match_rules(RULES, RAINY_NIGHT))
    assert matched == ["M-00", "M-02", "M-05", "M-08", "M-09", "M-10", "M-11"]


def test_combined_labels_need_all_parts():
    # M-02 needs night AND home (or night AND goal_calm); home alone isn't enough.
    assert "M-02" not in ids(match_rules(RULES, ["home", "afternoon", "goal_match"]))
    assert "M-02" in ids(match_rules(RULES, ["night", "goal_calm", "out"]))


def test_matched_rules_are_capped():
    every_label = ["goal_calm", "goal_focus", "goal_energize", "gym", "low_mood", "night",
                   "home", "rain", "sleep_short", "hr_high_resting", "work_study"]
    matched = [r for r in match_rules(RULES, every_label, max_matched=3) if not r.always]
    assert len(matched) == 3


def test_label_specific_nudges_only_apply_with_their_label():
    weather = next(r for r in RULES if r.id == "M-09")
    rain = {(n.axis, n.delta) for n in nudges_for([weather], ["rain"])}
    snow = {(n.axis, n.delta) for n in nudges_for([weather], ["snow"])}
    assert rain == {("energy", -0.10), ("acousticness", 0.15)}
    assert snow == {("energy", -0.05), ("acousticness", 0.10)}
    assert nudges_for([weather], ["cloudy"]) == []


def test_preferences_use_song_column_names():
    wind_down = next(r for r in RULES if r.id == "M-02")
    assert preferences_for([wind_down]) == [("tempo_bpm", 60.0, 80.0), ("instrumentalness", 0.5, 1.0)]


def test_prompt_text_lists_each_rule_id():
    text = prompt_text(match_rules(RULES, RAINY_NIGHT))
    for rule_id in ["M-00", "M-02", "M-05", "M-08", "M-09", "M-10", "M-11"]:
        assert f"[{rule_id}]" in text


def test_bad_rule_is_rejected(tmp_path):
    bad = tmp_path / "manual.md"
    bad.write_text("## M-01 · Broken\n- when: always\n- nudge: energy -0.9\n")
    with pytest.raises(ValueError):
        load_manual(str(bad))
