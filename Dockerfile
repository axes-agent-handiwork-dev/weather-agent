# The agent image Chat Plot runs, one step per container invocation.
# Pin the platform: Chat Plot's VMs are amd64, so the image must be amd64 even
# when built on an arm64 machine (e.g. Apple Silicon). Without this a native
# build yields an arm64 image that fails on the VM with "exec format error".
FROM --platform=linux/amd64 python:3.12-slim

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
