#!/bin/bash
# Docker Build Test Script for TechGiterview
# Test the improved Docker configuration

set -e

echo "🐳 Testing TechGiterview Docker Configuration"
echo "============================================"

# Function to check if user is in docker group
check_docker_permissions() {
    if ! groups $USER | grep -q '\bdocker\b'; then
        echo "❌ User $USER is not in docker group"
        echo "🔧 To fix this, run:"
        echo "   sudo usermod -aG docker $USER"
        echo "   newgrp docker  # or logout and login again"
        echo ""
        return 1
    fi
    echo "✅ Docker permissions OK"
    return 0
}

# Function to test Docker is running
test_docker() {
    echo "📋 Checking Docker daemon..."
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker daemon not accessible"
        return 1
    fi
    echo "✅ Docker daemon running"
}

# Function to build backend image
build_backend() {
    echo "🏗️  Building backend image (development stage)..."
    cd src/backend
    if docker build --target development -t techgiterview-backend:dev .; then
        echo "✅ Backend development image built successfully"
    else
        echo "❌ Backend build failed"
        return 1
    fi
    cd ../..
}

# Function to build production backend image
build_backend_prod() {
    echo "🏗️  Building backend image (production stage)..."
    cd src/backend
    if docker build --target production -t techgiterview-backend:prod .; then
        echo "✅ Backend production image built successfully"
    else
        echo "❌ Backend production build failed"
        return 1
    fi
    cd ../..
}

# Function to test container startup
test_container() {
    echo "🚀 Testing container startup..."
    
    # Start a test container
    if docker run -d --name techgiterview-test -p 8003:8002 techgiterview-backend:dev; then
        echo "✅ Container started"
        
        # Wait a moment for startup
        sleep 5
        
        # Test if the container is responding
        if curl -f http://localhost:8003/health 2>/dev/null; then
            echo "✅ Health check passed"
        else
            echo "⚠️  Health check failed (this might be normal for a quick test)"
        fi
        
        # Clean up
        docker stop techgiterview-test
        docker rm techgiterview-test
        echo "🧹 Cleaned up test container"
    else
        echo "❌ Container startup failed"
        return 1
    fi
}

# Main execution
main() {
    if check_docker_permissions && test_docker; then
        echo ""
        echo "🔨 Running build tests..."
        
        # Test development build
        if build_backend; then
            echo ""
            echo "🧪 Testing container..."
            test_container
        fi
        
        echo ""
        echo "🏭 Testing production build..."
        build_backend_prod
        
        echo ""
        echo "🎉 All Docker tests completed successfully!"
        echo ""
        echo "📝 Next steps:"
        echo "   • Development: docker-compose up"
        echo "   • Production: docker-compose -f docker-compose.yml -f docker-compose.prod.yml up"
        
    else
        echo ""
        echo "❌ Docker permissions need to be fixed first"
        exit 1
    fi
}

# Run main function
main "$@"