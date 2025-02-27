# Build stage
FROM python:3-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy package configuration and source code
COPY pyproject.toml ./
COPY plutus/ ./plutus/

# Install build dependencies and create wheels for package and all dependencies
RUN pip install --no-cache-dir build wheel \
    && pip wheel --no-cache-dir --wheel-dir /app/wheels -e . flask gunicorn python-dotenv pandas google-cloud-bigquery

# Final stage
FROM python:3-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=plutus \
    FLASK_ENV=production

# Copy wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install the application using wheels and clean up
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels plutus \
    && rm -rf /app/wheels \
    && useradd -m appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "plutus:create_app()"]

