"""Leaf tools: work that runs in-container during ``run_tool``."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from axes.agent import RunContext, Tool
from pydantic import BaseModel

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2


class ForecastArguments(BaseModel):
    """Input to the forecast tool."""

    location: str


class ForecastContent(BaseModel):
    """A day's conditions for one place."""

    place: str
    highTemperatureCelsius: float
    lowTemperatureCelsius: float
    precipitationProbability: int
    windSpeedKilometersPerHour: float


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    for attempt in range(REQUEST_ATTEMPTS):
        try:
            with urllib.request.urlopen(f"{url}?{query}", timeout=10) as resp:
                data: dict[str, Any] = json.load(resp)
            return data
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == REQUEST_ATTEMPTS - 1:
                raise
            time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise RuntimeError("unreachable")


class GetForecast(Tool[ForecastArguments, ForecastContent]):
    description = "Get today's forecast (temps, rain, wind) for a place."
    arguments_schema = ForecastArguments
    content_schema = ForecastContent

    async def run(
        self, arguments: ForecastArguments, ctx: RunContext
    ) -> ForecastContent:
        geo = _get_json(GEOCODE_URL, {"name": arguments.location, "count": 1})
        matches = geo.get("results")
        if not matches:
            raise ValueError(f"unknown location: {arguments.location!r}")
        place = matches[0]
        data = _get_json(
            FORECAST_URL,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": (
                    "temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,wind_speed_10m_max"
                ),
                "timezone": "auto",
            },
        )
        daily = data["daily"]
        country = place.get("country")
        name = place["name"]
        return ForecastContent(
            place=f"{name}, {country}" if country else name,
            highTemperatureCelsius=daily["temperature_2m_max"][0],
            lowTemperatureCelsius=daily["temperature_2m_min"][0],
            precipitationProbability=daily["precipitation_probability_max"][0]
            or 0,
            windSpeedKilometersPerHour=daily["wind_speed_10m_max"][0],
        )
