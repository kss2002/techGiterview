# Backend Dockerfile for TechGiterview
# Optimized multi-stage build for faster builds and reduced timeouts

# ================================
# Base Stage: System setup with caching
# ================================
FROM python:3.11-slim as base

# Set environment variables for faster builds
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies in a single layer with cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    gcc \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Install uv with specific version for reproducibility
RUN pip install --no-cache-dir "uv>=0.1.0"

# Create application user early with consistent IDs
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Set work directory
WORKDIR /app

# Copy dependency files for better layer caching
COPY pyproject.toml uv.lock* ./

# ================================
# Dependencies Stage: Progressive dependency installation
# ================================
FROM base as dependencies

# Create virtual environment with proper ownership
RUN uv venv .venv && \
    chown -R app:app .venv && \
    echo "Virtual environment created successfully"

# Install core dependencies first (fastest to install)
RUN echo "Installing core web dependencies..." && \
    .venv/bin/pip install --upgrade pip setuptools wheel && \
    .venv/bin/pip install --no-cache-dir \
        uvicorn[standard] \
        fastapi \
        pydantic \
        pydantic-settings \
        python-multipart \
        aiohttp \
        sqlalchemy \
    && echo "Core web dependencies installed"

# Install database and cache dependencies (medium speed)
RUN echo "Installing database dependencies..." && \
    .venv/bin/pip install --no-cache-dir \
        aiosqlite \
        asyncpg \
        psycopg2-binary \
        aioredis \
        redis \
    && echo "Database dependencies installed"

# Install AI dependencies (slowest, most likely to timeout)
RUN echo "Installing AI dependencies (this may take a while)..." && \
    .venv/bin/pip install --no-cache-dir \
        google-generativeai \
        langchain \
        langchain-core \
        langchain-google-genai \
        langgraph \
        langsmith \
        tiktoken \
    && echo "AI dependencies installed"

# Install analysis and utility dependencies
RUN echo "Installing analysis dependencies..." && \
    .venv/bin/pip install --no-cache-dir \
        chromadb \
        scipy \
        networkx \
        lizard \
        chardet \
    && echo "Analysis dependencies installed"

# Try uv sync as alternative (faster if uv.lock exists)
RUN echo "Attempting uv sync as backup..." && \
    (uv sync --frozen && echo "uv sync successful") || \
    echo "uv sync failed, using pip installation (this is normal)"

# Verification with timeout protection
RUN echo "Verifying installations..." && \
    timeout 30 .venv/bin/python -c "import uvicorn, fastapi; print('✅ Core web framework OK')" && \
    timeout 30 .venv/bin/python -c "import sqlalchemy, aiosqlite; print('✅ Database libraries OK')" && \
    timeout 30 .venv/bin/python -c "import google.generativeai; print('✅ Gemini AI OK')" && \
    timeout 30 .venv/bin/python -c "import langchain; print('✅ LangChain OK')" && \
    echo "✅ All critical dependencies verified"

# ================================
# Development Stage: For development with hot-reload
# ================================
FROM dependencies as development

# Copy application code
COPY --chown=app:app . .

# Make startup script executable and set proper permissions
RUN chmod +x start.sh && chown -R app:app /app

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

# Development command with startup script
CMD ["./start.sh"]

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