# 🎙️ Podcast Digest Agent

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent podcast processing system that transforms YouTube podcast content into AI-generated conversational audio digests. Submit YouTube URLs, and receive a synthesized two-person dialogue summarizing the key points in minutes instead of hours.

## ✨ Features

- 🎯 **Automated Processing**: Submit YouTube URLs and get conversational audio digests
- 🤖 **AI-Powered Agents**: Specialized agents for transcription, summarization, synthesis, and audio generation
- 🎭 **Multi-Voice TTS**: Google Cloud Text-to-Speech with distinct conversational voices
- 📱 **Modern Web Interface**: Next.js frontend with real-time processing visualization
- ⚡ **Real-time Updates**: WebSocket-based live progress tracking
- 🎨 **Beautiful UI**: Dark/light mode with responsive design using shadcn/ui
- 📊 **Processing Visualization**: Interactive workflow diagrams showing agent pipeline

## 🏗️ Architecture

The system consists of three main components:

### Backend (Python/FastAPI)
- **Specialized Agents**: TranscriptFetcher, SummarizerAgent, SynthesizerAgent, AudioGenerator
- **Google ADK Integration**: Agent Development Kit for orchestration
- **WebSocket Support**: Real-time status updates
- **RESTful API**: Comprehensive endpoints for processing and management

### Frontend (Next.js)
- **Interactive UI**: React-based interface with TypeScript
- **Real-time Visualization**: Agent workflow and progress tracking
- **Audio Player**: Enhanced playback with waveform visualization
- **Responsive Design**: Mobile-first approach with Tailwind CSS

### External Services
- **Google Cloud TTS**: High-quality voice synthesis with Chirp HD models
- **Google Gemini**: AI models for summarization and synthesis
- **YouTube Transcript API**: Automated transcript extraction

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud Account with enabled APIs:
  - Text-to-Speech API
  - Vertex AI API
