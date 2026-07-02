"""The procedural root agent: fetch the forecast, get advice, combine.

No LLM at this level. Each step reads history to decide the next action; the
control plane runs it and appends the result. This is a small state machine
over history, not an inline script — the leaf tool and the subagent are
dispatched by Chat Plot *between* step invocations. The finished report is
returned as ``content``.
"""

from __future__ import annotations

import json
from typing import Any

from axes.agent import (
    Agent,
    ChatMessage,
    Finish,
    Message,
    PlanResult,
    ToolCall,
)

from agent.advisor import ClothingAdvisor
from agent.schemas import WeatherArguments, WeatherContent
from agent.tools import GetForecast


def _tool_result(
    messages: list[ChatMessage], tool_name: str
) -> dict[str, Any] | None:
    """The most recent result of ``tool_name`` in history, if any.

    Chat Plot maps a tool/subagent result into a ``tool``-role message whose
    ``name`` is the tool and whose ``content`` is the JSON of its result.
    """
    for m in reversed(messages):
        if m.role == "tool" and m.name == tool_name and m.content:
            parsed: dict[str, Any] = json.loads(m.content)
            return parsed
    return None


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
        forecast = _tool_result(messages, "get_forecast")
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
        advice = _tool_result(messages, "clothing_advisor")
        if advice is None:
            # Step 2: hand the conditions to the clothing_advisor subagent.
            return Message(
                tool_calls=[
                    ToolCall(
                        name="clothing_advisor",
                        arguments={
                            "high_c": forecast["high_c"],
                            "low_c": forecast["low_c"],
                            "precip_prob": forecast["precip_prob"],
                            "wind_kph": forecast["wind_kph"],
                        },
                    )
                ]
            )
        # Step 3: combine imperatively into the finished report.
        report = WeatherContent(
            summary=(
                f"{forecast['place']} {self.arguments.when}: "
                f"{forecast['low_c']:.0f}–{forecast['high_c']:.0f}°C, "
                f"{forecast['precip_prob']}% chance of rain."
            ),
            high_c=forecast["high_c"],
            low_c=forecast["low_c"],
            advice=advice["advice"],
            items=advice["items"],
        )
        return Finish(reason="report assembled", content=report.model_dump())
