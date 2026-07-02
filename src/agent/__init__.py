"""A weather-reporting Chat Plot agent image, built on ``axes-agent``.

The image entrypoint is the framework console script (``axes-agent``), which
resolves ``agent:root`` by default — this package is named ``agent`` and
exposes ``root``, so no configuration is needed.
"""

from __future__ import annotations

from agent.weather import WeatherAgent

root = WeatherAgent()

__all__ = ["WeatherAgent", "root"]
