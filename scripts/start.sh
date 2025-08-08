#!/bin/bash

# TechGiterview Project Startup Script
# Author: Claude AI
# Description: Start the entire TechGiterview application stack

set -e

echo "🚀 TechGiterview Startup Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default mode
MODE=${1:-dev}

if [ "$MODE" != "dev" ] && [ "$MODE" != "prod" ]; then
    echo -e "${RED}Error: Invalid mode. Use 'dev' or 'prod'${NC}"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

echo -e "${BLUE}Starting in ${MODE} mode...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if required files exist
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found. Please run this script from the project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}Checking environment files...${NC}"

# Create .env files if they don't exist
if [ ! -f "src/backend/.env.dev" ]; then
    echo -e "${YELLOW}Creating default .env.dev file...${NC}"
    cat > src/backend/.env.dev << EOF
# Development Environment Variables
ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql://techgiterview_user:dev_password@localhost:5432/techgiterview_dev
REDIS_URL=redis://localhost:6379

# Vector Database
CHROMA_HOST=localhost
CHROMA_PORT=8001

# GitHub Integration
GITHUB_TOKEN=your_github_token_here

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# LangSmith (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=techgiterview-dev

# Security
SECRET_KEY=dev_secret_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
fi

if [ ! -f "src/frontend/.env.local" ]; then
    echo -e "${YELLOW}Creating default frontend .env.local file...${NC}"
    cat > src/frontend/.env.local << EOF
# Frontend Environment Variables
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENV=development
VITE_ENABLE_DEVTOOLS=true
EOF
fi

echo -e "${GREEN}✅ Environment files ready${NC}"

# Function to wait for service to be ready
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}Waiting for $service to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$port/health > /dev/null 2>&1 || \
           nc -z localhost $port > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service failed to start within expected time${NC}"
    return 1
}

if [ "$MODE" = "dev" ]; then
    echo -e "${BLUE}🔧 Starting development environment...${NC}"
    
    # Stop any existing containers
    docker-compose down
    
    # Start services
    echo -e "${YELLOW}Starting database services...${NC}"
    docker-compose up -d postgres redis chroma
    
    # Wait for databases to be ready
    echo -e "${YELLOW}Waiting for databases to be ready...${NC}"
    sleep 10
    
    # Start backend
    echo -e "${YELLOW}Starting backend service...${NC}"
    docker-compose up -d backend
    
    # Wait for backend to be ready
    wait_for_service "backend" "8000"
    
    # Start frontend
    echo -e "${YELLOW}Starting frontend service...${NC}"
    docker-compose up -d frontend
    
    # Final status check
    echo -e "${BLUE}Checking service status...${NC}"
    docker-compose ps
    
    echo -e "${GREEN}🎉 Development environment is ready!${NC}"
    echo ""
    echo -e "${BLUE}Services available at:${NC}"
    echo -e "  Frontend: ${YELLOW}http://localhost:3000${NC}"
    echo -e "  Backend API: ${YELLOW}http://localhost:8000${NC}"
    echo -e "  API Docs: ${YELLOW}http://localhost:8000/docs${NC}"
    echo -e "  PostgreSQL: ${YELLOW}localhost:5432${NC}"
    echo -e "  Redis: ${YELLOW}localhost:6379${NC}"
    echo -e "  ChromaDB: ${YELLOW}http://localhost:8001${NC}"
    echo ""
    echo -e "${YELLOW}To view logs: docker-compose logs -f${NC}"
    echo -e "${YELLOW}To stop: docker-compose down${NC}"

elif [ "$MODE" = "prod" ]; then
    echo -e "${BLUE}🚀 Starting production environment...${NC}"
    
    # Check if production environment file exists
    if [ ! -f "src/backend/.env.prod" ]; then
        echo -e "${RED}Error: .env.prod file not found. Please create production environment file.${NC}"
        exit 1
    fi
    
    # Use production docker-compose file
    if [ ! -f "docker-compose.prod.yml" ]; then
        echo -e "${YELLOW}Creating production docker-compose file...${NC}"
        cp docker-compose.yml docker-compose.prod.yml
        # Modify for production (remove volumes, use production Dockerfile, etc.)
        sed -i 's/dockerfile: Dockerfile/dockerfile: Dockerfile.prod/g' docker-compose.prod.yml
        sed -i 's/command: npm run dev/command: nginx -g "daemon off;"/g' docker-compose.prod.yml
    fi
    
    # Build and start production services
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    
    echo -e "${GREEN}🎉 Production environment is ready!${NC}"
    echo ""
    echo -e "${BLUE}Services available at:${NC}"
    echo -e "  Application: ${YELLOW}http://localhost:3000${NC}"
    echo -e "  API: ${YELLOW}http://localhost:8000${NC}"
fi

echo ""
echo -e "${GREEN}🎯 Next steps:${NC}"
echo -e "  1. Update environment variables with your API keys"
echo -e "  2. Visit the application and test GitHub repository analysis"
echo -e "  3. Check logs if you encounter any issues"