"""
Chat service module for the Vibe Mapping Agent.

This module provides the ChatService class, which handles processing chat messages
and generating responses using the AgentProcessor.
"""

import logging
from typing import Any, AsyncIterable, Dict, List, Optional

# Set up logger
logger = logging.getLogger(__name__)

# Import the agent processor
from .agent_processor import get_agent_processor, init_agent_processor, close_agent_processor


class ChatService:
    """
    Service for handling chat interactions using the AgentProcessor.
    
    This service manages the conversation flow, processes user messages,
    and generates appropriate responses using the LLM and available tools.
    """
    
    def __init__(self):
        """Initialize the ChatService."""
        self._agent_processor = None
    
    async def init(self):
        """Initialize the chat service and agent processor."""
        try:
            # Initialize the agent processor
            self._agent_processor = await init_agent_processor()
            logger.info("Chat service initialized successfully")
            return self._agent_processor
        except Exception as e:
            logger.error(f"Error initializing chat service: {str(e)}")
            raise
    
    def close(self):
        """Close any resources."""
        try:
            # Close the agent processor
            close_agent_processor()
            logger.info("Chat service closed successfully")
        except Exception as e:
            logger.error(f"Error closing chat service: {str(e)}")
    
    async def process_chat_message(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Process a chat message through the agent processor.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Dictionary containing the response and any additional data
        """
        if not self._agent_processor:
            await self.init()
        
        try:
            # Validate and format messages
            formatted_messages = self._format_messages(messages)
            
            # Process the messages through the agent processor
            result = await self._agent_processor.process(formatted_messages)
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "tool_outputs": result.get("tool_outputs", []),
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            return {
                "success": False,
                "response": "I encountered an error processing your message. Please try again.",
                "tool_outputs": [],
                "error": str(e)
            }
    
    async def process_chat_message_stream(self, messages: List[Dict[str, str]]) -> AsyncIterable[Dict[str, Any]]:
        """
        Process a chat message and stream the response chunks.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Yields:
            Dictionary chunks containing streaming response data
        """
        if not self._agent_processor:
            await self.init()
        
        try:
            # Validate and format messages
            formatted_messages = self._format_messages(messages)
            
            # Process the messages through the agent processor with streaming
            async for chunk in self._agent_processor.process_stream(formatted_messages):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            yield {
                "type": "error",
                "data": {"error": str(e)},
                "node": "chat_service"
            }
    
    def _format_messages(self, messages: List[Any]) -> List[Dict[str, str]]:
        """
        Format messages to ensure they have the correct structure.
        
        Args:
            messages: List of messages in various formats
            
        Returns:
            List of properly formatted message dictionaries
        """
        formatted_messages = []
        
        for msg in messages:
            if isinstance(msg, dict):
                # Already a dictionary, validate it has required keys
                if "role" in msg and "content" in msg:
                    formatted_messages.append({
                        "role": msg["role"],
                        "content": str(msg["content"])
                    })
                else:
                    logger.warning(f"Message missing required keys: {msg}")
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                # Message object with role and content attributes
                formatted_messages.append({
                    "role": msg.role,
                    "content": str(msg.content)
                })
            else:
                logger.warning(f"Unrecognized message format: {msg}")
        
        return formatted_messages


# Singleton instance management
_chat_service_instance = None

def get_chat_service() -> ChatService:
    """Get the singleton instance of ChatService."""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance

async def init_chat_service() -> ChatService:
    """Initialize the chat service."""
    try:
        service = get_chat_service()
        await service.init()
        return service
    except Exception as e:
        logger.error(f"Failed to initialize chat service: {str(e)}")
        raise

def close_chat_service():
    """Close the chat service."""
    try:
        service = get_chat_service()
        service.close()
    except Exception as e:
        logger.error(f"Error closing chat service: {str(e)}")
