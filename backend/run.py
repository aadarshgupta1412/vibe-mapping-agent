import argparse
import logging
import os

import uvicorn

from app.core.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()
    
    # Determine reload setting from environment or command line
    # Command line takes precedence over environment variable
    reload_mode = args.reload or (os.environ.get("RELOAD", "").lower() == "true")
    
    # Get port from environment (Railway sets this) or use local dev default
    port = int(os.environ.get("PORT", "8080"))
    
    # Log environment variables for debugging
    logger.info(f"Environment PORT: {os.environ.get('PORT', 'not set')}")
    logger.info(f"Using PORT: {port}")
    logger.info(f"Settings HOST: {settings.HOST}")
    logger.info(f"Starting server on {settings.HOST}:{port}")
    logger.info(f"Debug mode: {settings.DEBUG}, Reload: {reload_mode}")
    
    # Run the server with the determined reload setting
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=port, 
        reload=reload_mode
    )
