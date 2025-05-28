#!/bin/bash

# Switch Google Cloud account for the podcast-digest-agent project
# Usage: ./scripts/switch-gcloud-account.sh [EMAIL]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

EMAIL=${1:-""}

echo -e "${GREEN}🔄 Switching Google Cloud Account${NC}"

# Show current accounts
echo -e "\n${YELLOW}Current Google Cloud accounts:${NC}"
gcloud auth list

# Get current active account
CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "none")
echo -e "\n${BLUE}Currently active account: ${CURRENT_ACCOUNT}${NC}"

# If email not provided, prompt for it
if [ -z "$EMAIL" ]; then
    echo -e "\n${YELLOW}Enter the email address for your personal Google account:${NC}"
    read -r EMAIL
fi

# Check if account exists
if gcloud auth list --filter="account:${EMAIL}" --format="value(account)" | grep -q "${EMAIL}"; then
    echo -e "\n${GREEN}✓ Account ${EMAIL} already authenticated${NC}"
    echo -e "${YELLOW}Switching to this account...${NC}"
else
    echo -e "\n${YELLOW}Account ${EMAIL} not found. Adding new account...${NC}"
    echo -e "${YELLOW}This will open a browser for authentication${NC}"
    gcloud auth login --account "${EMAIL}"
fi

# Activate the account
echo -e "\n${YELLOW}Activating account ${EMAIL}...${NC}"
gcloud config set account "${EMAIL}"

# Set up Application Default Credentials for this account
echo -e "\n${YELLOW}Setting up Application Default Credentials for ${EMAIL}...${NC}"
echo -e "${RED}IMPORTANT: Make sure to select your personal account (${EMAIL}) in the browser!${NC}"
echo -e "${YELLOW}Press Enter to continue...${NC}"
read -r

# Clear existing ADC first
echo -e "\n${YELLOW}Clearing existing Application Default Credentials...${NC}"
rm -f ~/.config/gcloud/application_default_credentials.json

# Set new ADC
gcloud auth application-default login --account "${EMAIL}"

# Verify the setup
echo -e "\n${GREEN}✅ Account switch complete!${NC}"
echo -e "\n${YELLOW}Current configuration:${NC}"
echo -e "Active account: $(gcloud auth list --filter=status:ACTIVE --format='value(account)')"

# Show ADC info
if [ -f ~/.config/gcloud/application_default_credentials.json ]; then
    echo -e "ADC file exists: ${GREEN}✓${NC}"
else
    echo -e "ADC file exists: ${RED}✗${NC}"
fi

echo -e "\n${GREEN}🎉 You can now proceed with deployment!${NC}"
echo -e "${YELLOW}Next step: ./scripts/setup-gcloud-auth.sh podcast-digest-agent${NC}"
