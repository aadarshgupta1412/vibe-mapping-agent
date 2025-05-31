# Frontend - Vibe Mapping Agent

A modern chat interface built with Next.js for the Vibe Mapping Agent shopping assistant.

## 🌟 Live Demo

**Deployed at**: [https://vibe-mapping-agent.vercel.app](https://vibe-mapping-agent.vercel.app)

## 🛠️ Tech Stack

- **Framework**: Next.js 15.3.3 (App Router)
- **Language**: TypeScript 5.6.2
- **Styling**: Tailwind CSS 3.4.13
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **State Management**: React hooks (useState, useEffect)
- **HTTP Client**: Fetch API with EventSource for streaming
- **Deployment**: Vercel

## ✨ Features

- **Real-time Chat Interface**: Streaming responses with typing indicators
- **Modern UI**: Clean, responsive design with shadcn/ui components
- **Product Recommendations**: Display structured product data with images
- **Conversation Memory**: Maintains chat history during session
- **Error Handling**: Graceful fallbacks for API failures
- **Mobile Responsive**: Works seamlessly on all device sizes

## 🚀 Quick Start

### Prerequisites
- Node.js 18 or higher
- npm or yarn
- Backend API running (see [../backend/README.md](../backend/README.md))

### Development Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Set up environment variables**
   ```bash
   # Create .env.local file
   echo "BACKEND_URL=http://localhost:8080" > .env.local
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── globals.css        # Global styles and Tailwind imports
│   ├── layout.tsx         # Root layout component
│   └── page.tsx           # Home page with chat interface
├── components/            # React components
│   ├── ui/               # shadcn/ui base components
│   │   ├── button.tsx    # Button component
│   │   ├── card.tsx      # Card component
│   │   ├── input.tsx     # Input component
│   │   └── scroll-area.tsx # Scroll area component
│   ├── chat-interface.tsx # Main chat component
│   ├── message-list.tsx   # Message display component
│   └── product-card.tsx   # Product recommendation component
└── lib/                  # Utilities (inlined due to build issues)
    └── types.ts          # TypeScript type definitions
```

## 🔧 Environment Variables

### Local Development (.env.local)
```bash
BACKEND_URL=http://localhost:8080
```

### Production (Vercel)
```bash
BACKEND_URL=https://vibe-mapping-agent-production.up.railway.app
```

## 📦 Key Components

### ChatInterface (`components/chat-interface.tsx`)
Main chat component that handles:
- User message input
- Streaming response from backend
- Message state management
- Error handling

### MessageList (`components/message-list.tsx`)
Renders chat messages with:
- User and assistant message styling
- Product recommendation cards
- Auto-scrolling to latest messages

### ProductCard (`components/product-card.tsx`)
Displays product recommendations with:
- Product images and details
- Structured attribute display
- Responsive card layout

## 🚢 Deployment

### Vercel (Recommended)

1. **Connect GitHub Repository**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel auto-detects Next.js configuration

2. **Set Environment Variables**
   ```bash
   BACKEND_URL=https://vibe-mapping-agent-production.up.railway.app
   ```

3. **Deploy**
   - Automatic deployment on push to main branch
   - Preview deployments for pull requests

### Manual Deployment

```bash
# Build for production
npm run build

# Export static files (if needed)
npm run export

# Start production server
npm start
```

## 🛠️ Development Issues Resolved

### 1. Module Resolution Problems
**Issue**: Vercel builds failed with `"Module not found: Can't resolve '@/lib/utils'"`

**Root Cause**: 
- Nested duplicate `frontend/vibe-mapping-agent/` directory with outdated code
- TypeScript path alias issues in production builds

**Solution**: 
- Removed duplicate directory structure
- Inlined utility functions directly in components instead of using path aliases
- Added explicit `cn` function in each component:

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### 2. Node.js Version Compatibility
**Issue**: Vercel deployment failed due to Node.js version requirements

**Solution**: Added engines specification to `package.json`:
```json
{
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### 3. TypeScript Configuration
**Issue**: Module resolution problems with different configurations

**Solution**: Maintained clean `tsconfig.json` with standard Next.js configuration:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

## 🧪 Testing

### Build Testing
```bash
# Test production build
npm run build

# Check for TypeScript errors
npm run type-check

# Run linting
npm run lint
```

### Manual Testing Checklist
- [ ] Chat interface loads correctly
- [ ] Messages send and receive properly
- [ ] Streaming responses work
- [ ] Product cards display correctly
- [ ] Mobile responsiveness works
- [ ] Error states handle gracefully

## 🎨 Styling Guide

### Tailwind CSS Classes
- **Primary Colors**: `bg-blue-600`, `text-blue-600`
- **Background**: `bg-gray-50`, `bg-white`
- **Text Colors**: `text-gray-900`, `text-gray-600`
- **Spacing**: Consistent `p-4`, `m-4`, `gap-4`

### Component Styling
```typescript
// Example component styling
<div className="flex flex-col h-screen bg-gray-50">
  <div className="flex-1 overflow-hidden">
    <div className="h-full p-4">
      {/* Content */}
    </div>
  </div>
</div>
```

## 📚 API Integration

### Backend Communication
```typescript
// Streaming API call
const response = await fetch(`${process.env.BACKEND_URL}/api/chat`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    messages: [...messages, userMessage],
    stream: true
  })
});

// Handle streaming response
const reader = response.body?.getReader();
// Process stream chunks...
```

### Message Types
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  products?: Product[];
}

interface Product {
  id: string;
  name: string;
  price: number;
  image_url: string;
  attributes: Record<string, any>;
}
```

## 🔗 Related Documentation

- **Main README**: [../README.md](../README.md)
- **Backend README**: [../backend/README.md](../backend/README.md)
- **Next.js Documentation**: [nextjs.org/docs](https://nextjs.org/docs)
- **shadcn/ui Documentation**: [ui.shadcn.com](https://ui.shadcn.com)
- **Tailwind CSS**: [tailwindcss.com/docs](https://tailwindcss.com/docs)
