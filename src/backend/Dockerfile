# Backend Dockerfile for TechGiterview
# Multi-stage build: Base + Development/Production variants

# ================================
# Base Stage: Common setup
# ================================
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv globally
RUN pip install --no-cache-dir uv

# Create application user early
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# ================================
# Dependencies Stage: Install packages
# ================================
FROM base as dependencies

# Create virtual environment with proper ownership
RUN uv venv .venv && \
    chown -R app:app .venv

# Install dependencies with fallback strategy
RUN uv sync --frozen || \
    (echo "uv sync failed, trying manual install..." && \
     .venv/bin/pip install --upgrade pip && \
     .venv/bin/pip install --no-cache-dir \
        uvicorn[standard] \
        fastapi \
        aiohttp \
        aioredis \
        aiosqlite \
        asyncpg \
        chardet \
        chromadb \
        google-generativeai \
        langchain \
        langchain-core \
        langchain-google-genai \
        langgraph \
        langsmith \
        lizard \
        networkx \
        psycopg2-binary \
        pydantic \
        pydantic-settings \
        python-multipart \
        redis \
        scipy \
        sqlalchemy \
        tiktoken)

# Verify installation
RUN .venv/bin/python -c "import uvicorn, fastapi; print('Core dependencies OK')" && \
    .venv/bin/python -c "import langchain, google.generativeai; print('AI dependencies OK')"

# ================================
# Development Stage: For development with hot-reload
# ================================
FROM dependencies as development

# Copy application code
COPY --chown=app:app . .

# Set proper permissions
RUN chown -R app:app /app

# Environment variables for development
ENV PYTHONPATH="/app"
ENV DATABASE_PATH="/app/techgiterview_dev.db"
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV ENV="development"
ENV DEBUG="true"

# Switch to app user
USER app

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Development command with hot-reload
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

# ================================
# Production Stage: Optimized for production
# ================================
FROM dependencies as production

# Copy application code
COPY --chown=app:app . .

# Set proper permissions
RUN chown -R app:app /app

# Environment variables for production
ENV PYTHONPATH="/app"
ENV DATABASE_PATH="/app/techgiterview_prod.db"
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV ENV="production"
ENV DEBUG="false"

# Switch to app user
USER app

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Production command with workers
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4"]