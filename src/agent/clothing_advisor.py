"""The clothing-advisor subagent: an LLM that reasons about what to wear."""

from __future__ import annotations

from typing import Any

from axes.agent import Agent, ChatMessage, Finish, PlanResult
from pydantic import BaseModel


class ClothingArguments(BaseModel):
    """The conditions handed to the clothing advisor."""

    highTemperatureCelsius: float
    lowTemperatureCelsius: float
    precipitationProbability: int
    windSpeedKilometersPerHour: float


class ClothingContent(BaseModel):
    """The advisor's recommendation: free text."""

    advice: str


class ClothingAdvisor(Agent):
    """LLM subagent: given the day's conditions, advise what to wear.

    Pure judgment — no tools. Uses the default ``plan_step`` loop, re-keying
    the default ``{"text": ...}`` finish to ``{"advice": ...}`` — the model's
    free text is the recommendation.
    """

    name = "clothing_advisor"
    description = "Advise what to wear given the day's forecast conditions."
    arguments_schema = ClothingArguments
    content_schema = ClothingContent

    def plan_step(self, messages: list[ChatMessage]) -> PlanResult:
        # The default finish wraps the model's free text as {"text": ...};
        # re-key it to this agent's content contract.
        plan = super().plan_step(messages)
        if isinstance(plan, Finish):
            return Finish(
                reason=plan.reason,
                content={"advice": (plan.content or {}).get("text", "")},
            )
        return plan

    def prompt_context(self) -> dict[str, Any]:
        a = self.arguments
        return {
            "highTemperatureCelsius": a.highTemperatureCelsius,
            "lowTemperatureCelsius": a.lowTemperatureCelsius,
            "precipitationProbability": a.precipitationProbability,
            "windSpeedKilometersPerHour": a.windSpeedKilometersPerHour,
        }
