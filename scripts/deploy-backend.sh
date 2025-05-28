#!/bin/bash

# Deploy Backend to Google Cloud Run
# Usage: ./scripts/deploy-backend.sh [PROJECT_ID] [REGION]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
SERVICE_NAME="podcast-digest-agent"

echo -e "${GREEN}🚀 Deploying Podcast Digest Agent Backend to Cloud Run${NC}"
echo -e "${YELLOW}Project: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}Service: ${SERVICE_NAME}${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK${NC}"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with gcloud. Please run: gcloud auth login${NC}"
    exit 1
fi

# Set project
echo -e "\n${YELLOW}Setting project...${NC}"
gcloud config set project ${PROJECT_ID}

# Check ADC quota project
CURRENT_QUOTA_PROJECT=$(gcloud config get-value core/quota_project 2>/dev/null || echo "")
ADC_PROJECT=$(gcloud auth application-default print-access-token 2>&1 | grep -o 'project_id":"[^"]*' | cut -d'"' -f3 || echo "")

if [[ "$ADC_PROJECT" != "$PROJECT_ID" ]] || [[ "$CURRENT_QUOTA_PROJECT" != "$PROJECT_ID" ]]; then
    echo -e "\n${YELLOW}⚠️  Application Default Credentials are set for a different project${NC}"
    echo -e "${YELLOW}Current ADC project: ${ADC_PROJECT:-none}${NC}"
    echo -e "${YELLOW}Target project: ${PROJECT_ID}${NC}"
    echo -e "\n${YELLOW}Would you like to update ADC for this project? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${YELLOW}Setting up Application Default Credentials for project ${PROJECT_ID}...${NC}"
        gcloud auth application-default login --project=${PROJECT_ID}
        gcloud auth application-default set-quota-project ${PROJECT_ID}
    else
        echo -e "${YELLOW}Proceeding with current credentials. This may cause issues.${NC}"
    fi
else
    echo -e "\n${GREEN}✓ Application Default Credentials are correctly set for ${PROJECT_ID}${NC}"
fi

# Enable required APIs
echo -e "\n${YELLOW}Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com

# Get frontend URL for CORS configuration
echo -e "\n${YELLOW}Enter your Vercel frontend URL (e.g., https://your-app.vercel.app):${NC}"
echo -e "${YELLOW}If you haven't deployed the frontend yet, press Enter to use default CORS settings${NC}"
read FRONTEND_URL

# Set default CORS if no frontend URL provided
if [ -z "$FRONTEND_URL" ]; then
    FRONTEND_URL="http://localhost:3000"
    # Use semicolon as separator to avoid gcloud parsing issues
    CORS_ORIGINS="http://localhost:3000;http://localhost:3001"
    echo -e "${YELLOW}Using default CORS settings for local development${NC}"
    echo -e "${YELLOW}You can update this later after deploying the frontend${NC}"
else
    # Use semicolon as separator
    CORS_ORIGINS="${FRONTEND_URL};http://localhost:3000"
fi

# Deploy to Cloud Run
echo -e "\n${GREEN}📦 Building and deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1 \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars "GOOGLE_CLOUD_LOCATION=${REGION}" \
  --set-env-vars "LOG_LEVEL=INFO" \
  --set-env-vars "CORS_ALLOWED_ORIGINS=${CORS_ORIGINS}" \
  --set-env-vars "FRONTEND_URL=${FRONTEND_URL}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format 'value(status.url)')

# Get service account
SERVICE_ACCOUNT=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format 'value(spec.template.spec.serviceAccountName)')

# Grant Vertex AI permissions
echo -e "\n${YELLOW}Granting Vertex AI permissions...${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

# Test deployment
echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo -e "${YELLOW}Service URL: ${SERVICE_URL}${NC}"
echo -e "\n${YELLOW}Testing health endpoint...${NC}"
curl -s ${SERVICE_URL}/health | jq .

echo -e "\n${GREEN}🎉 Backend deployed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Update your frontend .env.local with:"
echo -e "   NEXT_PUBLIC_API_URL=${SERVICE_URL}"
echo -e "2. Deploy frontend to Vercel"
echo -e "3. Update CORS_ALLOWED_ORIGINS in Cloud Run if needed"
