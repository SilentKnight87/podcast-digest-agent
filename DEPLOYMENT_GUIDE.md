# Deployment Guide - Podcast Digest Agent

This guide covers deploying the Podcast Digest Agent with the backend on Google Cloud Run and the frontend on Vercel.

## Prerequisites

- Google Cloud account with billing enabled
- Vercel account
- Local development environment with:
  - `gcloud` CLI installed and configured
  - `vercel` CLI installed (`npm i -g vercel`)
  - Node.js 18+ and Python 3.11+

## Quick Start

### 1. Backend Deployment (Google Cloud Run)

```bash
# Set your project ID
export PROJECT_ID="podcast-digest-agent"

# If using multiple Google accounts, switch to your personal account first
./scripts/switch-gcloud-account.sh your-personal@gmail.com

# First time setup: Configure authentication
./scripts/setup-gcloud-auth.sh $PROJECT_ID

# Deploy backend
./scripts/deploy-backend.sh $PROJECT_ID us-central1
```

The script will:
- Enable required Google Cloud APIs
- Build and deploy the container to Cloud Run
- Set up proper IAM permissions for Vertex AI
- Configure CORS for your frontend URL
- Output the backend service URL

### 2. Frontend Deployment (Vercel)

```bash
# Update frontend environment with the backend URL from step 1
cd podcast-digest-ui
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL to your Cloud Run backend URL

# Deploy to Vercel
cd ..
./scripts/deploy-frontend.sh
```

### 3. Update Backend CORS (After Frontend Deployment)

```bash
# Update the backend with your Vercel frontend URL
./scripts/update-backend-cors.sh https://your-app.vercel.app
```

### 4. Verify Deployment

```bash
# Test both services
./scripts/test-deployment.sh https://your-backend.run.app https://your-frontend.vercel.app
```

## Detailed Deployment Steps

### Backend (Google Cloud Run)

1. **Prepare Environment Variables**
   ```bash
   # Production settings
   GOOGLE_GENAI_USE_VERTEXAI=TRUE
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
   ```

2. **Deploy Using gcloud**
   ```bash
   gcloud run deploy podcast-digest-agent \
     --source . \
     --region us-central1 \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300 \
     --min-instances 1 \
     --max-instances 10 \
     --allow-unauthenticated
   ```

3. **Set IAM Permissions**
   ```bash
   # Get service account
   SERVICE_ACCOUNT=$(gcloud run services describe podcast-digest-agent \
     --region us-central1 \
     --format 'value(spec.template.spec.serviceAccountName)')

   # Grant Vertex AI access
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/aiplatform.user"
   ```

### Frontend (Vercel)

1. **Configure Environment Variables in Vercel Dashboard**
   - `NEXT_PUBLIC_API_URL`: Your Cloud Run backend URL
   - `NEXT_PUBLIC_WS_URL`: (Optional) WebSocket URL, defaults to API URL
   - `NEXT_PUBLIC_ENABLE_ANALYTICS`: Set to "true" in production
   - `NEXT_PUBLIC_ENABLE_DEBUG_LOGS`: Set to "false" in production

2. **Deploy via Vercel CLI**
   ```bash
   cd podcast-digest-ui
   vercel --prod
   ```

3. **Or Deploy via GitHub Integration**
   - Connect your GitHub repo to Vercel
   - Set environment variables in project settings
   - Deploy automatically on push to main branch

## Environment Variables Reference

### Backend (.env)
```bash
# Google AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# CORS Settings
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
FRONTEND_URL=https://your-app.vercel.app

# Application Settings
LOG_LEVEL=INFO
DEBUG=false
```

### Frontend (.env.local)
```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend.run.app

# Optional WebSocket URL (defaults to API URL)
# NEXT_PUBLIC_WS_URL=wss://your-backend.run.app

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_DEBUG_LOGS=false
```

## Architecture Notes

### WebSocket Connections
- WebSockets connect directly from browser to Cloud Run backend
- Cloud Run fully supports WebSocket connections
- Set appropriate timeouts (up to 60 minutes) for long-running connections

### CORS Configuration
- Backend dynamically reads allowed origins from environment
- Update `CORS_ALLOWED_ORIGINS` when frontend URL changes
- Multiple origins supported (comma-separated)

### File Storage
- Currently uses local filesystem (suitable for single-instance)
- For multi-instance scaling, implement Google Cloud Storage
- Audio files are temporary and can be cleaned up periodically

## Monitoring & Troubleshooting

### View Cloud Run Logs
```bash
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=podcast-digest-agent" \
  --format="value(text)"
```

### Common Issues

1. **Multiple Google Accounts / Wrong ADC**
   ```bash
   # List all authenticated accounts
   gcloud auth list

   # Switch to your personal account
   ./scripts/switch-gcloud-account.sh your-email@gmail.com

   # Or manually switch
   gcloud config set account your-email@gmail.com

   # Clear and reset ADC
   rm -f ~/.config/gcloud/application_default_credentials.json
   gcloud auth application-default login
   ```

2. **CORS Errors**
   - Update `CORS_ALLOWED_ORIGINS` in Cloud Run environment
   - Ensure frontend URL includes protocol (https://)

2. **WebSocket Connection Failures**
   - Check Cloud Run logs for connection attempts
   - Verify WebSocket URL format in frontend
   - Ensure Cloud Run timeout is sufficient

3. **Vertex AI Permission Errors**
   - Verify service account has `aiplatform.user` role
   - Check project has Vertex AI API enabled

4. **Memory/Timeout Errors**
   - Increase Cloud Run memory allocation (up to 32Gi)
   - Increase timeout (up to 3600 seconds)
   - Monitor instance metrics in Cloud Console

## Cost Optimization

- Use minimum instances = 1 to reduce cold starts
- Set maximum instances based on expected load
- Enable CPU allocation only during requests
- Monitor usage and adjust resources accordingly

## Security Considerations

1. **API Authentication** (if needed)
   ```bash
   # Remove public access
   gcloud run services update podcast-digest-agent \
     --no-allow-unauthenticated
   ```

2. **Use Secret Manager** for sensitive data
   ```bash
   # Store secrets
   echo -n "secret-value" | gcloud secrets create my-secret --data-file=-

   # Grant access and use in Cloud Run
   gcloud run services update podcast-digest-agent \
     --set-secrets "MY_SECRET=my-secret:latest"
   ```

## Continuous Deployment

### GitHub Actions for Backend
```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend
on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'requirements.txt'
      - 'Dockerfile'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      - run: |
          gcloud run deploy podcast-digest-agent \
            --source . \
            --region us-central1
```

### Vercel Auto-Deploy
- Connect GitHub repository to Vercel
- Set up environment variables in Vercel dashboard
- Frontend deploys automatically on push

## Next Steps

1. Set up monitoring dashboards in Google Cloud Console
2. Configure alerts for errors and high latency
3. Implement caching for frequently accessed data
4. Add authentication if needed
5. Set up custom domain names for both services
