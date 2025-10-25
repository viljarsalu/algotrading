# Multi-stage Dockerfile for dYdX Trading Service

# Stage 1: Frontend assets build (Tailwind CSS)
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY backend/package*.json ./
COPY ../tailwind.config.js ../

# Install dependencies
RUN npm install

# Copy source files
COPY backend/src/static/css/input.css ./src/static/css/
COPY backend/src/static/js/ ./src/static/js/

# Build Tailwind CSS
RUN npm run prod

# Stage 2: Python application
FROM python:3.12-slim AS python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        libpq-dev \
        gcc \
        curl \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set work directory
WORKDIR /app

# Copy dependency files
COPY backend/requirements.txt backend/pyproject.toml backend/README.md ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false

# Generate lock file if needed and install dependencies
RUN poetry lock --no-interaction && poetry install --no-interaction --no-ansi

# Copy application code
COPY backend/src/ ./src/
COPY backend/src/templates/ ./templates/

# Copy built frontend assets from previous stage
COPY --from=frontend-builder /app/frontend/src/static/css/output.css ./src/static/css/
COPY --from=frontend-builder /app/frontend/src/static/js/ ./src/static/js/

# Create non-root user
RUN addgroup --system appuser && adduser --system appuser --ingroup appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command with environment variable
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port 8000"]

# Stage 3: Development image
FROM python-base AS development

# Switch back to root for development
USER root

# Install development dependencies
RUN poetry install --no-interaction --no-ansi

# Create logs directory
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch back to appuser
USER appuser

# Mount point for development
VOLUME ["/app"]

# Development start command with reload
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src"]

# Create logs directory
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Production start command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
