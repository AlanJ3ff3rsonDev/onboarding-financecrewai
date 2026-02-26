FROM python:3.13-slim

# System deps for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash appuser

# Install uv (pinned version)
COPY --from=ghcr.io/astral-sh/uv:0.6.3 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (layer caching)
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies (frozen = uses lock file exactly)
RUN uv sync --frozen --no-dev --no-install-project

# Install Playwright Chromium (as root, then fix ownership)
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers
RUN uv run playwright install chromium \
    && chown -R appuser:appuser /opt/pw-browsers

# Copy application code
COPY backend/app/ app/

# Give appuser ownership of /app (needed for SQLite database file)
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run server
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
