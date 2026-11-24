from datetime import datetime

from src.context import PLACES, WEATHER, Moment
from src.history import (
    AVOIDED_GENRE_PENALTY,
    FAMILIAR_BONUS,
    MAX_STRENGTH,
    PERSONAS,
    Play,
    blend,
    load_history,
    plays_for,
    profile_for,
    rerank,
)
from src.retrieval import LocalCatalog
from src.vibe import recommend_for_moment

SONGS = {s["id"]: s for s in LocalCatalog().songs}
PLAYS = load_history()


def play(song_id, hour=22, weather="rainy", place="home", completed=True):
    return Play("test", datetime(2026, 10, 1, hour), song_id, place, weather, completed)


def test_demo_history_has_three_valid_personas():
    assert {p.persona for p in PLAYS} == set(PERSONAS)
    assert all(p.song_id in SONGS and p.place in PLACES and p.weather in WEATHER for p in PLAYS)
    for persona in PERSONAS:
        assert 200 <= len(plays_for(PLAYS, persona)) <= 450


def test_student_rainy_nights_are_quiet_and_acoustic():
    student = plays_for(PLAYS, "student")
    rainy = profile_for(student, SONGS, 22, "rainy", "home")
    sunny = profile_for(student, SONGS, 22, "sunny", "home")
    assert rainy.centroid["energy"] < 0.3 and rainy.centroid["acousticness"] > 0.7
    assert rainy.centroid["acousticness"] > sunny.centroid["acousticness"]  # the weather matters
    assert "low energy" in rainy.summary() and "acoustic" in rainy.summary()


def test_gym_evenings_are_loud_and_electronic():
    gym = profile_for(plays_for(PLAYS, "gym_goer"), SONGS, 18, "sunny", "gym")
    assert gym.centroid["energy"] > 0.7 and gym.centroid["acousticness"] < 0.2


def test_no_similar_plays_means_no_influence():
    profile = profile_for([play(1, hour=8, weather="sunny", place="gym")], SONGS, 22, "rainy", "home")
    assert profile.strength == 0 and profile.centroid is None
    stated = {"energy": 0.5, "valence": 0.5, "acousticness": 0.5}
    assert blend(stated, profile) == stated


def test_strength_grows_with_similar_plays_and_stays_capped():
    few = profile_for([play(1)] * 5, SONGS, 22, "rainy", "home")
    many = profile_for([play(1)] * 500, SONGS, 22, "rainy", "home")
    assert 0 < few.strength < many.strength < MAX_STRENGTH
    assert many.centroid["energy"] == SONGS[1]["energy"]


def test_blend_moves_toward_history_by_the_strength():
    profile = profile_for([play(1)] * 20, SONGS, 22, "rainy", "home")  # 20 plays -> half of the maximum
    assert profile.strength == MAX_STRENGTH / 2
    stated = {"energy": 0.0, "valence": 0.0, "acousticness": 0.0}
    assert blend(stated, profile)["energy"] == round(profile.strength * SONGS[1]["energy"], 3)


def test_often_skipped_means_skipped_more_than_finished():
    plays = [play(1, completed=False)] * 2 + [play(2, completed=False)] * 2 + [play(2)] * 3
    profile = profile_for(plays, SONGS, 22, "rainy", "home")
    assert profile.skipped == {1}
    assert profile.familiar == {2}


def test_rerank_moves_familiar_up_and_skipped_and_avoided_down():
    a, b, c = SONGS[1], SONGS[2], SONGS[3]
    profile = profile_for([play(3)] * 3 + [play(1, completed=False)] * 2, SONGS, 22, "rainy", "home")
    ranked = rerank([(a, 0.10), (b, 0.12), (c, 0.14)], profile)
    assert [s["id"] for s, _ in ranked] == [3, 2, 1]  # 3: 0.14 - 0.05 · 2: 0.12 · 1: 0.10 + 0.10
    assert dict((s["id"], d) for s, d in ranked)[3] == round(0.14 - FAMILIAR_BONUS, 3)
    avoided = rerank([(a, 0.10), (b, 0.12)], None, genres_avoid=[a["genre"]])
    assert avoided[0][0]["id"] == 2 and avoided[1][1] == round(0.10 + AVOIDED_GENRE_PENALTY, 3)


def test_same_moment_gives_each_persona_different_picks():
    moment = Moment(hour=22, weather="rainy", note="rainy night, need to focus")
    picks = {persona: {p.song["id"] for p in recommend_for_moment(moment, history=plays_for(PLAYS, persona)).explanation.picks}
             for persona in PERSONAS}
    assert picks["student"] != picks["gym_goer"] != picks["night_owl"] != picks["student"]
