import pytest
import requests

from src import weather
from src.weather import category_for, get_conditions


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status = payload, status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"HTTP {self.status}")

    def json(self):
        return self.payload


def fake_get(geo_payload, forecast_payload=None, calls=None):
    def get(url, params=None, timeout=None):
        if calls is not None:
            calls.append((url, params, timeout))
        return FakeResponse(geo_payload if "geocoding" in url else forecast_payload)
    return get


BOSTON = {"results": [{"name": "Boston", "latitude": 42.36, "longitude": -71.06}]}


@pytest.mark.parametrize("code, expected", [
    (0, "sunny"), (1, "sunny"), (2, "cloudy"), (3, "cloudy"), (45, "foggy"), (53, "rainy"),
    (66, "rainy"), (81, "rainy"), (73, "snowy"), (86, "snowy"), (95, "stormy"), (99, "stormy"),
])
def test_weather_codes_map_to_categories(code, expected):
    assert category_for(code) == expected


def test_success_returns_category_and_local_hour(monkeypatch):
    calls = []
    forecast = {"utc_offset_seconds": -18000, "current": {"time": "2026-11-21T23:15", "weather_code": 63}}
    monkeypatch.setattr(weather.requests, "get", fake_get(BOSTON, forecast, calls))
    conditions, reason = get_conditions("  Boston ")
    assert conditions == weather.Conditions("rainy", 23) and reason == ""
    assert calls[0][1]["name"] == "Boston"
    assert all(timeout == weather.TIMEOUT_SECONDS for _, _, timeout in calls)


@pytest.mark.parametrize("geo_payload", [{}, {"results": []}, {"results": None}])
def test_unknown_city_is_skipped(monkeypatch, geo_payload):
    monkeypatch.setattr(weather.requests, "get", fake_get(geo_payload))
    conditions, reason = get_conditions("zzqqxx")
    assert conditions is None and "Couldn't find that city" in reason


def test_timeout_is_skipped(monkeypatch):
    def slow(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(weather.requests, "get", slow)
    conditions, reason = get_conditions("Boston")
    assert conditions is None and "too long" in reason


def test_bad_responses_are_skipped(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", fake_get(BOSTON, {"unexpected": True}))
    conditions, reason = get_conditions("Boston")
    assert conditions is None and "Couldn't get the weather" in reason


@pytest.mark.parametrize("city", ["", "   ", "x" * 81])
def test_empty_or_long_city_makes_no_request(monkeypatch, city):
    def never(*args, **kwargs):
        raise AssertionError("should not call the network")
    monkeypatch.setattr(weather.requests, "get", never)
    conditions, reason = get_conditions(city)
    assert conditions is None and reason
