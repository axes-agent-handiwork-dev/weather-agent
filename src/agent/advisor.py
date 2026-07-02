"""The clothing-advisor subagent: an LLM that reasons about what to wear."""

from __future__ import annotations

from typing import Any

from axes.agent import Agent

from agent.schemas import ClothingArguments, ClothingContent


class ClothingAdvisor(Agent):
    """LLM subagent: given the day's conditions, advise what to wear.

    Pure judgment — no tools. Uses the default ``plan_step``; its ``content``
    (a ``ClothingContent``) is produced by the model and mapped by Chat Plot.
    """

    name = "clothing_advisor"
    description = "Advise what to wear given the day's forecast conditions."
    arguments_schema = ClothingArguments
    content_schema = ClothingContent

    def prompt_context(self) -> dict[str, Any]:
        a = self.arguments
        return {
            "high_c": a.high_c,
            "low_c": a.low_c,
            "precip_prob": a.precip_prob,
            "wind_kph": a.wind_kph,
        }
