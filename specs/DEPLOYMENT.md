# DEPLOYMENT.md

## Overview
This document provides step-by-step instructions for deploying the Podcast Digest Agent application to Google Cloud Run. The application is a FastAPI service with embedded ADK agents for processing podcasts.

## Prerequisites

### Local Setup
```bash
# Install Google Cloud SDK
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate with Google Cloud
gcloud auth login

# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com
```

## Project Structure

The deployment follows the ADK-recommended structure:

```
podcast-digest-agent/
├── src/
│   ├── agents/           # ADK agent implementations
│   ├── api/              # FastAPI endpoints
│   ├── config/           # Configuration
│   └── main.py           # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── .dockerignore        # Files to exclude from container
└── .env.example         # Environment variables template
```

## Environment Variables

Create a `.env` file for local development:

```bash
# Google AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Application Settings
LOG_LEVEL=INFO
API_VERSION=v1

# Optional: For local testing with AI Studio
# GOOGLE_GENAI_USE_VERTEXAI=FALSE
# GOOGLE_API_KEY=your-api-key
```

## Dockerfile

Create a production-ready Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (ffmpeg for audio processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Cloud Run sets the PORT environment variable
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

## Build and Deploy Steps

### 1. Build Container Locally (Optional)
```bash
# Test the container locally
docker build -t podcast-digest-agent .
docker run -p 8080:8080 --env-file .env podcast-digest-agent
```

### 2. Deploy Using Cloud Build and Run

The simplest approach is to let Cloud Run build and deploy in one step:

```bash
# Deploy directly from source
gcloud run deploy podcast-digest-agent \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1 \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,LOG_LEVEL=INFO"
```

### 3. Alternative: Build and Deploy Separately

If you prefer more control over the build process:

```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and push to Artifact Registry
IMAGE_URL=us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/podcast-digest-agent
docker build -t $IMAGE_URL .
docker push $IMAGE_URL

# Deploy from the container image
gcloud run deploy podcast-digest-agent \
  --image $IMAGE_URL \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1 \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,LOG_LEVEL=INFO"
```

## Service Configuration

### Resource Allocation
- **Memory**: 2Gi (required for audio processing)
- **CPU**: 2 vCPUs
- **Timeout**: 300 seconds (5 minutes for long podcast processing)
- **Concurrency**: Default (1000 requests per instance)
- **Min Instances**: 1 (to reduce cold starts)
- **Max Instances**: 10 (adjust based on expected load)

### IAM Permissions

The Cloud Run service account needs Vertex AI permissions:

```bash
# Get the service account email
SERVICE_ACCOUNT=$(gcloud run services describe podcast-digest-agent \
  --region us-central1 \
  --format 'value(spec.template.spec.serviceAccountName)')

# Grant Vertex AI user permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"
```

## Verify Deployment

### 1. Get Service URL
```bash
SERVICE_URL=$(gcloud run services describe podcast-digest-agent \
  --region us-central1 \
  --format 'value(status.url)')

echo "Service deployed at: $SERVICE_URL"
```

### 2. Test Health Endpoint
```bash
curl $SERVICE_URL/health
# Expected: {"status":"healthy"}
```

### 3. Test API Documentation
```bash
# Open in browser
echo "API Documentation: $SERVICE_URL/docs"
```

### 4. Test Processing Endpoint
```bash
# Submit a processing request
curl -X POST $SERVICE_URL/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://youtube.com/watch?v=example",
    "options": {
      "target_duration": 600,
      "summary_style": "conversational"
    }
  }'
```

## Monitoring

### View Logs
```bash
# Stream logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=podcast-digest-agent" --format="value(text)"

# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=podcast-digest-agent" --limit 50
```

### View Metrics
```bash
# Open Cloud Run console
echo "https://console.cloud.google.com/run/detail/us-central1/podcast-digest-agent/metrics?project=$PROJECT_ID"
```

## Update Deployment

To update the service after code changes:

```bash
# Option 1: Deploy from source (recommended)
gcloud run deploy podcast-digest-agent --source . --region us-central1

# Option 2: Update specific environment variables
gcloud run services update podcast-digest-agent \
  --update-env-vars LOG_LEVEL=DEBUG \
  --region us-central1

# Option 3: Update resource limits
gcloud run services update podcast-digest-agent \
  --memory 4Gi \
  --cpu 4 \
  --region us-central1
```

## Rollback

If you need to rollback to a previous version:

```bash
# List all revisions
gcloud run revisions list --service podcast-digest-agent --region us-central1

# Route traffic to a specific revision
gcloud run services update-traffic podcast-digest-agent \
  --to-revisions REVISION_NAME=100 \
  --region us-central1
```

## Security Considerations

### 1. Enable Authentication (Optional)
```bash
# Remove --allow-unauthenticated flag to require authentication
gcloud run services update podcast-digest-agent \
  --no-allow-unauthenticated \
  --region us-central1
```

### 2. Use Secret Manager for Sensitive Data
```bash
# Create a secret
echo -n "your-api-key" | gcloud secrets create api-key --data-file=-

# Grant access to the service account
gcloud secrets add-iam-policy-binding api-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

# Update deployment to use the secret
gcloud run services update podcast-digest-agent \
  --set-secrets "GOOGLE_API_KEY=api-key:latest" \
  --region us-central1
```

## Cost Optimization

### 1. Set Maximum Instances
```bash
# Limit costs by capping maximum instances
gcloud run services update podcast-digest-agent \
  --max-instances 5 \
  --region us-central1
```

### 2. Use CPU Allocation Only During Requests
```bash
# Default behavior - CPU only allocated during request processing
gcloud run services update podcast-digest-agent \
  --no-cpu-throttling \
  --region us-central1
```

## Troubleshooting

### Common Issues

1. **Cold Start Delays**
   ```bash
   # Keep warm with minimum instances
   gcloud run services update podcast-digest-agent --min-instances 1
   ```

2. **Timeout Errors**
   ```bash
   # Increase timeout for long processing
   gcloud run services update podcast-digest-agent --timeout 900
   ```

3. **Memory Errors**
   ```bash
   # Increase memory allocation
   gcloud run services update podcast-digest-agent --memory 4Gi
   ```

4. **Permission Errors**
   ```bash
   # Ensure Vertex AI permissions
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/aiplatform.user"
   ```

## Clean Up

To avoid incurring charges, delete resources when no longer needed:

```bash
# Delete Cloud Run service
gcloud run services delete podcast-digest-agent --region us-central1

# Delete container images (if using Artifact Registry)
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/podcast-digest-agent
```

## Next Steps

1. Set up a custom domain: [Cloud Run domain mapping](https://cloud.google.com/run/docs/mapping-custom-domains)
2. Enable Cloud CDN for static assets: [Cloud CDN setup](https://cloud.google.com/cdn/docs/setting-up-cdn-with-cloud-run)
3. Configure monitoring alerts: [Cloud Monitoring](https://cloud.google.com/run/docs/monitoring)
4. Set up CI/CD pipeline: [Cloud Build triggers](https://cloud.google.com/build/docs/automating-builds/create-manage-triggers)
