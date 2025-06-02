#!/bin/bash

echo "🧪 Testing Podcast Digest Agent Deployment"
echo "========================================="

# Test health endpoint
echo -e "\n1️⃣ Testing health endpoint..."
curl -s https://podcast-digest-agent-989387598091.us-central1.run.app/health | jq '.'

# Create a test task
echo -e "\n2️⃣ Creating test processing task..."
TASK_ID=$(curl -s -X POST "https://podcast-digest-agent-989387598091.us-central1.run.app/api/v1/process_youtube_url" \
  -H "Content-Type: application/json" \
  -H "Origin: https://podcast-digest-agent.vercel.app" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# Wait a bit
echo -e "\n⏳ Waiting 30 seconds for processing..."
sleep 30

# Check status
echo -e "\n3️⃣ Checking task status..."
curl -s "https://podcast-digest-agent-989387598091.us-central1.run.app/api/v1/status/$TASK_ID" \
  -H "Origin: https://podcast-digest-agent.vercel.app" | jq '{
    status: .processing_status.status,
    progress: .processing_status.overall_progress,
    current_agent: .processing_status.current_agent_id,
    error: .error_message,
    audio_url: .audio_file_url
  }'

echo -e "\n✅ Test complete!"