import json
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.services.chat_service import get_chat_service

router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    recommendations: Optional[List[Dict[str, Any]]] = None

class StreamChunk(BaseModel):
    type: str  # 'content', 'recommendations', or 'error'
    data: Any
    done: bool = False

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """
    Process a chat message and return a response with optional product recommendations.
    If stream=True, returns a streaming response using EventSourceResponse.
    """
    client_host = req.client.host if req.client else "unknown"
    logger.debug(f"Chat request from {client_host}: {request.dict()}")
    
    # Convert pydantic models to dicts for the chat service
    messages = [msg.dict() for msg in request.messages]
    
    # Handle streaming response if requested
    if request.stream:
        return EventSourceResponse(chat_event_generator(messages))
    
    # Process the chat message
    chat_service = get_chat_service()
    try:
        result = await chat_service.process_chat_message(messages)
        return ChatResponse(
            response=result["response"],
            recommendations=result.get("recommendations")
        )
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def chat_event_generator(messages: List[Dict[str, str]]):
    """
    Generate event stream for chat messages using the EventSourceResponse format.
    """
    request_id = str(uuid.uuid4())
    logger.debug(f"Starting event stream for request {request_id}")
    
    try:
        chat_service = get_chat_service()
        async for chunk in chat_service.process_chat_message_stream(messages):
            if chunk["type"] == "error":
                # Send error as a special event
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": chunk["data"],
                        "done": True
                    })
                }
                break
                
            elif chunk["type"] == "content":
                # Stream content chunks as message events
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "content",
                        "content": chunk["data"],
                        "done": False
                    })
                }
                
            elif chunk["type"] == "recommendations":
                # Stream recommendations as a separate event
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "recommendations",
                        "recommendations": chunk["data"],
                        "done": False
                    })
                }
                
            elif chunk["type"] == "done":
                # Final event
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "content",
                        "content": "",
                        "done": True
                    })
                }
                
    except Exception as e:
        logger.error(f"Error in event stream for request {request_id}: {e}")
        yield {
            "event": "error",
            "data": json.dumps({
                "message": str(e),
                "done": True
            })
        }
    
    logger.debug(f"Completed event stream for request {request_id}")
