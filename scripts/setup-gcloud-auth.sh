#!/bin/bash

# Setup Google Cloud authentication for the podcast-digest-agent project
# Usage: ./scripts/setup-gcloud-auth.sh [PROJECT_ID]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ID=${1:-"podcast-digest-agent"}

echo -e "${GREEN}🔐 Setting up Google Cloud authentication for Podcast Digest Agent${NC}"
echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK${NC}"
    echo -e "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Login to gcloud (if not already logged in)
echo -e "\n${YELLOW}Checking gcloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}Not logged in. Starting authentication...${NC}"
    gcloud auth login
else
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    echo -e "${GREEN}✓ Already logged in as: ${ACTIVE_ACCOUNT}${NC}"
fi

# Set the project
echo -e "\n${YELLOW}Setting active project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Set Application Default Credentials
echo -e "\n${YELLOW}Setting up Application Default Credentials...${NC}"
echo -e "${YELLOW}This will open a browser for authentication${NC}"
gcloud auth application-default login --project=${PROJECT_ID}

# Set quota project for ADC
echo -e "\n${YELLOW}Setting quota project for ADC...${NC}"
gcloud auth application-default set-quota-project ${PROJECT_ID}

# Verify setup
echo -e "\n${GREEN}✅ Authentication setup complete!${NC}"
echo -e "\n${YELLOW}Current configuration:${NC}"
echo -e "Active account: $(gcloud auth list --filter=status:ACTIVE --format='value(account)')"
echo -e "Active project: $(gcloud config get-value project)"
echo -e "ADC quota project: $(gcloud config get-value core/quota_project 2>/dev/null || echo 'Not set')"

# Test API access
echo -e "\n${YELLOW}Testing API access...${NC}"
if gcloud services list --enabled --filter="name:aiplatform.googleapis.com" --format="value(name)" &> /dev/null; then
    echo -e "${GREEN}✓ Vertex AI API is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Vertex AI API not enabled. Run deploy script to enable required APIs.${NC}"
fi

echo -e "\n${GREEN}🎉 Authentication setup complete!${NC}"
echo -e "${YELLOW}You can now run: ./scripts/deploy-backend.sh${NC}"
