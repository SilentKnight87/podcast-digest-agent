#!/bin/bash

echo "🎙️ Podcast Digest Agent Setup"
echo "=============================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Check Node.js
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi
node_version=$(node --version)
echo "✅ Node.js $node_version"

# Setup backend
echo ""
echo "Setting up backend..."
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy .env if it doesn't exist
if [ ! -f "../.env" ]; then
    cp ../.env.example ../.env
    echo "📝 Created .env file - please edit it with your credentials"
fi

# Setup frontend
echo ""
echo "Setting up frontend..."
cd ../client
npm install

if [ ! -f ".env.local" ]; then
    cp .env.example .env.local
    echo "📝 Created client/.env.local file"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Google API credentials"
echo "2. Start backend: cd server && source venv/bin/activate && python src/main.py"
echo "3. Start frontend: cd client && npm run dev"
echo "4. Visit http://localhost:3000"
echo ""
echo "Happy podcasting! 🎧"