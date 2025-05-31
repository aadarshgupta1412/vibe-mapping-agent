from fastapi import APIRouter

from .chat import router as chat_router

# Create a main router that includes all other routers
router = APIRouter()

# Include the chat router
router.include_router(chat_router)
