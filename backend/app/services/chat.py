"""
Chat Service

This module implements the LangGraph conversation flow for the vibe mapping agent.
It integrates the vibe mapper and product service to handle the conversation flow.
"""

from typing import List, Dict, Any, TypedDict, Optional
from langchain_core.messages import HumanMessage, AIMessage
import json
import os

# Import our services
from .vibe_mapper import map_vibe_query
from .product_service import filter_products_by_attributes

# Try to import LangGraph, with fallback for development
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Mock implementation for development
    class StateGraph:
        def __init__(self, *args, **kwargs):
            pass
        
        def add_node(self, *args, **kwargs):
            pass
            
        def add_edge(self, *args, **kwargs):
            pass
            
        def compile(self, *args, **kwargs):
            pass
    
    END = "end"

# Try to import Gemini
try:
    import google.generativeai as genai
    
    # Configure Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Define our state type
class State(TypedDict):
    messages: List[Dict[str, str]]
    current_step: str
    attributes: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    follow_up_count: int

# Mock LLM function that will be replaced with actual LLM call
async def call_llm(messages, system_prompt=None):
    """
    Call the LLM with the given messages.
    
    In a real implementation, this would use the Gemini API.
    For now, we'll use a simple mock implementation.
    """
    if HAS_GEMINI and os.getenv("GEMINI_API_KEY"):
        try:
            # Convert messages to Gemini format
            gemini_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                gemini_messages.append({"role": "system", "parts": [system_prompt]})
            
            # Add conversation messages
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append({"role": role, "parts": [msg["content"]]})
            
            # Call Gemini API
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(gemini_messages)
            
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            # Fall back to mock implementation
    
    # Mock implementation
    last_message = messages[-1]["content"] if messages else ""
    
    # Simple mock response logic
    if "size" in last_message.lower() or "budget" in last_message.lower():
        return "Thanks for sharing that information. What kind of style or occasion are you looking for?"
    elif any(word in last_message.lower() for word in ["casual", "formal", "party", "work"]):
        return "Great! Based on your preferences, I'll find some recommendations that might work for you."
    else:
        return "Could you tell me more about what size you're looking for and your budget range?"

# Node functions for our graph
async def process_initial_query(state: State) -> State:
    """
    Process the initial user query and extract vibe terms.
    """
    messages = state["messages"]
    user_query = messages[-1]["content"] if messages[-1]["role"] == "user" else ""
    
    # Extract vibe terms and map to attributes
    vibe_result = map_vibe_query(user_query)
    
    # Store the attributes in the state
    state["attributes"] = vibe_result.get("attributes", {})
    
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
    
    response = await call_llm(messages, system_prompt)
    
    # Add AI response to messages
    state["messages"].append({"role": "assistant", "content": response})
    
    return state

async def ask_follow_up(state: State) -> State:
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
    
    response = await call_llm(messages, system_prompt)
    
    # Add AI response to messages
    state["messages"].append({"role": "assistant", "content": response})
    
    # Decide next step based on follow-up count
    if state["follow_up_count"] >= 2:
        state["current_step"] = "generate_recommendations"
    else:
        state["current_step"] = "process_follow_up"
    
    return state

async def process_follow_up(state: State) -> State:
    """
    Process the user's response to a follow-up question.
    """
    messages = state["messages"]
    user_query = messages[-1]["content"] if messages[-1]["role"] == "user" else ""
    
    # Extract vibe terms and map to attributes from the follow-up response
    vibe_result = map_vibe_query(user_query)
    
    # Merge with existing attributes
    for key, value in vibe_result.get("attributes", {}).items():
        if key in state["attributes"]:
            state["attributes"][key].extend(value)
            # Remove duplicates
            state["attributes"][key] = list(set(state["attributes"][key]))
        else:
            state["attributes"][key] = value
    
    # Decide if we need more follow-up questions
    if state["follow_up_count"] < 2 and len(state["attributes"]) < 3:
        state["current_step"] = "ask_follow_up"
    else:
        state["current_step"] = "generate_recommendations"
    
    return state

async def generate_recommendations(state: State) -> State:
    """
    Generate product recommendations based on attributes.
    """
    messages = state["messages"]
    attributes = state["attributes"]
    
    # Filter products based on attributes
    recommendations = filter_products_by_attributes(attributes, limit=3)
    
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
    
    response = await call_llm(messages, system_prompt)
    
    # Add AI response to messages
    state["messages"].append({"role": "assistant", "content": response})
    
    # End the conversation flow
    state["current_step"] = END
    
    return state

# Define the router function
def router(state: State) -> str:
    return state["current_step"]

# Create and configure the graph
def create_graph():
    """Create the LangGraph workflow."""
    # Initialize the graph
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("process_initial_query", process_initial_query)
    graph.add_node("ask_follow_up", ask_follow_up)
    graph.add_node("process_follow_up", process_follow_up)
    graph.add_node("generate_recommendations", generate_recommendations)
    
    # Add edges
    graph.add_edge("process_initial_query", router)
    graph.add_edge("ask_follow_up", router)
    graph.add_edge("process_follow_up", router)
    graph.add_edge("generate_recommendations", END)
    
    # Compile the graph
    return graph.compile()

# Initialize the graph
chat_graph = create_graph()

# Main function to process chat messages
async def process_chat_message(messages):
    """Process a chat message through the LangGraph workflow."""
    # Convert the messages to the format expected by the graph
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
    
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
        final_state = await chat_graph.ainvoke(state)
        
        # Extract the last assistant message as the response
        assistant_messages = [msg for msg in final_state["messages"] if msg["role"] == "assistant"]
        response = assistant_messages[-1]["content"] if assistant_messages else "I'm not sure how to respond to that."
        
        return {
            "response": response,
            "recommendations": final_state.get("recommendations", [])
        }
    except Exception as e:
        print(f"Error in chat graph: {str(e)}")
        return {
            "response": "I encountered an error processing your request. Please try again.",
            "recommendations": []
        }
