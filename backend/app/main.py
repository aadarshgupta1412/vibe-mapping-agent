from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Vibe Mapping Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Vibe Mapping Agent API is running"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Get the last user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user messages provided")
    
    last_user_message = user_messages[-1].content.lower()
    
    # Simple keyword-based response logic
    response = "I'll help you find the perfect clothing based on your vibe! Would you like to specify any preferences for size or budget?"
    recommendations = []
    
    # Process based on keywords in the message
    if "casual" in last_user_message or "everyday" in last_user_message:
        response = "For casual wear, I'd recommend checking out our relaxed fit items. Here are some options that might match your vibe!"
        recommendations = [MOCK_PRODUCTS[0], MOCK_PRODUCTS[1], MOCK_PRODUCTS[3]]
    
    elif "formal" in last_user_message or "elegant" in last_user_message or "professional" in last_user_message:
        response = "For more formal occasions, we have several elegant options. Here are some recommendations that might suit your needs!"
        recommendations = [MOCK_PRODUCTS[4], MOCK_PRODUCTS[5]]
    
    elif "dress" in last_user_message:
        response = "Looking for a dress? Here's a beautiful option that might match what you're looking for!"
        recommendations = [MOCK_PRODUCTS[2]]
    
    elif "top" in last_user_message or "shirt" in last_user_message or "blouse" in last_user_message:
        response = "Here are some tops that might match your style!"
        recommendations = [MOCK_PRODUCTS[0], MOCK_PRODUCTS[3]]
    
    elif "bottom" in last_user_message or "pants" in last_user_message or "jeans" in last_user_message or "skirt" in last_user_message:
        response = "Here are some bottoms that might work for your style!"
        recommendations = [MOCK_PRODUCTS[1], MOCK_PRODUCTS[5]]
    
    # If this is a follow-up message and we have context from previous messages
    if len(request.messages) > 2:
        prev_assistant_msg = next((msg for msg in reversed(request.messages) if msg.role == "assistant"), None)
        if prev_assistant_msg and "specific occasion" in prev_assistant_msg.content.lower():
            if "work" in last_user_message or "office" in last_user_message:
                response = "Perfect for work! Here are some professional options that would look great in an office setting."
                recommendations = [MOCK_PRODUCTS[4], MOCK_PRODUCTS[3]]
            elif "weekend" in last_user_message or "casual" in last_user_message:
                response = "For weekend casual wear, these options would be perfect!"
                recommendations = [MOCK_PRODUCTS[0], MOCK_PRODUCTS[1]]
    
    return ChatResponse(response=response, recommendations=recommendations)
