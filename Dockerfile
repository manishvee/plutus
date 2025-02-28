# Build stage
FROM python:3.13-slim-bookworm AS builder

# Set working directory
WORKDIR /app

# Install build dependencies and poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && export PATH="/root/.local/bin:$PATH" \
    && poetry config virtualenvs.create false \
    && poetry config installer.max-workers 4

# Copy application code
COPY pyproject.toml poetry.lock ./
COPY plutus/ ./plutus/

# Install the application with poetry and then remove poetry and build dependencies
RUN export PATH="/root/.local/bin:$PATH" \
    && poetry build \
    && poetry install --no-interaction --no-ansi \
    && pip install dist/plutus-*.tar.gz \
    && rm -rf ./dist \
    && rm -rf /root/.cache/pip/* \
    && rm -rf /root/.local/share/pypoetry \
    && rm -rf /root/.cache/poetry \
    && rm -rf /root/.local/bin/poetry \
    && apt-get purge -y gcc python3-dev curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Final stage
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=plutus \
    FLASK_ENV=production \
    PYTHONPATH=/app

# Copy installed package and binaries from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Create non-root user with minimal privileges
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin -d /app appuser \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /usr/local/lib/python3.13/site-packages \
    && chown -R appuser:appuser /usr/local/bin

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "plutus:create_app()"]