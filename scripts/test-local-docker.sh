#!/bin/bash

# Test Docker build and run locally
# Usage: ./scripts/test-local-docker.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Testing Docker build locally${NC}"

# Build Docker image
echo -e "\n${YELLOW}Building Docker image...${NC}"
docker build -t podcast-digest-agent:test .

# Create temporary .env file for Docker
echo -e "\n${YELLOW}Creating test environment...${NC}"
cat > .env.docker.test << EOF
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=${GOOGLE_API_KEY:-"your-api-key"}
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
PORT=8080
EOF

# Run container
echo -e "\n${YELLOW}Starting container...${NC}"
docker run -d \
  --name podcast-digest-test \
  -p 8080:8080 \
  --env-file .env.docker.test \
  -v ${GOOGLE_APPLICATION_CREDENTIALS:-""}:/app/credentials.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  podcast-digest-agent:test

# Wait for container to start
echo -e "\n${YELLOW}Waiting for container to start...${NC}"
sleep 5

# Test health endpoint
echo -e "\n${YELLOW}Testing health endpoint...${NC}"
if curl -s http://localhost:8080/health | jq .; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    docker logs podcast-digest-test
fi

# Show logs
echo -e "\n${YELLOW}Container logs:${NC}"
docker logs podcast-digest-test | tail -20

# Cleanup
echo -e "\n${YELLOW}Cleaning up...${NC}"
docker stop podcast-digest-test
docker rm podcast-digest-test
rm -f .env.docker.test

echo -e "\n${GREEN}✅ Docker test complete!${NC}"
echo -e "${YELLOW}If successful, you can deploy with: ./scripts/deploy-backend.sh${NC}"
