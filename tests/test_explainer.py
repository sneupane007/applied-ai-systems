import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from src.explainer import (
    MODEL,
    ClaudeReasoner,
    ReasonerError,
    build_prompt,
    check_picks,
    direction_for,
    explain,
)
from src.manual import load_manual, match_rules

LABELS = ["goal_match", "home", "low_mood", "night", "rain"]
RULES = match_rules(load_manual(), LABELS)
TARGET = {"energy": 0.1, "valence": 0.25, "acousticness": 0.8}
LISTENER = {"mood": "Rainy window", "energy_level": "Low", "goal": "Match my mood", "place": "Home",
            "time_of_day": "night", "weather": "rainy", "labels": LABELS, "note": "just cozy",
            "history": "none", "played_before": []}


def song(id, energy, valence, artist=None):
    return {"id": id, "title": f"Song {id}", "artist": artist or f"Artist {id}", "genre": "folk",
            "energy": energy, "valence": valence, "acousticness": 0.8, "tempo_bpm": 70.0, "instrumentalness": 0.0}


CANDIDATES = [(song(i, energy=0.1 + i * 0.05, valence=v), 0.1 * i)
              for i, v in enumerate([0.1, 0.15, 0.2, 0.22, 0.4, 0.5, 0.6, 0.7], start=1)]


class FakeReasoner:
    def __init__(self, answer=None, error=None):
        self.answer, self.error, self.calls = answer, error, 0

    def propose(self, listener, rules_text, candidates):
        self.calls += 1
        if self.error:
            raise self.error
        return self.answer


def answer(*song_ids, rules=("M-05",)):
    return {"intro": "Cozy picks.", "picks": [{"song_id": i, "rule_ids": list(rules), "reason": f"Fits {i}."}
                                              for i in song_ids]}


def test_check_drops_unknown_songs_and_rules_and_duplicates():
    raw = answer(5, 99, 5, 6, rules=("M-05", "M-77"))
    raw["picks"][0]["reason"] = "x" * 500
    picks, bad_songs, bad_rules = check_picks(raw, CANDIDATES, {r.id for r in RULES})
    assert [p.song["id"] for p in picks] == [5, 6]
    assert bad_songs == [99]
    assert set(bad_rules) == {"M-77"}
    assert all(p.rule_ids == ["M-05"] for p in picks)
    assert len(picks[0].reason) == 300


def test_ai_answer_is_used_when_valid():
    explanation = explain(FakeReasoner(answer(5, 6, 7, 8, 4)), LISTENER, RULES, CANDIDATES, LABELS, "match", TARGET)
    assert explanation.mode == "ai"
    assert explanation.intro == "Cozy picks."
    # Low mood: valence steps up through the set (M-10).
    valences = [p.song["valence"] for p in explanation.picks]
    assert valences == sorted(valences)


def test_too_few_valid_picks_falls_back_to_offline():
    explanation = explain(FakeReasoner(answer(5, 98, 99)), LISTENER, RULES, CANDIDATES, LABELS, "match", TARGET)
    assert explanation.mode == "offline"
    assert explanation.rejected_song_ids == [98, 99]
    assert len(explanation.picks) == 5


@pytest.mark.parametrize("error", [ReasonerError("couldn't reach Claude"), ValueError("bad json"), KeyError("picks")])
def test_reasoner_failures_fall_back_to_offline(error):
    explanation = explain(FakeReasoner(error=error), LISTENER, RULES, CANDIDATES, LABELS, "match", TARGET)
    assert explanation.mode == "offline"
    assert explanation.notes and "offline" in explanation.notes[0]


def test_no_reasoner_means_offline_template_reasons():
    explanation = explain(None, LISTENER, RULES, CANDIDATES, LABELS, "match", TARGET)
    assert explanation.mode == "offline"
    assert all("target" in p.reason for p in explanation.picks)


def test_at_most_two_very_sad_songs_for_low_mood():
    # The AI picks four very sad songs (valence < 0.25); two get swapped for warmer ones.
    explanation = explain(FakeReasoner(answer(1, 2, 3, 4, 5)), LISTENER, RULES, CANDIDATES, LABELS, "match", TARGET)
    very_sad = [p for p in explanation.picks if p.song["valence"] < 0.25]
    assert len(very_sad) == 2
    assert any("Swapped 2" in n for n in explanation.notes)
    assert explanation.picks[-1].song["valence"] == max(p.song["valence"] for p in explanation.picks)


def test_direction_follows_goal_then_mood_then_signals():
    assert direction_for("calm", ["low_mood"]) == ("energy", -1)
    assert direction_for("energize", []) == ("energy", 1)
    assert direction_for("match", ["low_mood"]) == ("valence", 1)
    assert direction_for("match", ["hr_high_resting"]) == ("energy", -1)
    assert direction_for("focus", ["work_study"]) is None


def test_prompt_contains_labels_rules_and_songs():
    prompt = build_prompt(LISTENER, "[M-05] Low mood", CANDIDATES[:2])
    assert "low_mood" in prompt and "[M-05]" in prompt and "id=1 |" in prompt and '"just cozy"' in prompt


# --- ClaudeReasoner with a fake client (no network) ---

class FakeClient:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.kwargs = response, error, None
        self.messages = self

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


def response(payload, stop_reason="end_turn"):
    text = json.dumps(payload) if isinstance(payload, dict) else payload
    return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)],
                           _request_id="req_test")


def test_claude_reasoner_sends_haiku_low_effort_json_schema():
    client = FakeClient(response(answer(5, 6, 7)))
    reasoner = ClaudeReasoner(client=client)
    result = reasoner.propose(LISTENER, "[M-05] Low mood", CANDIDATES)
    assert result["picks"][0]["song_id"] == 5
    assert client.kwargs["model"] == MODEL == "claude-haiku-5-5"
    assert client.kwargs["output_config"]["effort"] == "low"
    assert client.kwargs["output_config"]["format"]["type"] == "json_schema"
    assert reasoner.last_request_id == "req_test"


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_claude_reasoner_rejects_refusals_and_cut_off_answers(stop_reason):
    with pytest.raises(ReasonerError):
        ClaudeReasoner(client=FakeClient(response(answer(5), stop_reason))).propose(LISTENER, "", CANDIDATES)


REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


@pytest.mark.parametrize("error", [
    anthropic.APIConnectionError(request=REQUEST),
    anthropic.RateLimitError("slow down", response=httpx2.Response(429, request=REQUEST), body=None),
    anthropic.AuthenticationError("bad key", response=httpx2.Response(401, request=REQUEST), body=None),
    anthropic.InternalServerError("oops", response=httpx2.Response(500, request=REQUEST), body=None),
])
def test_claude_api_errors_become_reasoner_errors(error):
    with pytest.raises(ReasonerError):
        ClaudeReasoner(client=FakeClient(error=error)).propose(LISTENER, "", CANDIDATES)


def test_unreadable_json_raises_value_error():
    with pytest.raises(ValueError):
        ClaudeReasoner(client=FakeClient(response("not json"))).propose(LISTENER, "", CANDIDATES)
