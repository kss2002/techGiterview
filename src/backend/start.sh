#!/bin/bash
# Optimized startup script for TechGiterview backend
# Handles progressive startup with better error reporting

set -e

echo "🚀 Starting TechGiterview Backend..."
echo "======================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for dependency with timeout
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-30}
    
    echo "⏳ Waiting for $service_name ($host:$port)..."
    
    for i in $(seq 1 $timeout); do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $i/$timeout - waiting 1s..."
        sleep 1
    done
    
    echo "❌ $service_name not available after ${timeout}s"
    return 1
}

# Function to verify Python environment
verify_python_env() {
    echo "🐍 Verifying Python environment..."
    
    # Check if virtual environment exists
    if [[ ! -f "/app/.venv/bin/python" ]]; then
        echo "❌ Virtual environment not found at /app/.venv/bin/python"
        echo "📂 Available files in /app:"
        ls -la /app/ || true
        echo "📂 Available files in /app/.venv/bin:"
        ls -la /app/.venv/bin/ || true
        exit 1
    fi
    
    # Check if pip is available
    if [[ ! -f "/app/.venv/bin/pip" ]]; then
        echo "❌ pip not found in virtual environment at /app/.venv/bin/pip"
        echo "📂 Available files in /app/.venv/bin:"
        ls -la /app/.venv/bin/ || true
        exit 1
    fi
    
    # Display environment info
    echo "📊 Environment Information:"
    echo "   Python: $(/app/.venv/bin/python --version)"
    echo "   Pip: $(/app/.venv/bin/pip --version)"
    echo "   Virtual Environment: /app/.venv"
    echo "   Package count: $(/app/.venv/bin/pip list | wc -l) packages"
    
    # Test critical imports with timeout and comprehensive error reporting
    echo "🔍 Testing critical imports..."
    
    timeout 30 /app/.venv/bin/python -c "
import sys
print(f'Python path: {sys.path[:3]}...')

# Test core web framework
try:
    import uvicorn
    print('✅ uvicorn imported successfully')
except ImportError as e:
    print(f'❌ uvicorn import failed: {e}')
    sys.exit(1)

try:
    import fastapi
    print('✅ FastAPI imported successfully')
except ImportError as e:
    print(f'❌ FastAPI import failed: {e}')
    sys.exit(1)

# Test database libraries
try:
    import sqlalchemy
    print('✅ SQLAlchemy imported successfully')
except ImportError as e:
    print(f'⚠️  SQLAlchemy import failed: {e}')

# Test AI libraries (optional, might be slow)
try:
    import google.generativeai
    print('✅ Google Generative AI imported successfully')
except ImportError as e:
    print(f'⚠️  Google Generative AI import failed: {e}')

print('✅ Core dependencies verified - ready to start application')
" || {
        echo "❌ Python environment verification failed"
        echo "🔧 Debugging information:"
        echo "   PYTHONPATH: $PYTHONPATH"
        echo "   PATH: $PATH"
        echo "   Virtual env activation:"
        source /app/.venv/bin/activate && python --version || echo "Failed to activate venv"
        exit 1
    }
}

# Function to initialize database if needed
init_database() {
    echo "🗄️  Initializing database..."
    
    if [[ -f "/app/app/core/init_db.py" ]]; then
        echo "   Running database initialization..."
        /app/.venv/bin/python -c "
try:
    from app.core.init_db import init_database
    init_database()
    print('✅ Database initialization completed')
except Exception as e:
    print(f'⚠️  Database initialization failed: {e}')
    print('   This might be normal if database already exists')
" || echo "   Database initialization skipped (might already exist)"
    else
        echo "   Database initialization script not found, skipping..."
    fi
}

# Function to start the application with progressive timeouts
start_application() {
    echo "🌟 Starting FastAPI application..."
    
    # Set Python path
    export PYTHONPATH="/app:$PYTHONPATH"
    
    # Start uvicorn with optimized settings
    exec /app/.venv/bin/python -m uvicorn main:app \
        --host 0.0.0.0 \
        --port 8002 \
        --reload \
        --reload-delay 2 \
        --timeout-keep-alive 5 \
        --access-log \
        --log-level info
}

# Main execution flow
main() {
    echo "🏁 Starting main execution..."
    
    # Wait for Redis if configured
    if [[ -n "$REDIS_URL" ]]; then
        # Extract host and port from Redis URL
        redis_host=$(echo "$REDIS_URL" | sed -n 's/.*redis:\/\/\([^:]*\):.*/\1/p')
        redis_port=$(echo "$REDIS_URL" | sed -n 's/.*redis:\/\/[^:]*:\([0-9]*\).*/\1/p')
        
        if [[ -n "$redis_host" && -n "$redis_port" ]]; then
            wait_for_service "$redis_host" "$redis_port" "Redis" 60 || {
                echo "⚠️  Redis not available, continuing anyway..."
            }
        fi
    fi
    
    # Verify Python environment
    verify_python_env
    
    # Initialize database
    init_database
    
    # Start the application
    start_application
}

# Handle signals gracefully
trap 'echo "🛑 Received shutdown signal, stopping..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"