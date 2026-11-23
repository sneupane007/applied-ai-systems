import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from src.context import Moment
from src.explainer import MODEL, ReasonerError
from src.intent import SCHEMA, UNKNOWN, ClaudeIntentParser, TextIntent, clean, fill, keyword_parse, read_prompt


def read(text):
    return clean(keyword_parse(text))


@pytest.mark.parametrize("text, expected", [
    ("rainy night, need to focus, no lyrics", dict(goal="focus", weather="rainy", instrumental=True)),
    ("pump me up at the gym, some hip hop, no country",
     dict(goal="energize", place="gym", genres_like=["hip-hop"], genres_avoid=["country"])),
    ("feeling down and lonely", dict(mood_card="rainy_window")),
    ("wind down for sleep", dict(goal="calm")),
    ("storm outside and I'm angry", dict(mood_card="storm", weather="stormy")),
    ("r&b and jazz please, don't want metal", dict(genres_like=["jazz", "r-n-b"], genres_avoid=["metal"])),
    ("exhausted, something cozy", dict(mood_card="cozy_blanket", energy_level="Drained")),
])
def test_keywords(text, expected):
    intent = read(text)
    for name, value in expected.items():
        got = getattr(intent, name)
        assert (sorted(got) if isinstance(got, list) else got) == value, name


def test_nothing_too_sad_is_a_request_not_a_sad_mood():
    intent = read("nothing too sad, just cozy")
    assert intent.avoid_sad and intent.mood_card == "cozy_blanket"
    assert read("not sad at all").mood_card is None


def test_clean_drops_unknown_values_and_conflicts():
    intent = clean({"mood_card": "volcano", "goal": UNKNOWN, "place": "gym", "weather": "hail",
                    "instrumental": "yes", "genres_like": ["jazz", "jazz", "polka"], "genres_avoid": ["jazz", "metal"]})
    assert intent == TextIntent(place="gym", genres_like=["jazz"], genres_avoid=["metal"])


def test_fill_only_sets_what_the_listener_left_on_auto():
    moment, from_prompt = fill(Moment(hour=9, place="home"), TextIntent(place="gym", goal="energize"))
    assert moment.place == "home" and moment.goal == "energize"
    assert from_prompt == ["goal"]


# --- ClaudeIntentParser with a fake client (no network) ---

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


ANSWER = {"mood_card": "rainy_window", "energy_level": UNKNOWN, "goal": "focus", "place": UNKNOWN, "weather": UNKNOWN,
          "instrumental": True, "avoid_sad": False, "genres_like": ["piano"], "genres_avoid": []}
REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def test_claude_parser_sends_the_form_and_a_strict_schema():
    client = FakeClient(response(ANSWER))
    parser = ClaudeIntentParser(client=client)
    intent, mode, notes = read_prompt("melancholy piano to study to", parser)
    assert mode == "ai" and notes == []
    assert intent == TextIntent(mood_card="rainy_window", goal="focus", instrumental=True, genres_like=["piano"])
    assert client.kwargs["model"] == MODEL
    assert client.kwargs["output_config"]["format"] == {"type": "json_schema", "schema": SCHEMA}
    assert "melancholy piano to study to" in client.kwargs["messages"][0]["content"]
    assert UNKNOWN in SCHEMA["properties"]["place"]["enum"] and SCHEMA["additionalProperties"] is False
    assert parser.last_request_id == "req_test"


@pytest.mark.parametrize("client", [
    FakeClient(error=anthropic.APIConnectionError(request=REQUEST)),
    FakeClient(error=anthropic.RateLimitError("slow", response=httpx2.Response(429, request=REQUEST), body=None)),
    FakeClient(response(ANSWER, stop_reason="refusal")),
    FakeClient(response("not json")),
])
def test_claude_failures_fall_back_to_keywords(client):
    intent, mode, notes = read_prompt("need to focus", ClaudeIntentParser(client=client))
    assert mode == "keywords" and intent.goal == "focus"
    assert len(notes) == 1 and "keywords were used" in notes[0]


def test_claude_errors_become_reasoner_errors():
    with pytest.raises(ReasonerError):
        ClaudeIntentParser(client=FakeClient(error=anthropic.APIConnectionError(request=REQUEST))).parse("hi")


def test_empty_prompt_is_not_read_at_all():
    class NeverCalled:
        def parse(self, text):
            raise AssertionError("the parser should not be called")

    assert read_prompt("   ", NeverCalled()) == (TextIntent(), "none", [])
