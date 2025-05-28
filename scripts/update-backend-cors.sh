#!/bin/bash

# Update CORS settings on deployed Cloud Run backend
# Usage: ./scripts/update-backend-cors.sh [FRONTEND_URL] [PROJECT_ID] [REGION]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
FRONTEND_URL=${1:-""}
PROJECT_ID=${2:-"podcast-digest-agent"}
REGION=${3:-"us-central1"}
SERVICE_NAME="podcast-digest-agent"

echo -e "${GREEN}🔄 Updating CORS settings for Podcast Digest Agent Backend${NC}"
echo -e "${YELLOW}Project: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}Service: ${SERVICE_NAME}${NC}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get frontend URL if not provided
if [ -z "$FRONTEND_URL" ]; then
    echo -e "\n${YELLOW}Enter your Vercel frontend URL (e.g., https://your-app.vercel.app):${NC}"
    read FRONTEND_URL
fi

# Validate URL
if [ -z "$FRONTEND_URL" ]; then
    echo -e "${RED}❌ Frontend URL is required${NC}"
    exit 1
fi

# Set CORS origins (include localhost for development)
# Use semicolon as separator to avoid gcloud parsing issues
CORS_ORIGINS="${FRONTEND_URL};http://localhost:3000;http://localhost:3001"

echo -e "\n${YELLOW}Updating CORS settings...${NC}"
echo -e "${YELLOW}New CORS origins: ${CORS_ORIGINS}${NC}"

# Update environment variables
gcloud run services update ${SERVICE_NAME} \
  --region ${REGION} \
  --update-env-vars "CORS_ALLOWED_ORIGINS=${CORS_ORIGINS}" \
  --update-env-vars "FRONTEND_URL=${FRONTEND_URL}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format 'value(status.url)')

echo -e "\n${GREEN}✅ CORS settings updated successfully!${NC}"
echo -e "${YELLOW}Backend URL: ${SERVICE_URL}${NC}"
echo -e "${YELLOW}Frontend can now access the backend from: ${FRONTEND_URL}${NC}"

# Test CORS
echo -e "\n${YELLOW}Testing CORS headers...${NC}"
curl -s -I -X OPTIONS ${SERVICE_URL}/api/v1/config \
  -H "Origin: ${FRONTEND_URL}" \
  -H "Access-Control-Request-Method: GET" | grep -i "access-control" || echo "${YELLOW}CORS headers may take a moment to propagate${NC}"

echo -e "\n${GREEN}🎉 Update complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Update your frontend .env.local with:"
echo -e "   NEXT_PUBLIC_API_URL=${SERVICE_URL}"
echo -e "2. Deploy or redeploy your frontend"
