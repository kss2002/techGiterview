# Backend Dockerfile for TechGiterview
# Python + uv 기반 FastAPI 애플리케이션 - 단일 스테이지

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy uv configuration files
COPY pyproject.toml uv.lock* ./

# Create virtual environment explicitly and install dependencies
RUN uv sync

# Verify uvicorn installation
RUN .venv/bin/python -c "import uvicorn; print('uvicorn successfully installed')"
RUN ls -la .venv/bin/uvicorn

# Copy application code
COPY --chown=app:app . .

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R app:app /app/data

# Set environment variables
ENV PYTHONPATH="/app"
ENV DATABASE_PATH="/app/techgiterview_dev.db"
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Switch to non-root user
USER app

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Command to run the application using python -m uvicorn as backup
# Primary: absolute path to uvicorn
# Backup: python -m uvicorn
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]