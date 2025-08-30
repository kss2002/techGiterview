#!/bin/bash

# Docker build test script for TechGiterview backend
# Tests the ChromaDB timeout fixes

set -e

echo "🔧 Testing Docker build with ChromaDB timeout fixes..."
echo "📂 Building from: $(pwd)"

# Add user to docker group if not already (requires re-login)
if ! groups $USER | grep -q docker; then
    echo "⚠️  User not in docker group. Run: sudo usermod -aG docker $USER && newgrp docker"
    echo "   Then logout/login or run: newgrp docker"
fi

# Build the backend container
echo "🏗️  Building backend container..."
if docker build -t techgiterview-backend -f src/backend/Dockerfile src/backend; then
    echo "✅ Backend build successful!"
    
    # Test container startup
    echo "🧪 Testing container startup..."
    if docker run --rm -d --name test-backend -p 8002:8002 techgiterview-backend; then
        sleep 5
        if curl -f http://localhost:8002/health; then
            echo "✅ Container health check passed!"
        else
            echo "⚠️  Container health check failed"
        fi
        docker stop test-backend || true
    else
        echo "⚠️  Container startup failed"
    fi
else
    echo "❌ Backend build failed"
    exit 1
fi

echo "🎉 Docker build test completed!"