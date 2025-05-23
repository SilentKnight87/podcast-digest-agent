# Docker Containerization Specification

## Status: 📝 NOT STARTED

**Priority**: Medium
**Estimated Time**: 1 day
**Dependencies**: Code cleanup, testing suite

### Prerequisites
- ⬜ Docker and Docker Compose installed
- ⬜ Environment variables documented
- ⬜ Secrets management strategy defined
- ⬜ Container registry selected

---

## Overview

This specification outlines the approach for containerizing the Podcast Digest Agent application using Docker. Containerization will provide consistency across development, testing, and production environments, simplify deployment, and enable easier scaling in the future.

## Goals

1. Create a containerized environment for both backend and frontend
2. Enable simple local development with Docker Compose
3. Ensure proper environment separation (development, testing, production)
4. Optimize container sizes and performance
5. Implement security best practices
6. Prepare for future CI/CD pipeline integration

## Implementation Details

### 1. Backend Containerization

#### Dockerfile for Python Backend

```dockerfile
# podcast-digest-agent/Dockerfile
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    PODCAST_AGENT_TEST_MODE=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry export -f requirements.txt > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
COPY dev-requirements.txt ./
RUN pip install --no-cache-dir -r dev-requirements.txt

# Copy the rest of the application code
COPY . .

# Expose API port
EXPOSE 8000

# Command to run the application with hot reloading
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy the rest of the application code
COPY . .

# Create non-root user for security
RUN addgroup --system app && \
    adduser --system --ingroup app app && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Create and set proper permissions for required directories
RUN mkdir -p /app/output_audio /app/input && \
    chmod 755 /app/output_audio /app/input

# Expose API port
EXPOSE 8000

# Command to run the application in production mode
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2. Frontend Containerization

#### Dockerfile for Next.js Frontend

```dockerfile
# podcast-digest-ui/Dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files
COPY podcast-digest-ui/package.json podcast-digest-ui/package-lock.json* ./

# Install dependencies
RUN npm ci

# Development image
FROM base AS development
WORKDIR /app

# Copy node_modules from deps
COPY --from=deps /app/node_modules ./node_modules
COPY podcast-digest-ui ./

# Set development environment
ENV NODE_ENV=development

# Expose port
EXPOSE 3000

# Start Next.js in development mode
CMD ["npm", "run", "dev"]

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app

# Copy node_modules from deps
COPY --from=deps /app/node_modules ./node_modules
COPY podcast-digest-ui ./

# Set production environment
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS production
WORKDIR /app

# Set production environment
ENV NODE_ENV=production

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
```

### 3. Docker Compose Configuration

#### docker-compose.yml for Local Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    volumes:
      - .:/app
      - /app/node_modules
      - backend_output:/app/output_audio
      - backend_input:/app/input
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
      - OUTPUT_AUDIO_DIR=/app/output_audio
      - INPUT_DIR=/app/input
    depends_on:
      - redis

  frontend:
    build:
      context: .
      dockerfile: podcast-digest-ui/Dockerfile
      target: development
    volumes:
      - ./podcast-digest-ui:/app
      - /app/node_modules
      - /app/.next
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  backend_output:
  backend_input:
  redis_data:
```

#### docker-compose.prod.yml for Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    volumes:
      - backend_output:/app/output_audio
      - backend_input:/app/input
      - credentials:/app/credentials:ro
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
      - OUTPUT_AUDIO_DIR=/app/output_audio
      - INPUT_DIR=/app/input
    restart: unless-stopped
    depends_on:
      - redis

  frontend:
    build:
      context: .
      dockerfile: podcast-digest-ui/Dockerfile
      target: production
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    restart: unless-stopped
    depends_on:
      - backend

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
      - ./nginx/logs:/var/log/nginx
    restart: unless-stopped
    depends_on:
      - backend
      - frontend

volumes:
  backend_output:
  backend_input:
  redis_data:
  credentials:
```

### 4. Nginx Configuration for Production

```nginx
# nginx/conf.d/default.conf
server {
    listen 80;
    server_name podcast-digest.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name podcast-digest.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend static files
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /api/v1/ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Audio files
    location /api/v1/audio {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Docker Ignore Files

#### .dockerignore for Backend

```
# .dockerignore
.git
.gitignore
.venv
venv
env
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.pytest_cache
.coverage
htmlcov
.tox
.env
.env.*
output_audio/*
!output_audio/.gitkeep
node_modules
podcast-digest-ui
```

#### .dockerignore for Frontend

```
# podcast-digest-ui/.dockerignore
.git
.gitignore
node_modules
.next
out
.DS_Store
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.env.local
.env.development.local
.env.test.local
.env.production.local
```

## Environment Configuration

### 1. Environment Variables Management

Create env templates for development and production:

```
# .env.template
DEBUG=False
API_V1_STR=/api/v1
OUTPUT_AUDIO_DIR=/app/output_audio
INPUT_DIR=/app/input
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
DEFAULT_SUMMARY_LENGTH=medium
DEFAULT_AUDIO_STYLE=conversational
DEFAULT_TTS_VOICE=en-US-Neural2-J
```

### 2. Secrets Management

Store secure credentials:

1. Create a Docker volume for credentials
2. Use environment variables for non-sensitive configuration
3. For production, consider integrating with a secrets management service

## Deployment Workflow

1. **Local Development**:
   - `docker-compose up`
   - Changes to code are reflected immediately with hot reloading

2. **Testing**:
   - `docker-compose -f docker-compose.yml -f docker-compose.test.yml up`
   - Runs tests in isolated environment

3. **Production Deployment**:
   - Build production images: `docker-compose -f docker-compose.prod.yml build`
   - Push to container registry: `docker-compose -f docker-compose.prod.yml push`
   - Deploy: `docker-compose -f docker-compose.prod.yml up -d`

## Security Considerations

1. **Non-root Users**:
   - Run containers as non-root users
   - Set proper file permissions

2. **Dependency Scanning**:
   - Implement container scanning in CI/CD
   - Regularly update base images

3. **Environment Segregation**:
   - Keep development and production environments separate
   - Limit exposure of sensitive information

4. **Network Security**:
   - Restrict container network access
   - Use internal Docker networks for inter-service communication

## Performance Optimization

1. **Multi-stage Builds**:
   - Keep final images small by using multi-stage builds
   - Include only necessary files and dependencies

2. **Resource Allocation**:
   - Set appropriate CPU and memory limits
   - Monitor resource usage and adjust as needed

3. **Caching Strategies**:
   - Leverage Docker build cache effectively
   - Use volume mounts for development

## Implementation Plan

1. **Phase 1: Basic Container Setup**
   - Create Dockerfiles for backend and frontend
   - Implement docker-compose for local development
   - Test basic functionality

2. **Phase 2: Environment Configuration**
   - Set up environment variables
   - Configure volumes for persistent data
   - Test different environment configurations

3. **Phase 3: Production Readiness**
   - Create production docker-compose
   - Set up Nginx for routing
   - Implement security measures

4. **Phase 4: Documentation and Testing**
   - Document deployment process
   - Test deployment in staging environment
   - Create monitoring and logging strategy

## Considerations and Constraints

1. **GPU Support**:
   - If ML models require GPU acceleration, additional configuration may be needed

2. **Storage Requirements**:
   - Audio files may require significant storage
   - Consider volume management strategies

3. **Scaling Considerations**:
   - For future scaling, consider Kubernetes or Docker Swarm
   - Plan for horizontal scaling of services