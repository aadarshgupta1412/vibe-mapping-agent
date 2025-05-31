# Backend - Vibe Mapping Agent API

A FastAPI-based conversational agent that maps vibe-based clothing queries to structured attributes and provides product recommendations.

## 🌟 Live API

**Deployed at**: [https://vibe-mapping-agent-production.up.railway.app](https://vibe-mapping-agent-production.up.railway.app)

- **API Documentation**: [/docs](https://vibe-mapping-agent-production.up.railway.app/docs) (Swagger UI)
- **Alternative Docs**: [/redoc](https://vibe-mapping-agent-production.up.railway.app/redoc) (ReDoc)

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.115.6 with async/await
- **Language**: Python 3.8+
- **AI/ML**: 
  - Google Gemini 2.0 Flash (via `google-generativeai>=0.8.0`)
  - LangGraph 0.2.60 for conversation flow
  - LangChain ecosystem for LLM orchestration
- **Database**: Supabase (PostgreSQL) with `supabase>=2.0.2`
- **Server**: Uvicorn ASGI server
- **Deployment**: Railway with automatic GitHub integration

## ✨ Features

- **Conversational Agent**: Natural language processing with follow-up questions
- **Streaming Responses**: Real-time conversation with Server-Sent Events (SSE)
- **Vibe Mapping**: Translate natural language to structured product attributes
- **Product Search**: Query Supabase catalog with semantic matching
- **Memory Management**: Maintain conversation context across turns
- **Error Handling**: Graceful fallbacks and detailed error responses
- **CORS Support**: Configurable origins for frontend integration

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Supabase account with database setup
- Google Gemini API key
- pip or pipenv for dependency management

### Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your credentials
   nano .env
   ```

3. **Run the development server**
   ```bash
   python run.py
   ```

4. **Test the API**
   - API Base: http://localhost:8080
   - Swagger UI: http://localhost:8080/docs
   - ReDoc: http://localhost:8080/redoc

## 📁 Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── core/                   # Core configuration and database
│   ├── config.py          # Pydantic settings with env var loading
│   └── database.py        # Supabase client initialization
├── routes/                 # API endpoints
│   ├── __init__.py
│   ├── chat.py           # Chat endpoint with streaming support
│   └── health.py         # Health check endpoints
├── services/              # Business logic
│   ├── __init__.py
│   ├── llm_service.py    # LLM integration and chat logic
│   ├── agent.py          # LangGraph agent implementation
│   └── database_service.py # Supabase database operations
└── models/                # Pydantic models
    ├── __init__.py
    ├── chat.py           # Chat request/response models
    └── product.py        # Product data models
```

## 🔧 Environment Variables

### Required (.env)
```bash
# Database Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key

# Optional: Portkey Gateway (for LLM routing/monitoring)
PORTKEY_API_KEY=your_portkey_api_key
PORTKEY_VIRTUAL_KEY=your_portkey_virtual_key
PORTKEY_GATEWAY_URL=https://api.portkey.ai/v1/proxy
```

### Server Configuration (.env)
```bash
# Server Settings
PORT=8080                              # Server port (Railway requires 8080)
HOST=0.0.0.0                          # Bind to all interfaces
DEBUG=False                           # Enable debug mode for development
RELOAD=False                          # Enable auto-reload for development

# CORS Settings
CORS_ORIGINS_STR=https://vibe-mapping-agent.vercel.app,http://localhost:3000

# LLM Model Selection
LLM_MODEL=gemini-2.0-flash           # Default model to use
```

## 📚 API Endpoints

### Chat Endpoint
```http
POST /api/chat
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "I need something cute for brunch"
    }
  ],
  "stream": false
}
```

**Response (Non-streaming)**:
```json
{
  "message": {
    "role": "assistant", 
    "content": "I'd love to help you find something cute for brunch! ..."
  },
  "products": [
    {
      "id": "prod_123",
      "name": "Floral Midi Dress",
      "price": 89.99,
      "image_url": "https://...",
      "attributes": {
        "style": "casual",
        "occasion": "brunch",
        "color": "pastel"
      }
    }
  ]
}
```

**Streaming Response** (when `stream: true`):
```
data: {"type": "message_chunk", "content": "I'd love to help"}
data: {"type": "message_chunk", "content": " you find something"}
data: {"type": "products", "products": [...]}
data: {"type": "done"}
```

### Health Check
```http
GET /health
```

```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00Z",
  "services": {
    "database": "connected",
    "llm": "available"
  }
}
```

## 🧠 LLM Agent Architecture

### LangGraph Workflow
```python
# Simplified agent flow
def create_agent_workflow():
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("understand_query", understand_user_query)
    workflow.add_node("ask_questions", ask_follow_up_questions)
    workflow.add_node("extract_attributes", extract_product_attributes)
    workflow.add_node("search_products", search_product_catalog)
    workflow.add_node("format_response", format_final_response)
    
    # Define flow
    workflow.add_edge(START, "understand_query")
    workflow.add_conditional_edges(
        "understand_query",
        should_ask_questions,
        {
            "ask": "ask_questions",
            "extract": "extract_attributes"
        }
    )
    
    return workflow.compile()
```

### State Management
```python
class ConversationState(TypedDict):
    messages: List[BaseMessage]
    user_query: str
    extracted_attributes: Dict[str, Any]
    follow_up_question: Optional[str]
    products: List[Product]
    conversation_complete: bool
```

## 🚢 Deployment

### Railway (Production)

1. **Connect GitHub Repository**
   - Go to [railway.app](https://railway.app)
   - Import your GitHub repository
   - Railway auto-detects Python application

2. **Set Environment Variables**
   ```bash
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   GEMINI_API_KEY=your_gemini_api_key
   DEBUG=False
   RELOAD=False
   CORS_ORIGINS_STR=https://vibe-mapping-agent.vercel.app
   ```

3. **Deploy**
   - Automatic deployment on push to main branch
   - Railway provides HTTPS endpoint automatically

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="your_url"
export SUPABASE_KEY="your_key"
export GEMINI_API_KEY="your_key"

# Run production server
python run.py
```

## 🛠️ Development Issues Resolved

### 1. Railway Dependency Conflicts
**Issue**: Version conflicts between langchain ecosystem packages

**Root Cause**: 
- `gotrue==2.8.1` vs `supabase 2.0.2` requirements
- `langchain-community==0.3.13` vs `langchain==0.1.0`
- `langsmith==0.2.11` vs `langchain 0.1.20`

**Solution**: Updated `requirements.txt` with compatible versions:
```txt
# LangChain ecosystem with compatible versions
langchain>=0.1.20
langchain-community>=0.3.13
langsmith>=0.2.11
langchain-google-genai>=2.0.8
langgraph>=0.2.60

# Supabase with compatible gotrue
supabase>=2.0.2

# Updated Google Generative AI
google-generativeai>=0.8.0
```

### 2. Railway Port Configuration
**Issue**: Railway returned 502 errors despite successful builds

**Root Cause**: 
- Backend ran on port 8000 internally
- Railway expected apps to bind to assigned PORT (8080)
- HTTP→HTTPS redirect issues

**Solution**: Updated default port in `config.py`:
```python
class Settings(BaseSettings):
    PORT: int = Field(default=8080)  # Changed from 8000
    HOST: str = Field(default="0.0.0.0")
```

### 3. Environment Variable Parsing
**Issue**: Boolean environment variables not parsed correctly

**Solution**: Added model validator in `config.py`:
```python
@model_validator(mode="after")
def parse_boolean_env_vars(self):
    debug_str = os.getenv("DEBUG", "True")
    reload_str = os.getenv("RELOAD", "True")
    
    self.DEBUG = debug_str.lower() in ("true", "1", "t")
    self.RELOAD = reload_str.lower() in ("true", "1", "t")
    return self
```

### 4. CORS Configuration
**Issue**: Frontend couldn't communicate with backend due to CORS errors

**Solution**: Configurable CORS origins with proper parsing:
```python
CORS_ORIGINS_STR: str = Field(default="http://localhost:3000")

@model_validator(mode="after")
def parse_cors_origins(self):
    origins = self.CORS_ORIGINS_STR
    if origins:
        self.cors_allow_origins = [
            origin.strip() for origin in origins.split(",") 
            if origin.strip()
        ]
    return self
```

## 🧪 Testing

### Manual API Testing
```bash
# Test health endpoint
curl http://localhost:8080/health

# Test chat endpoint (non-streaming)
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I need something casual for weekend"}
    ],
    "stream": false
  }'

# Test streaming endpoint
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Show me trendy jackets"}
    ],
    "stream": true
  }'
```

### Database Testing
```python
# Test Supabase connection
from app.core.database import get_supabase_client

async def test_db_connection():
    client = await get_supabase_client()
    result = client.table('products').select('*').limit(1).execute()
    print(f"Database connection: {'OK' if result.data else 'Failed'}")
```

## 📊 Monitoring & Logging

### Application Logs
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Railway Logs
Access deployment logs through Railway dashboard:
- Build logs for dependency issues
- Runtime logs for application errors
- Request logs for API debugging

## 🔗 Related Documentation

- **Main README**: [../README.md](../README.md)
- **Frontend README**: [../frontend/README.md](../frontend/README.md)
- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **LangGraph Documentation**: [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph)
- **Supabase Python Client**: [supabase.com/docs/reference/python](https://supabase.com/docs/reference/python)
- **Railway Documentation**: [docs.railway.app](https://docs.railway.app) 