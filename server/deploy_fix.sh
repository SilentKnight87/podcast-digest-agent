#!/bin/bash

echo "🚀 Deploying Podcast Digest Agent with Vertex AI configuration"

# Change to project root directory (where Dockerfile is)
cd /Users/peterbrown/Documents/Code/podcast-digest-agent

# Deploy using Dockerfile with proper environment variables
gcloud run deploy podcast-digest-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=podcast-digest-agent" \
  --set-env-vars "GOOGLE_CLOUD_LOCATION=us-central1" \
  --set-env-vars "OUTPUT_AUDIO_DIR=/tmp" \
  --set-env-vars "CORS_ALLOWED_ORIGINS=http://localhost:3000;http://localhost:3001;https://podcast-digest-agent.vercel.app" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10

echo "✅ Deployment initiated"