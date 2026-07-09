"""The procedural root agent: fetch the forecast, get advice, combine.

No LLM at this level. Each step reads history to decide the next action; the
control plane runs it and appends the result. This is a small state machine
over history, not an inline script — the leaf tool and the subagent are
dispatched by Chat Plot *between* step invocations. The finished report is
returned as ``content``.
"""

from __future__ import annotations

import json

from axes.agent import (
    Agent,
    ChatMessage,
    Finish,
    Message,
    PlanResult,
    ToolCall,
)
from pydantic import BaseModel

from agent.clothing_advisor import ClothingAdvisor
from agent.tools import GetForecast


class WeatherArguments(BaseModel):
    """How the weather agent is invoked."""

    location: str
    when: str = "today"


class WeatherContent(BaseModel):
    """What a completed weather report returns."""

    summary: str
    highTemperatureCelsius: float
    lowTemperatureCelsius: float
    advice: str


class WeatherAgent(Agent):
    name = "weather"
    description = "Report a place's weather today and what to wear."
    arguments_schema = WeatherArguments
    content_schema = WeatherContent
    prompts = []
    tools = {
        "get_forecast": GetForecast(),
        "clothing_advisor": ClothingAdvisor(),
    }

    def plan_step(self, messages: list[ChatMessage]) -> PlanResult:
        # Chat Plot maps a tool/subagent result into a ``tool``-role message
        # whose ``name`` is the tool and whose ``content`` is its result JSON.
        results = {
            m.name: json.loads(m.content)
            for m in messages
            if m.role == "tool" and m.name and m.content
        }
        forecast = results.get("get_forecast")
        if forecast is None:
            # Step 1: fetch the forecast.
            return Message(
                tool_calls=[
                    ToolCall(
                        name="get_forecast",
                        arguments={"location": self.arguments.location},
                    )
                ]
            )
        if "highTemperatureCelsius" not in forecast:
            # The tool returned an error payload rather than a forecast;
            # surface it instead of KeyError-ing on the missing fields.
            reason = (
                forecast.get("error") or "get_forecast returned no forecast"
            )
            return Finish(reason="get_forecast failed", error=reason)
        advice = results.get("clothing_advisor")
        if advice is None:
            # Step 2: hand the conditions to the clothing_advisor subagent.
            return Message(
                tool_calls=[
                    ToolCall(
                        name="clothing_advisor",
                        arguments={
                            "highTemperatureCelsius": forecast[
                                "highTemperatureCelsius"
                            ],
                            "lowTemperatureCelsius": forecast[
                                "lowTemperatureCelsius"
                            ],
                            "precipitationProbability": forecast[
                                "precipitationProbability"
                            ],
                            "windSpeedKilometersPerHour": forecast[
                                "windSpeedKilometersPerHour"
                            ],
                        },
                    )
                ]
            )
        if "advice" not in advice:
            # The subagent returned an error payload rather than a
            # recommendation; surface it instead of KeyError-ing on the
            # missing field.
            reason = (
                advice.get("error") or "clothing_advisor returned no advice"
            )
            return Finish(reason="clothing_advisor failed", error=reason)
        # Step 3: combine imperatively into the finished report.
        report = WeatherContent(
            summary=(
                f"{forecast['place']} {self.arguments.when}: "
                f"{forecast['lowTemperatureCelsius']:.0f}–"
                f"{forecast['highTemperatureCelsius']:.0f}°C, "
                f"{forecast['precipitationProbability']}% chance of rain."
            ),
            highTemperatureCelsius=forecast["highTemperatureCelsius"],
            lowTemperatureCelsius=forecast["lowTemperatureCelsius"],
            advice=advice["advice"],
        )
        return Finish(reason="report assembled", content=report.model_dump())
