# Vibe Mapping Agent

A conversational shopping assistant that translates vibe-based clothing queries into structured attributes and provides personalized product recommendations.

## 🌟 Live Deployments

- **Frontend**: [https://vibe-mapping-agent.vercel.app](https://vibe-mapping-agent.vercel.app) (Vercel)
- **Backend API**: [https://vibe-mapping-agent-production.up.railway.app](https://vibe-mapping-agent-production.up.railway.app) (Railway)

## 🎯 Project Overview

This project implements a conversational agent that:

1. **Takes vibe-based queries** (e.g., "something cute for brunch", "professional but trendy")
2. **Asks targeted follow-up questions** to clarify preferences 
3. **Maps vague terms to structured attributes** (fabric, fit, color, style)
4. **Recommends products** from a catalog with detailed justification
5. **Provides streaming responses** for real-time conversation

## 🏗️ Architecture

### Frontend (Next.js + Vercel)
- **Framework**: Next.js 15.3.3 with TypeScript
- **UI Components**: shadcn/ui with Tailwind CSS
- **Deployment**: Vercel with automatic GitHub integration
- **Features**: Real-time chat interface, product recommendation display

### Backend (FastAPI + Railway)
- **Framework**: FastAPI with async/await support
- **AI/ML**: LangGraph for conversation flow + Google Gemini 2.0 Flash
- **Database**: Supabase (PostgreSQL) for product catalog and user data
- **Deployment**: Railway with automatic GitHub integration
- **Features**: Streaming responses, structured data extraction, product search

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.8+
- Supabase account (for database)
- Google Gemini API key

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/aadarshgupta1412/vibe-mapping-agent.git
   cd vibe-mapping-agent
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Create .env file with your credentials
   cp .env.example .env
   # Edit .env with your API keys
   
   # Run the server
   python run.py
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   
   # Set backend URL for local development
   echo "BACKEND_URL=http://localhost:8080" > .env.local
   
   # Run the development server  
   npm run dev
   ```

4. **Open your browser**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8080

## 📁 Project Structure

```
vibe-mapping-agent/
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   └── lib/             # Utility functions
│   ├── package.json         # Frontend dependencies
│   └── README.md           # Frontend-specific documentation
├── backend/                 # FastAPI application  
│   ├── app/
│   │   ├── main.py         # FastAPI entry point
│   │   ├── core/           # Configuration and database
│   │   ├── routes/         # API endpoints
│   │   └── services/       # Business logic (LLM, chat, etc.)
│   ├── requirements.txt    # Python dependencies
│   ├── run.py             # Server startup script
│   └── README.md          # Backend-specific documentation
└── README.md              # This file
```

## 🔧 Environment Variables

### Backend (.env)
```bash
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# LLM API
GEMINI_API_KEY=your_gemini_api_key

# Server Configuration (Production)
DEBUG=False
RELOAD=False
CORS_ORIGINS_STR=https://vibe-mapping-agent.vercel.app,http://localhost:3000
```

### Frontend (.env.local)
```bash
# Backend API URL
BACKEND_URL=https://vibe-mapping-agent-production.up.railway.app
```

## 🚢 Deployment

### Frontend (Vercel)
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard:
   - `BACKEND_URL`: `https://vibe-mapping-agent-production.up.railway.app`
3. Deploy automatically on push to main branch

### Backend (Railway)  
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard:
   - `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`
   - `DEBUG=False`, `RELOAD=False`
   - `CORS_ORIGINS_STR=https://vibe-mapping-agent.vercel.app`
3. Deploy automatically on push to main branch

## 🛠️ Development Notes

### Issues Resolved
- **Module Resolution**: Fixed Vercel build errors by inlining utility functions instead of using path aliases
- **Railway Port Configuration**: Set default port to 8080 for Railway compatibility  
- **Dependency Conflicts**: Resolved langchain ecosystem version conflicts in requirements.txt
- **Node.js Compatibility**: Added engines field to package.json for Vercel deployment

### Key Features
- **Streaming Responses**: Real-time conversation with EventSource/SSE
- **Structured Data Extraction**: Convert natural language to product attributes
- **Product Search**: Query Supabase catalog with semantic matching
- **Conversation Memory**: Maintain context across multiple turns
- **Error Handling**: Graceful fallbacks for API failures

## 🧪 Testing

### Backend Testing
```bash
cd backend
# Test the API endpoint
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "I need something casual for weekend"}], "stream": false}'
```

### Frontend Testing
```bash
cd frontend
npm run build    # Test production build
npm run lint     # Check code quality
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add feature'`
5. Push to your fork: `git push origin feature-name`
6. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Live Demo**: [vibe-mapping-agent.vercel.app](https://vibe-mapping-agent.vercel.app)
- **GitHub Repository**: [github.com/aadarshgupta1412/vibe-mapping-agent](https://github.com/aadarshgupta1412/vibe-mapping-agent)
- **Frontend Details**: [frontend/README.md](frontend/README.md)
- **Backend Details**: [backend/README.md](backend/README.md)