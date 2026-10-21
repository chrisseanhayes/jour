FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nano \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY jour_cli/ ./jour_cli/

# Install into a venv so pip --user quirks are avoided in a container
RUN python3 -m venv /opt/jour-venv \
    && /opt/jour-venv/bin/pip install --upgrade pip \
    && /opt/jour-venv/bin/pip install -e .

ENV PATH="/opt/jour-venv/bin:$PATH"
ENV EDITOR="nano"

# Copy test suite
COPY tests/ ./tests/

CMD ["sh", "tests/smoke.sh"]
