#!/bin/bash

# Deploy Frontend to Vercel
# Usage: ./scripts/deploy-frontend.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Podcast Digest UI to Vercel${NC}"

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI not found. Installing...${NC}"
    npm i -g vercel
fi

# Change to frontend directory
cd client

# Check for .env.local
if [ ! -f .env.local ]; then
    echo -e "${YELLOW}⚠️  .env.local not found. Creating from example...${NC}"
    cp .env.local.example .env.local
    echo -e "${RED}Please update .env.local with your Cloud Run backend URL${NC}"
    echo -e "${YELLOW}Example: NEXT_PUBLIC_API_URL=https://podcast-digest-agent-xxxxx-uc.a.run.app${NC}"
    exit 1
fi

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
npm install

# Build project locally to catch errors
echo -e "\n${YELLOW}Building project...${NC}"
npm run build

# Deploy to Vercel
echo -e "\n${GREEN}📦 Deploying to Vercel...${NC}"
echo -e "${YELLOW}Note: You'll need to configure environment variables in Vercel dashboard:${NC}"
echo -e "- NEXT_PUBLIC_API_URL (your Cloud Run backend URL)"
echo -e "- NEXT_PUBLIC_WS_URL (optional, will be derived from API_URL)"

# Deploy with Vercel CLI
vercel --prod

echo -e "\n${GREEN}🎉 Frontend deployment initiated!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Set environment variables in Vercel dashboard"
echo -e "2. Update Cloud Run CORS settings with your Vercel URL"
echo -e "3. Test the full application flow"
