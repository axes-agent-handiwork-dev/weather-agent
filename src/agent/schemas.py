"""The typed contracts for the weather agent and its parts.

Naming is uniform: every ``arguments_schema`` is ``<Name>Arguments`` and every
``content_schema`` is ``<Name>Content`` — for the root agent, the subagent, and
the leaf tool alike.
"""

from __future__ import annotations

from pydantic import BaseModel


class WeatherArguments(BaseModel):
    """How the weather agent is invoked."""

    location: str
    when: str = "today"


class WeatherContent(BaseModel):
    """What a completed weather report returns."""

    summary: str
    high_c: float
    low_c: float
    advice: str
    items: list[str]


class ForecastArguments(BaseModel):
    """Input to the forecast tool."""

    location: str


class ForecastContent(BaseModel):
    """A day's conditions for one place."""

    place: str
    high_c: float
    low_c: float
    precip_prob: int
    wind_kph: float


class ClothingArguments(BaseModel):
    """The conditions handed to the clothing advisor."""

    high_c: float
    low_c: float
    precip_prob: int
    wind_kph: float


class ClothingContent(BaseModel):
    """The advisor's recommendation."""

    advice: str
    items: list[str]