- FFmpeg (for audio processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/podcast-digest-agent.git
   cd podcast-digest-agent
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up Frontend**
   ```bash
   cd podcast-digest-ui
   npm install
   ```

4. **Configure Environment**

   Create `.env` file in the root directory:
   ```bash
   # Google Cloud Configuration
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

   # API Configuration
   DEBUG=false
   LOG_LEVEL=INFO

   # Directories
   OUTPUT_AUDIO_DIR=./output_audio
   INPUT_DIR=./input
   ```

5. **Google Cloud Authentication**
   ```bash
   # Option 1: Service Account Key
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"

   # Option 2: Application Default Credentials
   gcloud auth application-default login
   ```

### Running the Application

1. **Start the Backend**
   ```bash
   python src/main.py
   ```
   The API will be available at `http://localhost:8000`

2. **Start the Frontend** (in a new terminal)
   ```bash
   cd podcast-digest-ui
   npm run dev
   ```
   The web interface will be available at `http://localhost:3000`

3. **Process Your First Podcast**
   - Open `http://localhost:3000`
   - Paste a YouTube podcast URL
   - Click "Generate Digest"
   - Watch the real-time processing visualization
   - Listen to your AI-generated digest!

## 📚 Usage

### Web Interface

1. **Submit URLs**: Paste YouTube podcast URLs in the input field
2. **Monitor Progress**: Watch the agent workflow visualization in real-time
3. **Listen**: Play the generated audio digest directly in the browser
4. **History**: Access previously processed podcasts

### API Endpoints

- `POST /api/v1/process_youtube_url` - Submit URL for processing
- `GET /api/v1/status/{task_id}` - Check processing status
- `WS /api/v1/ws/status/{task_id}` - Real-time status updates
- `GET /api/v1/history` - Retrieve processing history
- `GET /api/v1/config` - Get configuration options
- `GET /audio/{filename}` - Serve generated audio files

### Command Line (Legacy)

```bash
# Add URLs to input file
echo "https://youtube.com/watch?v=example" > input/youtube_links.txt

# Run processing pipeline
python src/runners/simple_pipeline.py

# Generated audio will be in output_audio/
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test module
pytest tests/agents/test_summarizer_agent.py
```

### Frontend Tests
```bash
cd podcast-digest-ui
npm test
```

### Code Quality
```bash
# Linting
ruff check src/
ruff check --fix src/

# Formatting
black src/

# Type checking
mypy src/
```

## 📁 Project Structure

```
podcast-digest-agent/
├── src/                          # Python backend
│   ├── agents/                   # Specialized processing agents
│   ├── api/                      # FastAPI routes and endpoints
│   ├── config/                   # Configuration management
│   ├── core/                     # Core services (WebSocket, tasks)
│   ├── models/                   # Pydantic data models
│   ├── tools/                    # Utility tools and functions
│   └── runners/                  # Pipeline orchestration
├── podcast-digest-ui/            # Next.js frontend
│   ├── src/
│   │   ├── app/                  # Next.js app router
│   │   ├── components/           # React components
│   │   ├── contexts/             # React contexts
│   │   └── types/                # TypeScript definitions
│   └── public/                   # Static assets
├── tests/                        # Backend test suite
├── specs/                        # Project specifications
├── input/                        # Input files (URLs)
├── output_audio/                 # Generated audio files
└── requirements.txt              # Python dependencies
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|-------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud service account key | Required |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `OUTPUT_AUDIO_DIR` | Audio output directory | `./output_audio` |
| `INPUT_DIR` | Input files directory | `./input` |

### Google Cloud Setup

1. Create a Google Cloud Project
2. Enable the following APIs:
   - Text-to-Speech API
   - Vertex AI API
3. Create a service account with appropriate permissions
4. Download the service account key JSON file
5. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## 🚀 Deployment

### Production Deployment

The application is designed for deployment with:
- **Backend**: Google Cloud Run
- **Frontend**: Vercel

#### Quick Deploy

```bash
# Deploy backend to Cloud Run
./scripts/deploy-backend.sh your-project-id us-central1

# Deploy frontend to Vercel
./scripts/deploy-frontend.sh
```

#### Manual Deployment

**Backend (Cloud Run)**
```bash
# Build and deploy
gcloud run deploy podcast-digest-agent \
  --source . \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated
```

**Frontend (Vercel)**
```bash
cd podcast-digest-ui
vercel --prod
```

#### Environment Configuration

**Backend Production Variables**
```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

**Frontend Production Variables**
```bash
NEXT_PUBLIC_API_URL=https://your-backend.run.app
```

For detailed deployment instructions, see the [Deployment Guide](DEPLOYMENT_GUIDE.md).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Run tests and ensure code quality
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Guidelines

- Write tests for new features (TDD approach)
- Follow code style guidelines (Black, Ruff)
- Add type hints for all functions
- Update documentation for API changes
- Ensure all tests pass before submitting

## 📈 Roadmap

### Current Phase: Core Features ✅
- [x] Basic processing pipeline
- [x] Web interface with real-time updates
- [x] Agent workflow visualization
- [x] WebSocket integration

### Phase 2: Enhanced Features 🚧
- [ ] Enhanced audio player with waveform
- [ ] Google Speech Studio multi-speaker TTS
- [ ] Advanced configuration options
- [ ] Improved error handling and recovery

### Phase 3: Advanced Features 📋
- [ ] Cloud storage integration
- [ ] Batch processing
- [ ] Custom voice training
- [ ] Multi-language support
- [ ] API rate limiting and authentication

## 🐛 Troubleshooting

### Common Issues

**Google Cloud Authentication Errors**
```bash
# Verify credentials
gcloud auth list
gcloud config list

# Re-authenticate if needed
gcloud auth application-default login
```

**Audio Processing Errors**
```bash
# Install FFmpeg (macOS)
brew install ffmpeg

# Install FFmpeg (Ubuntu)
sudo apt update && sudo apt install ffmpeg
```

**WebSocket Connection Issues**
- Check firewall settings
- Ensure both frontend and backend are running
- Verify WebSocket endpoint URLs


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Cloud Platform for AI and TTS services
- OpenAI for inspiration in agent-based architectures
- The open-source community for excellent tools and libraries

---

**Made with ❤️ by the SilentKnight87**
