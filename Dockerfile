# The agent image Chat Plot runs, one step per container invocation.
FROM python:3.12-slim

# The uv binary, copied from the official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install the locked dependency set (pyproject + uv.lock are the single source
# of truth). Manifests and sources are needed to build/install the package;
# copied before the lockstep so the layer caches across code edits.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# Run the framework console script from the synced environment. The package is
# named `agent` and exposes `root`, so the default `agent:root` resolves with no
# AXES_AGENT needed.
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["axes-agent"]
