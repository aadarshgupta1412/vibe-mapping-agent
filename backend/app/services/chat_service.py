"""
Chat Service

This module implements the LangGraph conversation flow for the vibe mapping agent.
It integrates the vibe mapper and product service to handle the conversation flow.
Uses a singleton pattern for the chat service with Supabase integration.
"""

import asyncio
import json
import logging
import os
from typing import (Any, AsyncGenerator, AsyncIterable, Dict, List, Optional,
                    TypedDict)

from langchain_core.messages import AIMessage, HumanMessage
from portkey_ai import Portkey

# Set up logger
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.database import get_supabase_client

from .vibe_mapper import map_vibe_query

# Try to import LangGraph, with fallback for development
from langgraph.graph import END, START, StateGraph

# Define our state type
class State(TypedDict):
    messages: List[Dict[str, str]]
    current_step: str
    attributes: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    follow_up_count: int


class ChatService:
    """Singleton chat service for handling conversation flow"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._chat_graph = None
        self._supabase = None
        self._portkey = None
        self._initialized = True
        logger.info("ChatService instance created")
    
    def init(self):
        """Initialize the chat service"""
        # Initialize Supabase client
        try:
            self._supabase = get_supabase_client()
            logger.info("Supabase client initialized in ChatService")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            self._supabase = None
        
        # Initialize Portkey for LLM calls
        try:
            self._portkey = Portkey(api_key=settings.PORTKEY_API_KEY)
            logger.info("Portkey client initialized for LLM calls")
        except Exception as e:
            logger.error(f"Failed to initialize Portkey: {str(e)}")
            self._portkey = None
        
        # Initialize chat graph
        self._chat_graph = self._create_graph()
        logger.info("Chat graph initialized")
    
    def close(self):
        """Clean up resources"""
        self._chat_graph = None
        self._supabase = None
        self._portkey = None
        logger.info("Chat service resources released")
    
    async def call_llm_stream(self, messages, system_prompt=None):
        """
        Call the LLM with the given messages using Portkey and stream the response.
        Returns an async generator that yields content chunks.
        """
        if not self._portkey and settings.PORTKEY_API_KEY:
            try:
                self._portkey = Portkey(
                    api_key=settings.PORTKEY_API_KEY,
                    virtual_key=settings.PORTKEY_VIRTUAL_KEY
                )
                logger.info("Portkey client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Portkey: {str(e)}")
        
        # Format messages for Portkey
        formatted_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation messages
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Get the last message for mock responses
        last_message = messages[-1]["content"] if messages else ""
        
        # Try to use Portkey if available
        portkey_success = False
        if self._portkey:
            try:
                # Streaming response
                stream_response = await self._portkey.chat.completions.create(
                    messages=formatted_messages,
                    model=settings.LLM_MODEL or "gemini-pro",  # Use Gemini Pro by default
                    stream=True,
                    max_tokens=1000,
                    headers={
                        "X-Portkey-Mode": "gateway",
                        "X-Portkey-Trace-Id": "vibe-mapping-agent-trace"
                    }
                )
                
                async for chunk in stream_response:
                    if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
                portkey_success = True
            except Exception as e:
                logger.error(f"Error streaming from Portkey: {str(e)}")
                # Fall through to mock implementation
        
        # Only use mock implementation if Portkey failed or is not available
        if not portkey_success:
            # Generate mock response based on message content
            if "size" in last_message.lower() or "budget" in last_message.lower():
                mock_response = "Thanks for sharing that information. What kind of style or occasion are you looking for?"
            elif any(word in last_message.lower() for word in ["casual", "formal", "party", "work"]):
                mock_response = "Great! Based on your preferences, I'll find some recommendations that might work for you."
            else:
                mock_response = "Could you tell me more about what size you're looking for and your budget range?"
            
            # Simulate streaming by yielding one word at a time
            for word in mock_response.split():
                yield word + " "
                await asyncio.sleep(0.1)  # Simulate delay
    
    async def call_llm(self, messages, system_prompt=None, stream=False):
        """
        Call the LLM with the given messages using Portkey.
        If stream=True, delegates to call_llm_stream which returns an async generator.
        Otherwise returns the complete response as a string.
        """
        if stream:
            # This is a bit of a hack - we can't directly return the generator
            # so we create a dummy async generator that just yields from the real one
            async def stream_wrapper():
                async for chunk in self.call_llm_stream(messages, system_prompt):
                    yield chunk
            return stream_wrapper()
        
        # For non-streaming mode
        if not self._portkey and settings.PORTKEY_API_KEY:
            try:
                self._portkey = Portkey(
                    api_key=settings.PORTKEY_API_KEY,
                    virtual_key=settings.PORTKEY_VIRTUAL_KEY
                )
                logger.info("Portkey client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Portkey: {str(e)}")
        
        # Format messages for Portkey
        formatted_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation messages
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Get the last message for mock responses
        last_message = messages[-1]["content"] if messages else ""
        
        # Try to use Portkey if available
        if self._portkey:
            try:
                # Regular response
                response = await self._portkey.chat.completions.create(
                    messages=formatted_messages,
                    model=settings.LLM_MODEL or "gemini-pro",  # Use Gemini Pro by default
                    max_tokens=1000,
                    headers={
                        "X-Portkey-Mode": "gateway",
                        "X-Portkey-Trace-Id": "vibe-mapping-agent-trace"
                    }
                )
                
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error calling LLM via Portkey: {str(e)}")
                # Fall through to mock implementation
        
        # Generate mock response based on message content
        if "size" in last_message.lower() or "budget" in last_message.lower():
            mock_response = "Thanks for sharing that information. What kind of style or occasion are you looking for?"
        elif any(word in last_message.lower() for word in ["casual", "formal", "party", "work"]):
            mock_response = "Great! Based on your preferences, I'll find some recommendations that might work for you."
        else:
            mock_response = "Could you tell me more about what size you're looking for and your budget range?"
        
        return mock_response
    
    async def process_initial_query(self, state: State) -> State:
        """
        Process the initial user query and extract vibe terms.
        """
        try:
            messages = state["messages"]
            user_query = messages[-1]["content"] if messages[-1]["role"] == "user" else ""
            
            # Extract vibe terms and map to attributes
            vibe_result = map_vibe_query(user_query)
            
            # Ensure vibe_result is properly serializable
            if hasattr(vibe_result, "__dict__"):
                vibe_result = vibe_result.__dict__
            
            # Store the attributes in the state
            state["attributes"] = vibe_result.get("attributes", {})
            
            # Initialize follow-up count
            state["follow_up_count"] = 0
            
            # Decide if we need follow-up questions
            if not state["attributes"] or len(state["attributes"]) < 2:
                state["current_step"] = "ask_follow_up"
            else:
                state["current_step"] = "generate_recommendations"
            
            # Generate response
            system_prompt = """
            You are a helpful shopping assistant that helps users find clothing based on their preferences.
            Extract key information from their query and ask follow-up questions if needed.
            Be conversational and friendly.
            """
            
            response = await self.call_llm(messages, system_prompt)
            
            # Add AI response to messages
            state["messages"].append({"role": "assistant", "content": response})
            
        except Exception as e:
            logger.error(f"Error in process_initial_query: {str(e)}")
            # Provide a fallback response if there's an error
            fallback_response = "I'm here to help you find clothing. Could you tell me more about what you're looking for?"
            state["messages"].append({"role": "assistant", "content": fallback_response})
            state["current_step"] = "ask_follow_up"
            state["attributes"] = {}
            state["follow_up_count"] = 0
        
        return state
    
    async def ask_follow_up(self, state: State) -> State:
        """
        Ask follow-up questions based on missing information.
        """
        messages = state["messages"]
        attributes = state["attributes"]
        
        # Increment follow-up count
        state["follow_up_count"] += 1
        
        # Determine what information we're missing
        missing_info = []
        if "occasion" not in attributes:
            missing_info.append("occasion")
        if "style" not in attributes:
            missing_info.append("style")
        if "fit" not in attributes:
            missing_info.append("fit")
        
        # Generate follow-up question
        system_prompt = f"""
        You are a helpful shopping assistant. The user is looking for clothing.
        Based on their previous messages, ask a specific follow-up question about their preferences.
        Focus on asking about: {', '.join(missing_info[:2])}.
        Keep your question short and specific.
        """
        
        response = await self.call_llm(messages, system_prompt)
        
        # Add AI response to messages
        state["messages"].append({"role": "assistant", "content": response})
        
        # Decide next step based on follow-up count
        if state["follow_up_count"] >= 2:
            state["current_step"] = "generate_recommendations"
        else:
            state["current_step"] = "process_follow_up"
        
        return state
    
    async def process_follow_up(self, state: State) -> State:
        """
        Process the user's response to a follow-up question.
        """
        messages = state["messages"]
        user_query = messages[-1]["content"] if messages[-1]["role"] == "user" else ""
        
        try:
            # Extract vibe terms and map to attributes from the follow-up response
            vibe_result = map_vibe_query(user_query)
            
            # Ensure vibe_result is properly serializable
            if hasattr(vibe_result, "__dict__"):
                vibe_result = vibe_result.__dict__
            
            # Merge with existing attributes
            for key, value in vibe_result.get("attributes", {}).items():
                if key in state["attributes"]:
                    # Ensure we're working with lists
                    if not isinstance(state["attributes"][key], list):
                        state["attributes"][key] = [state["attributes"][key]]
                    if not isinstance(value, list):
                        value = [value]
                        
                    state["attributes"][key].extend(value)
                    # Remove duplicates
                    state["attributes"][key] = list(set(state["attributes"][key]))
                else:
                    state["attributes"][key] = value
            
            # Increment follow-up count
            state["follow_up_count"] = state.get("follow_up_count", 0) + 1
            
            # Decide if we need more follow-up questions
            if state["follow_up_count"] < 2 and len(state["attributes"]) < 3:
                state["current_step"] = "ask_follow_up"
            else:
                state["current_step"] = "generate_recommendations"
                
        except Exception as e:
            logger.error(f"Error in process_follow_up: {str(e)}")
            # Fallback to recommendations if there's an error
            state["current_step"] = "generate_recommendations"
        
        return state
    
    async def generate_recommendations(self, state: State) -> State:
        """
        Generate product recommendations based on attributes.
        """
        messages = state["messages"]
        attributes = state["attributes"]
        
        # Instead of filtering products, just create a mock response
        # This will be replaced with actual database queries in the future
        recommendations = [
            {
                "id": "mock-1",
                "name": "Product based on your preferences",
                "category": "clothing",
                "price": 99.99,
                "attributes": attributes
            }
        ]
        
        # Store recommendations in state
        state["recommendations"] = recommendations
        
        # Generate response with recommendations
        system_prompt = f"""
        You are a helpful shopping assistant. Based on the user's preferences, recommend the following products:
        {json.dumps(recommendations, indent=2)}
        
        Format your response as follows:
        1. A brief introduction acknowledging their preferences
        2. A list of recommendations with key features
        3. A brief conclusion asking if they'd like to see more options or refine their search
        
        Keep your response conversational and friendly.
        """
        
        response = await self.call_llm(messages, system_prompt)
        
        # Add AI response to messages
        state["messages"].append({"role": "assistant", "content": response})
        
        # End the conversation flow
        state["current_step"] = END
        
        return state
    
    def router(self, state: State) -> str:
        """Route to the next step based on current_step in state"""
        return state["current_step"]
    
    def _create_graph(self):
        """Create the LangGraph workflow with Portkey integration."""
        # Initialize the graph
        graph = StateGraph(State)
        
        # Initialize Portkey LLM client if not already done
        if not self._portkey and settings.PORTKEY_API_KEY:
            try:
                self._portkey = Portkey(
                    api_key=settings.PORTKEY_API_KEY,
                    virtual_key=settings.PORTKEY_VIRTUAL_KEY
                )
                logger.info("Portkey client initialized in graph creation")
            except Exception as e:
                logger.error(f"Failed to initialize Portkey in graph creation: {str(e)}")
        
        # Configure LLM for LangGraph nodes
        if self._portkey:
            # Create a custom LLM handler that uses Portkey
            from typing import Any, Dict, Iterator, List, Optional, Union

            from langchain_core.language_models import BaseChatModel
            from langchain_core.messages import (AIMessage, BaseMessage,
                                                 HumanMessage, SystemMessage)
            from langchain_core.outputs import ChatGeneration, ChatResult
            
            class PortkeyLLM(BaseChatModel):
                def __init__(self, portkey_client, model_name="gemini-pro"):
                    # Initialize with keyword arguments for Pydantic
                    super().__init__(portkey_client=portkey_client, model_name=model_name)
                    
                @property
                def portkey_client(self):
                    return self.model_kwargs.get("portkey_client")
                    
                @property
                def model_name(self):
                    return self.model_kwargs.get("model_name", "gemini-pro")
                    
                def _generate(self, messages: List[BaseMessage], **kwargs) -> ChatResult:
                    raise NotImplementedError("PortkeyLLM is designed for async usage only")
                
                async def _agenerate(self, messages: List[BaseMessage], **kwargs) -> ChatResult:
                    # Convert LangChain messages to Portkey format
                    portkey_messages = []
                    for msg in messages:
                        if isinstance(msg, SystemMessage):
                            portkey_messages.append({"role": "system", "content": msg.content})
                        elif isinstance(msg, HumanMessage):
                            portkey_messages.append({"role": "user", "content": msg.content})
                        elif isinstance(msg, AIMessage):
                            portkey_messages.append({"role": "assistant", "content": msg.content})
                    
                    # Call Portkey API
                    try:
                        # Set a reasonable timeout for the API call
                        response = await self.portkey_client.chat.completions.create(
                            messages=portkey_messages,
                            model=self.model_name,
                            max_tokens=1000,
                            timeout=30.0,  # 30 second timeout
                            headers={
                                "X-Portkey-Mode": "gateway",
                                "X-Portkey-Trace-Id": "vibe-mapping-agent-trace"
                            }
                        )
                        
                        # Convert response to LangChain format
                        message = AIMessage(content=response.choices[0].message.content)
                        generation = ChatGeneration(message=message)
                        return ChatResult(generations=[generation])
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Error calling LLM via Portkey: {error_msg}")
                        
                        # Provide a more specific error message based on the type of error
                        if "Connection error" in error_msg:
                            fallback_content = "I'm having trouble connecting to the language model service. This could be due to network issues or API key configuration."
                        elif "timeout" in error_msg.lower():
                            fallback_content = "The request to the language model timed out. Please try again with a simpler query."
                        elif "api key" in error_msg.lower():
                            fallback_content = "There seems to be an issue with the API key configuration."
                        else:
                            fallback_content = "I'm having trouble processing that request. Could you try again?"
                        
                        # Return a fallback response
                        message = AIMessage(content=fallback_content)
                        generation = ChatGeneration(message=message)
                        return ChatResult(generations=[generation])
                
                @property
                def _llm_type(self) -> str:
                    return "portkey-llm"
            
            # Create the LLM instance
            llm = PortkeyLLM(self._portkey, settings.LLM_MODEL or "gemini-pro")
            
            # Store the LLM in the instance for future use
            self._llm = llm
        
        # Add nodes
        graph.add_node("process_initial_query", self.process_initial_query)
        graph.add_node("ask_follow_up", self.ask_follow_up)
        graph.add_node("process_follow_up", self.process_follow_up)
        graph.add_node("generate_recommendations", self.generate_recommendations)
        
        # Add START edge - this is required as the entry point to the graph
        graph.add_edge(START, "process_initial_query")
        
        # Add conditional edges using the router function
        graph.add_conditional_edges("process_initial_query", self.router)
        graph.add_conditional_edges("ask_follow_up", self.router)
        graph.add_conditional_edges("process_follow_up", self.router)
        
        # Add a direct edge from generate_recommendations to END
        graph.add_edge("generate_recommendations", END)
        
        # Compile the graph
        return graph.compile()
    
    async def process_chat_message(self, messages):
        """Process a chat message through the LangGraph workflow."""
        if not self._chat_graph:
            self.init()
        
        # Convert the messages to the format expected by the graph
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({"role": msg.role, "content": msg.content})
        
        # Initialize the state
        state = {
            "messages": formatted_messages,
            "current_step": "process_initial_query",
            "attributes": {},
            "recommendations": [],
            "follow_up_count": 0
        }
        
        # Run the graph
        try:
            final_state = await self._chat_graph.ainvoke(state)
            
            # Extract the last assistant message as the response
            assistant_messages = [msg for msg in final_state["messages"] if msg["role"] == "assistant"]
            response = assistant_messages[-1]["content"] if assistant_messages else "I'm not sure how to respond to that."
            
            return {
                "response": response,
                "recommendations": final_state.get("recommendations", [])
            }
        except Exception as e:
            logger.error(f"Error in chat graph: {str(e)}")
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "recommendations": []
            }
    
    async def process_chat_message_stream(self, messages) -> AsyncIterable[Dict[str, Any]]:
        """Process a chat message and stream the response chunks using LangGraph's astream."""
        from pydantic import BaseModel
        
        class StreamChunk(BaseModel):
            type: str  # 'content', 'recommendations', or 'error'
            data: Any
            done: bool = False
        
        if not self._chat_graph:
            self.init()
        
        # Convert the messages to the format expected by the graph
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({"role": msg.role, "content": msg.content})
        
        # Initialize the state
        state = {
            "messages": formatted_messages,
            "current_step": "process_initial_query",
            "attributes": {},
            "recommendations": [],
            "follow_up_count": 0
        }
        
        try:
            # Use LangGraph's native streaming functionality
            current_response = ""
            sent_recommendations = False
            
            # Stream each state update from the graph
            async for partial_state in self._chat_graph.astream(state):
                # Extract the latest assistant message if available
                assistant_messages = [msg for msg in partial_state["messages"] if msg["role"] == "assistant"]
                
                if assistant_messages:
                    latest_message = assistant_messages[-1]["content"]
                    
                    # If we have new content to stream
                    if len(latest_message) > len(current_response):
                        new_content = latest_message[len(current_response):]
                        current_response = latest_message
                        
                        # Stream the new content chunk
                        yield StreamChunk(
                            type="content",
                            data={"content": new_content},
                            done=False
                        )
                
                # If we have recommendations and haven't sent them yet
                if partial_state.get("recommendations") and not sent_recommendations:
                    recommendations = partial_state["recommendations"]
                    yield StreamChunk(
                        type="recommendations",
                        data={"recommendations": recommendations},
                        done=False
                    )
                    sent_recommendations = True
            
            # Signal completion after the graph is done
            yield StreamChunk(
                type="content",
                data={"content": ""},
                done=True
            )
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            yield StreamChunk(
                type="error",
                data={"message": f"Error: {str(e)}"},
                done=True
            )


# Singleton instance getter
_chat_service_instance = None

def get_chat_service():
    """Get the singleton instance of ChatService"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance

def init_chat_service():
    """Initialize the chat service"""
    service = get_chat_service()
    service.init()
    return service

def close_chat_service():
    """Close the chat service"""
    service = get_chat_service()
    service.close()
