# weather-agent

A reference [Chat Plot](../chat-plot) agent image built on the agent framework
in [`axes-client`](../axes-client) (`axes.agent`). It reports a place's weather
today and what to wear, using [Open-Meteo](https://open-meteo.com) (keyless, no
API key in the image).

It exercises both `plan_step` paths:

- **`WeatherAgent`** (root) — **procedural**, no LLM. A small state machine over
  history: fetch the forecast (leaf tool), get clothing advice (subagent), then
  combine into a `WeatherContent` returned as the finished `content`.
- **`ClothingAdvisor`** (subagent) — **LLM-driven**. Given the conditions, it
  reasons about what to wear; Chat Plot derives its `ClothingContent` from the
  model's final message.

## Layout

A `src/agent` package — the base for real agents, not a single file. The
package is named `agent` and exposes `root`, so the framework's default
`agent:root` resolves with no configuration.

| path                        | role                                        |
| --------------------------- | ------------------------------------------- |
| `src/agent/weather.py`      | `WeatherAgent`, the procedural root         |
| `src/agent/clothing_advisor.py` | `ClothingAdvisor`, the LLM subagent     |
| `src/agent/tools.py`        | `GetForecast`, the leaf tool                |
| `src/agent/prompt.md`       | the `ClothingAdvisor` system prompt (Jinja) |
| `src/agent/__init__.py`     | exposes `root`                              |

No `__main__`, no config. Schema/tool attributes are plain class assignments;
the base classes declare them `ClassVar`, so authored subclasses never need to.

## Develop

```bash
uv sync
```

## Run a step locally

```bash
uv run axes-agent <<'JSON'
{"verb": "plan_step", "arguments": {"location": "Paris"}, "messages": []}
JSON
```

Step 1 emits a `get_forecast` tool call; feed the result back to get the
`clothing_advisor` call; feed that back to get the finished report. Or exercise
the leaf tool directly:

```bash
uv run axes-agent <<'JSON'
{"verb": "run_tool", "tool_call": {"name": "get_forecast",
 "arguments": {"location": "Paris"}}}
JSON
```

## Build the image

The image installs from `uv.lock` with `uv sync --frozen`. That lock currently
pins `axes-client` via the local `[tool.uv.sources]` override; once it is
published, drop that override and re-run `uv lock` so the lock resolves from
PyPI — then:

The Dockerfile pins `--platform=linux/amd64` (Chat Plot's VMs are amd64), so a
plain `docker build` on any host produces an amd64 image:

```bash
docker build -t weather-agent .
echo '{"verb":"run_tool","tool_call":{"name":"get_forecast","arguments":{"location":"Paris"}}}' \
  | docker run -i --rm weather-agent
```
