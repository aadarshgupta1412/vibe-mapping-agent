import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import check_connection, close_db, init_db
from app.routes import router
from app.services.chat_service import close_chat_service, init_chat_service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title=settings.PROJECT_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services on startup
@app.on_event("startup")
async def startup_services():
    logger.info("Initializing services")
    # Initialize database connections
    db_manager = init_db()
    logger.info("Database connections initialized")
    
    # Check database connection
    connection_ok = await check_connection()
    if not connection_ok:
        logger.warning("Supabase connection check failed")
    
    # Initialize chat service
    init_chat_service()
    logger.info("Chat service initialized")
    
# Close services on shutdown
@app.on_event("shutdown")
async def shutdown_services():
    logger.info("Shutting down services")
    # Close chat service
    close_chat_service()
    logger.info("Chat service closed")
    
    # Close database connections
    close_db()
    logger.info("Database connections closed")

# Define models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class Product(BaseModel):
    id: str
    name: str
    category: str
    price: float
    fabric: str
    fit: str
    color: str
    pattern: Optional[str] = None
    style: Optional[List[str]] = None
    occasion: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    recommendations: Optional[List[Product]] = None

# Mock product data
MOCK_PRODUCTS = [
    {
        "id": "T001",
        "name": "Sun-Dapple Floral Top",
        "category": "top",
        "price": 72,
        "fabric": "Linen",
        "fit": "Relaxed",
        "color": "Pastel yellow",
        "pattern": "Floral"
    },
    {
        "id": "J002",
        "name": "Urban Edge Jeans",
        "category": "bottom",
        "price": 95,
        "fabric": "Denim",
        "fit": "Slim",
        "color": "Dark blue",
        "pattern": "Solid"
    },
    {
        "id": "D003",
        "name": "Breezy Day Dress",
        "category": "dress",
        "price": 120,
        "fabric": "Cotton",
        "fit": "A-line",
        "color": "Mint green",
        "pattern": "Striped"
    },
    {
        "id": "S004",
        "name": "Coastal Linen Shirt",
        "category": "top",
        "price": 85,
        "fabric": "Linen",
        "fit": "Regular",
        "color": "White",
        "pattern": "Solid"
    },
    {
        "id": "B005",
        "name": "Power Move Blazer",
        "category": "outerwear",
        "price": 150,
        "fabric": "Wool blend",
        "fit": "Tailored",
        "color": "Black",
        "pattern": "Solid"
    },
    {
        "id": "S006",
        "name": "Silky Evening Skirt",
        "category": "bottom",
        "price": 85,
        "fabric": "Silk",
        "fit": "A-line",
        "color": "Deep burgundy",
        "pattern": "Solid"
    }
]

# Include the router in the app
app.include_router(router, prefix=settings.API_V1_STR)

@app.get("/")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
