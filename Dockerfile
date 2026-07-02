# The agent image Chat Plot runs, one step per container invocation.
FROM python:3.12-slim

# The uv binary, copied from the official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# TEMPORARY: axes-client is pulled from a private GitHub repo over SSH (see
# [tool.uv.sources] in pyproject.toml). uv needs a `git` binary to clone it,
# and github.com must be a known host for the SSH clone to succeed.
# Once axes-client is published to PyPI, drop the source override, re-run
# `uv lock`, and this git/ssh scaffolding can be removed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git openssh-client \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p -m 0700 /root/.ssh \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts

# Install the locked dependency set (pyproject + uv.lock are the single source
# of truth). Manifests and sources are needed to build/install the package;
# copied before the lockstep so the layer caches across code edits.
# --mount=type=ssh forwards the host SSH agent for the private git clone only;
# no keys are baked into the image. Build with: docker build --ssh default ...
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN --mount=type=ssh uv sync --frozen --no-dev --no-editable

# Run the framework console script from the synced environment. The package is
# named `agent` and exposes `root`, so the default `agent:root` resolves with no
# AXES_AGENT needed.
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["axes-agent"]
