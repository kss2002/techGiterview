# Docker Troubleshooting Guide

## Backend Container Timeout Issues

### Quick Fix Commands

```bash
# 1. Increase Docker Compose timeout
export COMPOSE_HTTP_TIMEOUT=300
export DOCKER_CLIENT_TIMEOUT=300

# 2. Build with progress monitoring
docker-compose build --progress=plain backend

# 3. Start with logs
docker-compose up --remove-orphans --force-recreate

# 4. Debug startup issues
docker-compose logs -f backend
```

### Common Issues and Solutions

#### 1. Build Timeout (60 second timeout)
**Symptoms**: "Read timed out" during build
**Solution**: 
```bash
# Set longer timeout
export COMPOSE_HTTP_TIMEOUT=600
docker-compose up --build
```

#### 2. Dependency Installation Timeout
**Symptoms**: Build hangs during pip install
**Solution**:
```bash
# Build with verbose output
docker build --target development --progress=plain src/backend/

# Or build stages individually
docker build --target base -t techgiterview-base src/backend/
docker build --target dependencies -t techgiterview-deps src/backend/
docker build --target development -t techgiterview-dev src/backend/
```

#### 3. Health Check Failures
**Symptoms**: Container starts but health check fails
**Solution**:
```bash
# Check container logs
docker-compose logs backend

# Manual health check
docker exec -it techgiterview_backend_1 curl -f http://localhost:8002/health

# Disable health check temporarily
# Add to docker-compose.yml backend service:
# healthcheck:
#   disable: true
```

#### 4. Volume Mount Issues
**Symptoms**: "Virtual environment not found"
**Solution**:
```bash
# Remove volumes and rebuild
docker-compose down -v
docker-compose up --build

# Check volume contents
docker exec -it techgiterview_backend_1 ls -la /app/.venv/bin/
```

#### 5. Memory/Resource Issues
**Symptoms**: Build fails with no specific error
**Solution**:
```bash
# Check Docker resources
docker system df
docker system prune

# Increase Docker memory limit in Docker Desktop
# Or add to docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

### Performance Tips

1. **Use BuildKit for faster builds**:
   ```bash
   export DOCKER_BUILDKIT=1
   export COMPOSE_DOCKER_CLI_BUILD=1
   ```

2. **Parallel dependency installation**:
   The Dockerfile now installs dependencies in stages for better caching

3. **Minimize rebuild frequency**:
   Only essential source files are mounted as volumes

### Debugging Commands

```bash
# Check if containers are running
docker-compose ps

# View real-time logs
docker-compose logs -f backend

# Execute commands in container
docker-compose exec backend /bin/bash

# Check virtual environment
docker-compose exec backend /app/.venv/bin/python --version

# Test health endpoint
docker-compose exec backend curl -f http://localhost:8002/health

# Check startup script
docker-compose exec backend cat start.sh

# Monitor resource usage
docker stats
```

### Environment-Specific Commands

#### Development
```bash
# Standard development startup
docker-compose up

# Development with rebuild
docker-compose up --build

# Development with logs
docker-compose up --build --remove-orphans
```

#### Production
```bash
# Production startup
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Production logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### If All Else Fails

1. **Complete reset**:
   ```bash
   docker-compose down -v --remove-orphans
   docker system prune -a
   docker-compose up --build
   ```

2. **Manual verification**:
   ```bash
   # Test the build script
   ./scripts/docker-build-test.sh
   
   # Build without cache
   docker-compose build --no-cache backend
   ```

3. **Check system resources**:
   ```bash
   # Check available disk space
   df -h
   
   # Check available memory
   free -h
   
   # Check Docker daemon status
   sudo systemctl status docker
   ```

### Getting Help

If issues persist:
1. Run `./scripts/docker-build-test.sh` and share the output
2. Share the output of `docker-compose logs backend`
3. Check the container build logs with `docker-compose build --progress=plain backend`