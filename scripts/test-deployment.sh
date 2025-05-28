#!/bin/bash

# Test Deployment
# Usage: ./scripts/test-deployment.sh [BACKEND_URL] [FRONTEND_URL]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_URL=${1:-"http://localhost:8000"}
FRONTEND_URL=${2:-"http://localhost:3000"}

echo -e "${GREEN}🔍 Testing Podcast Digest Deployment${NC}"
echo -e "${YELLOW}Backend: ${BACKEND_URL}${NC}"
echo -e "${YELLOW}Frontend: ${FRONTEND_URL}${NC}"

# Test backend health
echo -e "\n${YELLOW}Testing backend health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s ${BACKEND_URL}/health)
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
    echo $HEALTH_RESPONSE | jq .
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    exit 1
fi

# Test API docs
echo -e "\n${YELLOW}Testing API documentation...${NC}"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BACKEND_URL}/docs)
if [ $DOCS_STATUS -eq 200 ]; then
    echo -e "${GREEN}✅ API documentation accessible${NC}"
else
    echo -e "${RED}❌ API documentation not accessible (HTTP ${DOCS_STATUS})${NC}"
fi

# Test CORS headers
echo -e "\n${YELLOW}Testing CORS headers...${NC}"
CORS_HEADERS=$(curl -s -I -X OPTIONS ${BACKEND_URL}/api/v1/config \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Access-Control-Request-Method: GET")

if [[ $CORS_HEADERS == *"Access-Control-Allow-Origin"* ]]; then
    echo -e "${GREEN}✅ CORS headers present${NC}"
else
    echo -e "${RED}❌ CORS headers missing${NC}"
    echo -e "${YELLOW}You may need to update CORS_ALLOWED_ORIGINS in Cloud Run${NC}"
fi

# Test frontend
echo -e "\n${YELLOW}Testing frontend accessibility...${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${FRONTEND_URL})
if [ $FRONTEND_STATUS -eq 200 ]; then
    echo -e "${GREEN}✅ Frontend accessible${NC}"
else
    echo -e "${RED}❌ Frontend not accessible (HTTP ${FRONTEND_STATUS})${NC}"
fi

# Test sample processing (optional)
echo -e "\n${YELLOW}Would you like to test podcast processing? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}Enter a YouTube URL to test:${NC}"
    read YOUTUBE_URL

    echo -e "\n${YELLOW}Submitting processing request...${NC}"
    TASK_RESPONSE=$(curl -s -X POST ${BACKEND_URL}/api/v1/tasks \
        -H "Content-Type: application/json" \
        -d "{\"youtube_url\": \"${YOUTUBE_URL}\"}")

    TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')
    if [ "$TASK_ID" != "null" ]; then
        echo -e "${GREEN}✅ Task created: ${TASK_ID}${NC}"
        echo -e "${YELLOW}Check status at: ${BACKEND_URL}/api/v1/tasks/${TASK_ID}${NC}"
    else
        echo -e "${RED}❌ Failed to create task${NC}"
        echo $TASK_RESPONSE | jq .
    fi
fi

echo -e "\n${GREEN}🎉 Deployment testing complete!${NC}"
