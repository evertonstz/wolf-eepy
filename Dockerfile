# Using python 3.14 as base image
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

# 1. Install systemd and curl (needed for UV install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    systemd \
    && rm -rf /var/lib/apt/lists/*

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY README.md /app
COPY LICENSE /app
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

HEALTHCHECK --interval=30s --timeout=6s --start-period=60s --retries=3 \
  CMD uv run wolf-eepy-healthcheck || exit 1

# Use uv to run the project entrypoint (keeps uv semantics and venv handling)
CMD ["uv", "run", "wolf-eepy-monitor"]
