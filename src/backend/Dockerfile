# Backend Dockerfile for TechGiterview
# Python + uv 기반 FastAPI 애플리케이션

# Multi-stage build for optimization
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy uv configuration files
COPY pyproject.toml uv.lock* ./

# Install dependencies with uv
RUN uv sync --frozen

# Production stage
FROM python:3.11-slim

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --chown=app:app . .

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R app:app /app/data

# Switch to non-root user
USER app

# Set environment variables
ENV PYTHONPATH="/app"
ENV DATABASE_PATH="/app/techgiterview_dev.db"

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]