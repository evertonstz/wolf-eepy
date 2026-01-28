# Using python 3.14 as base image
FROM python:3.14-slim

# 1. Install systemd and curl (needed for UV install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    systemd curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Install latest UV from official installer
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:${PATH}"

# Prevents Python from writing .pyc files to the container
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures logs are sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 3. Copy only config first to take advantage of Docker layer caching
COPY pyproject.toml uv.lock .python-version ./

# 4. Set up venv and install dependencies using uv only
RUN uv venv && uv sync

# 5. Copy in the rest of the code
COPY . .

HEALTHCHECK --interval=30s --timeout=6s --start-period=60s --retries=3 \
  CMD uv run wolf-healthcheck || exit 1

CMD ["uv", "run", "wolf-eepy"]
