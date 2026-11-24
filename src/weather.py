"""Current weather and local hour for a city, from Open-Meteo.

Open-Meteo is free for non-commercial use with no API key (under 10,000 calls a day;
data under CC-BY 4.0; place names from GeoNames). The city is sent only here, never to the AI.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 5
CITY_MAX = 80


@dataclass
class Conditions:
    weather: str  # one of context.WEATHER
    hour: int     # local hour in that city, 0-23


def category_for(code: int) -> str:
    """Map a WMO weather code to one of: sunny, cloudy, foggy, rainy, snowy, stormy."""
    if code in (0, 1):
        return "sunny"
    if code in (45, 48):
        return "foggy"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "rainy"
    if 71 <= code <= 77 or code in (85, 86):
        return "snowy"
    if code >= 95:
        return "stormy"
    return "cloudy"


def get_conditions(city: str) -> Tuple[Optional[Conditions], str]:
    """Return (conditions, "") on success, or (None, a reason to show the user)."""
    city = city.strip()
    if not city:
        return None, "No city given, so weather is skipped."
    if len(city) > CITY_MAX:
        return None, f"City names must be {CITY_MAX} characters or fewer, so weather is skipped."
    try:
        geo = requests.get(GEOCODE_URL, params={"name": city, "count": 1, "language": "en", "format": "json"},
                           timeout=TIMEOUT_SECONDS)
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            return None, "Couldn't find that city, so weather is skipped."
        place = results[0]
        forecast = requests.get(FORECAST_URL, params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "weather_code",
            "timezone": "auto",
        }, timeout=TIMEOUT_SECONDS)
        forecast.raise_for_status()
        current = forecast.json()["current"]
        hour = datetime.fromisoformat(current["time"]).hour  # local time, because timezone=auto
        return Conditions(category_for(int(current["weather_code"])), hour), ""
    except requests.Timeout:
        return None, "The weather service took too long, so weather is skipped."
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None, "Couldn't get the weather right now, so it's skipped."
