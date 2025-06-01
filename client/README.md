# Podcast Digest Agent - Frontend

Modern Next.js frontend for the Podcast Digest Agent application.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server  
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 🏗️ Architecture

This frontend is built with:

- **Next.js 15** with App Router
- **TypeScript** for type safety
- **shadcn/ui** for UI components  
- **TanStack Query** for data fetching
- **Motion.dev** for animations

## 🎯 Key Components

- **HeroSection**: Main landing page with URL input
- **ProcessingVisualizer**: Real-time processing animation
- **RateLimitNotice**: User-friendly rate limit feedback
- **PlayDigestButton**: Audio playback with controls

## ⚙️ Configuration

Create `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production, set your Cloud Run backend URL.

## 🧪 Development

```bash
# Run development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Build locally
npm run build
```

## 📦 Deployment

Deploy to Vercel:
```bash
vercel --prod
```

Make sure to set `NEXT_PUBLIC_API_URL` environment variable in Vercel dashboard.
