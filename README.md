# 🎙️ Podcast Digest Agent

Transform any YouTube video into an AI-powered conversational audio summary using Google's latest AI technologies.

🔗 **[Live Demo](https://podcast-digest-agent.vercel.app)**

## 🎯 Overview

Podcast Digest Agent is a full-stack application that leverages Google's Agent Development Kit (ADK) to create engaging audio summaries from YouTube videos. The system uses a pipeline of specialized AI agents to fetch transcripts, generate summaries, and produce natural conversational audio with dual voices.

## 🏗️ Architecture

```mermaid
graph TB
    A[Frontend - Next.js] -->|WebSocket + REST API| B[Backend - FastAPI]
    B --> C[Google ADK Pipeline]
    C --> D[Transcript Agent]
    D -->|YouTube Transcript| E[Dialogue Agent]
    E -->|Conversational Script| F[Audio Agent]
    F -->|Google Cloud TTS| G[Audio Output]
    B -.->|Real-time Updates| A
    
    style A fill:#3b82f6,color:#fff
    style B fill:#10b981,color:#fff
    style C fill:#f59e0b,color:#fff
```

## 🚀 Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **Google ADK v1.0.0** - Official Google Agent Development Kit
- **Gemini 2.0 Flash** - Google's low cost/fast inference
- **Google Cloud TTS** - Text-to-speech with Chirp HD voices
- **Pydantic v2** - Data validation and serialization

### Frontend  
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **shadcn/ui** - Modern UI components
- **TanStack Query** - Data fetching and caching
- **Motion.dev** - Smooth animations

### Infrastructure
- **Google Cloud Run** - Serverless managed container
- **Vercel** - Frontend deployment hosting
- **Webshare Proxy** - Allow access to Youtube from GCP

## ✨ Key Features

- **Real-time Processing Visualization** - Watch AI agents work in real-time via WebSocket
- **Dual-Voice Conversations** - Natural dialogue between two AI hosts
- **Smart Rate Limiting** - User-friendly rate limiting with countdown timers and clear feedback
- **Production Proxy System** - Reliable YouTube access with automatic rotation
- **Type-Safe Architecture** - Full TypeScript + Pydantic validation
- **Async Processing** - Concurrent audio generation for performance

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Cloud account with APIs enabled
- Webshare proxy credentials (optional)

### Backend Setup
```bash
# Clone repository
git clone https://github.com/yourusername/podcast-digest-agent.git
cd podcast-digest-agent

# Navigate to server directory
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run backend
python src/main.py
```

### Frontend Setup
```bash
# From project root
cd client
npm install
npm run dev
```

## 🔧 Configuration

Create a `.env` file with:
```env
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
WEBSHARE_API_KEY=your-proxy-key  # Optional
```

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)


## 🧪 Testing

```bash
# Backend tests
pytest tests/ --cov=src

# Frontend tests  
cd client
npm run test

# Test rate limiting
curl -X POST http://localhost:8000/api/v1/test_rate_limit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=test"}'
```

## 🛡️ Rate Limiting

The application includes intelligent rate limiting to ensure fair usage:

- **Main Processing**: 10 requests per hour per IP address
- **Test Endpoint**: 3 requests per minute (for development testing)
- **User Experience**: Live countdown timers and clear feedback when limits are reached
- **Auto-Reset**: Limits reset automatically using sliding window algorithm

When rate limited, users see:
- Clear error messages explaining the limit
- Countdown timer showing when they can try again
- Exact reset time for transparency

## 🤝 Contributing

Contributions are welcome!
