"""
All live weather I/O lives here, and ONLY here. This module never calls an
LLM and the LLM never calls an external API directly — the graph nodes that
wrap these functions are the sole boundary between "facts" (this module) and
"language" (the LLM nodes in graph.py). This is what makes the
"numbers must come from the API, not the model" non-negotiable enforceable:
grep the repo for requests.get and you'll find it only here.
"""
from __future__ import annotations

from typing import Any, Optional

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

CURRENT_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
    "wind_gusts_10m",
    "uv_index",
]
HOURLY_FIELDS = [
    "temperature_2m",
    "precipitation_probability",
    "precipitation",
    "wind_speed_10m",
    "wind_gusts_10m",
    "uv_index",
    "weather_code",
]
DAILY_FIELDS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "uv_index_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
]

REQUEST_TIMEOUT_SECONDS = 8


class GeocodeError(Exception):
    """Raised when a location can't be resolved — caller must fail honestly."""


class WeatherAPIError(Exception):
    """Raised when the forecast API is unreachable or errors — caller must fail honestly."""


def geocode_location(name: str) -> dict[str, Any]:
    """Resolve a free-text place name to coordinates.

    Returns dict with lat, lon, resolved_name. Raises GeocodeError if the
    location can't be resolved (no results OR the request itself failed) —
    both cases are treated identically per the spec: a "can't resolve a
    location" failure, not a half-answer.
    """
    try:
        resp = requests.get(
            GEOCODE_URL,
            params={"name": name, "count": 5, "language": "en", "format": "json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise GeocodeError(f"Geocoding request failed for '{name}': {exc}") from exc

    results = data.get("results")
    if not results:
        raise GeocodeError(f"No geocoding results for '{name}'.")

    top = results[0]  # picking the first candidate silently, per spec
    return {
        "lat": top["latitude"],
        "lon": top["longitude"],
        "resolved_name": ", ".join(
            filter(None, [top.get("name"), top.get("admin1"), top.get("country")])
        ),
    }


def fetch_forecast(lat: float, lon: float) -> dict[str, Any]:
    """Fetch current + hourly + daily forecast fields for a coordinate.

    Raises WeatherAPIError on any network/HTTP/parse failure — caller must
    fail honestly rather than guess.
    """
    try:
        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": ",".join(CURRENT_FIELDS),
                "hourly": ",".join(HOURLY_FIELDS),
                "daily": ",".join(DAILY_FIELDS),
                "timezone": "auto",
                "forecast_days": 2,  # today + tomorrow, covers "this evening" follow-ups
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise WeatherAPIError(f"Forecast request failed for ({lat}, {lon}): {exc}") from exc

    if "current" not in data:
        # Metadata-only response (e.g. missing field list) — treat as a failure,
        # not a silent empty answer.
        raise WeatherAPIError(f"Forecast response missing 'current' data: {data}")

    return data


def resolve_and_fetch(location_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convenience wrapper: geocode then fetch. Returns (location_info, forecast_data)."""
    location_info = geocode_location(location_name)
    forecast = fetch_forecast(location_info["lat"], location_info["lon"])
    return location_info, forecast
