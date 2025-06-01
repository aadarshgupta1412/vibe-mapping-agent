"""
Agent processor module for the Vibe Mapping Agent.

This module provides the implementation of the LangGraph workflow for processing
chat messages and generating responses.
"""

import logging
from typing import Any, Dict, List, Optional, AsyncIterable
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
import google.generativeai as genai

from app.core.config import settings
from app.models.agent_state import AgentState
from .tools import get_tools_manager, init_tools_manager

# Set up logger
logger = logging.getLogger(__name__)

# Import API keys from settings
GEMINI_API_KEY = settings.GEMINI_API_KEY
# PORTKEY_API_KEY = settings.PORTKEY_API_KEY  # Commented out to remove Portkey integration
# PORTKEY_VIRTUAL_KEY = settings.PORTKEY_VIRTUAL_KEY  # Commented out to remove Portkey integration
LLM_MODEL = settings.LLM_MODEL or "gemini-2.0-flash"

class AgentProcessor:
    """
    Processor for agent interactions using LangGraph.
    
    This class implements a graph-based workflow for processing chat messages,
    with nodes for agent reasoning, tool processing, and response generation.
    """
    
    def __init__(self):
        """Initialize the AgentProcessor."""
        self._llm = None
        self._graph = None
        self._tools_manager = None
    
    async def init(self):
        """Initialize the agent graph, LLM, and tools."""
        logger.info("🚀 Initializing AgentProcessor...")
        
        if self._graph:
            logger.info("✅ AgentProcessor already initialized, returning existing graph")
            return self._graph
        
        # Initialize the LLM
        logger.info("🤖 Initializing LLM...")
        await self._init_llm()
        
        # Initialize the tools manager
        logger.info("🔧 Initializing tools manager...")
        self._tools_manager = init_tools_manager()
        
        # Log available tools for debugging
        if self._tools_manager:
            available_tools = self._tools_manager.get_tools()
            logger.info(f"🛠️ Available tools after initialization: {len(available_tools)}")
            for i, tool in enumerate(available_tools):
                tool_name = getattr(tool, 'name', f'unknown_tool_{i}')
                tool_description = getattr(tool, 'description', 'No description')
                logger.info(f"  📋 Tool {i+1}: {tool_name} - {tool_description[:100]}...")
        else:
            logger.error("❌ Tools manager initialization failed!")
        
        # Create the agent graph
        logger.info("📊 Creating agent graph...")
        self._graph = self._create_graph()
        
        logger.info("✅ AgentProcessor initialization complete")
        return self._graph
        
    async def _init_llm(self):
        """Initialize the LLM for the agent processor."""
        logger.info("🤖 Starting LLM initialization...")
        
        try:
            # Configure Gemini API using the native google.generativeai library
            # to avoid compatibility issues with langchain's wrapper
            if GEMINI_API_KEY:
                logger.info(f"🔑 Configuring Gemini API with model: {LLM_MODEL}")
                
                # Configure the API key
                genai.configure(api_key=GEMINI_API_KEY)
                logger.debug("🔑 API key configured successfully")
                
                # Initialize the model
                self._llm = genai.GenerativeModel(
                    model_name=LLM_MODEL,
                    generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                        max_output_tokens=2048,  # Increased from 512 to handle tool responses
                    )
                )
                
                logger.info(f"✅ Successfully initialized native Gemini model {LLM_MODEL}")
            else:
                # No API keys available, log a warning
                logger.warning("⚠️ No API keys available for LLM. Using mock responses.")
                self._llm = None
                    
        except Exception as e:
            logger.error(f"❌ Error initializing LLM: {str(e)}")
            self._llm = None
        
    def close(self):
        """Close any resources."""
        logger.info("🔄 Closing AgentProcessor resources...")
        # Currently no resources to close
        logger.debug("ℹ️ No resources to clean up")
        logger.info("✅ AgentProcessor resources closed")
    
    async def agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main agent node that processes messages and decides whether to use tools or respond.
        
        This node handles the agent's reasoning and decision-making process.
        """
        logger.info("🧠 Entering agent_node...")
        
        # Convert AgentState to dict if needed
        if hasattr(state, 'model_dump'):
            state_dict = state.model_dump()
            logger.debug("📦 Converted AgentState to dict")
        else:
            state_dict = state
            logger.debug("📦 Using state as dict directly")
            
        messages = state_dict["messages"]
        tools = state_dict.get("tools", [])
        
        logger.info(f"📝 Processing {len(messages)} messages")
        logger.info(f"🔧 Available tools: {len(tools)}")
        
        if not self._llm:
            # Fallback if LLM not available
            logger.warning("⚠️ LLM not available, using fallback response")
            new_state = state_dict.copy()
            new_state["messages"].append({
                "role": "assistant", 
                "content": "I'm currently unavailable. Please try again later."
            })
            new_state["current_tool"] = None
            logger.info("🔙 Returning fallback state")
            return new_state
        
        try:
            logger.info("🔄 Converting messages to Google Gemini format...")
            
            # Convert messages to Google Gemini format
            gemini_messages = []
            system_instruction = """
                You are a fashion-savvy shopping assistant that helps customers find clothing based on their vibe descriptions.

                CONVERSATION FLOW:
                1. When a user asks for clothing with a vibe description (e.g., "something cute for brunch"), ask AT MOST 1-2 targeted follow-up questions to clarify their needs. 
                2. Focus follow-up questions on critical missing information like category, size, budget, or specific preferences.
                3. After 1-2 follow-ups, provide product recommendations with clear justification.
                4. NEVER ask more than 2 follow-up questions.

                RESPONSE FORMATTING:
                - Use clean, plain text without any formatting symbols like asterisks, bullets, or markdown
                - Separate different products with clear line breaks
                - Write in natural, conversational language
                - Keep responses organized but simple
                - If you receive a tool response with JSON format, use it to generate a list of products in a readable format
                - If you receive a tool response with a list of products, ALWAYS SHOW APPAREL ID to the user for each product
                - Start numbered lists with a new line and a number followed by a period

                ATTRIBUTE MAPPING:
                - Translate vibe terms like "casual," "elegant," or "cute" into structured attributes
                - Map seasonal terms to appropriate fabrics and styles
                - Infer preferences based on occasion mentions

                RECOMMENDATIONS:
                - Provide 3-5 specific product recommendations that match both explicit and inferred preferences
                - Include a brief justification explaining why these items match their vibe
                - Highlight key features that align with their request using plain text descriptions

                Remember to maintain a helpful, knowledgeable tone and focus on understanding the shopper's needs efficiently.
            """
            
            for i, msg in enumerate(messages):
                logger.debug(f"📄 Processing message {i+1}: role={msg['role']}")
                
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                    logger.debug("🎯 Found system instruction")
                elif msg["role"] == "user":
                    gemini_messages.append({
                        "role": "user",
                        "parts": [msg["content"]]
                    })
                    logger.debug(f"👤 Added user message: {msg['content'][:50]}...")
                elif msg["role"] == "assistant":
                    if not msg["content"]:
                        msg["content"] = "Let me help you with that."
                    gemini_messages.append({
                        "role": "model",
                        "parts": [msg["content"]]
                    })
                    logger.debug(f"🤖 Added assistant message: {msg['content'][:50]}...")
                elif msg["role"] == "tool":
                    # Convert tool messages to model messages to maintain conversation flow
                    tool_content = f"I used the {msg.get('name', 'tool')} and got: {msg['content']}"
                    gemini_messages.append({
                        "role": "model",
                        "parts": [tool_content]
                    })
                    logger.debug(f"🔧 Added tool result as model message: {tool_content[:50]}...")
                else:
                    logger.warning(f"⚠️ Unknown message role: {msg['role']}, skipping")
            
            # Prepare the prompt with system instruction if present
            if system_instruction and gemini_messages:
                logger.info("🎯 Prepending system instruction to first user message")
                if gemini_messages[0]["role"] == "user":
                    original_content = gemini_messages[0]["parts"][0]
                    gemini_messages[0]["parts"][0] = f"{system_instruction}\n\nUser: {original_content}"
                    logger.debug("✅ System instruction prepended successfully")
            
            # Prepare tools for Gemini function calling if available
            gemini_tools = []
            if tools:
                logger.info(f"🔧 Preparing {len(tools)} tools for Gemini function calling...")
                
                for i, tool in enumerate(tools):
                    logger.debug(f"🔧 Processing tool {i+1}: {type(tool)}")
                    
                    tool_name = None
                    tool_description = None
                    tool_parameters = {"type": "object", "properties": {}, "required": []}
                    
                    # Extract tool information
                    if hasattr(tool, 'name'):
                        tool_name = tool.name
                        tool_description = getattr(tool, 'description', f"Tool: {tool_name}")
                        logger.debug(f"🔧 Tool {i+1} name: {tool_name}")
                        logger.debug(f"🔧 Tool {i+1} description: {tool_description[:100]}...")
                        
                        # Try to get parameters from the tool's args_schema
                        if hasattr(tool, 'args_schema') and tool.args_schema:
                            try:
                                logger.debug(f"🔧 Extracting schema for tool: {tool_name}")
                                # Convert Pydantic schema to Gemini format
                                schema = tool.args_schema.model_json_schema()
                                logger.debug(f"🔧 Raw schema for {tool_name}: {json.dumps(schema, indent=2)}")
                                
                                # Ensure we have the right structure for Gemini
                                tool_parameters = {
                                    "type": "object",
                                    "properties": schema.get("properties", {}),
                                    "required": schema.get("required", [])
                                }
                                
                                # Clean up the properties to ensure they're Gemini-compatible
                                clean_properties = {}
                                for prop_name, prop_schema in tool_parameters["properties"].items():
                                    clean_prop = {}
                                    
                                    # Map types to Gemini-compatible types
                                    prop_type = prop_schema.get("type", "string")
                                    if prop_type == "integer":
                                        clean_prop["type"] = "integer"
                                    elif prop_type == "number":
                                        clean_prop["type"] = "number"
                                    elif prop_type == "boolean":
                                        clean_prop["type"] = "boolean"
                                    else:
                                        clean_prop["type"] = "string"
                                    
                                    # Add description if available
                                    if "description" in prop_schema:
                                        clean_prop["description"] = prop_schema["description"]
                                    
                                    # Add enum values if available
                                    if "enum" in prop_schema:
                                        clean_prop["enum"] = prop_schema["enum"]
                                    
                                    clean_properties[prop_name] = clean_prop
                                
                                tool_parameters["properties"] = clean_properties
                                logger.debug(f"🔧 Cleaned parameters for {tool_name}: {json.dumps(tool_parameters, indent=2)}")
                                
                            except Exception as e:
                                logger.warning(f"⚠️ Error extracting schema for tool {tool_name}: {e}")
                                # Use default empty object schema
                                tool_parameters = {"type": "object", "properties": {}, "required": []}
                        else:
                            logger.debug(f"🔧 No args_schema found for tool: {tool_name}")
                        
                    elif isinstance(tool, dict) and 'name' in tool:
                        tool_name = tool['name']
                        tool_description = tool.get('description', f"Tool: {tool_name}")
                        schema_params = tool.get('parameters', {})
                        if schema_params and isinstance(schema_params, dict):
                            tool_parameters = schema_params
                            # Ensure it has the required structure
                            if "type" not in tool_parameters:
                                tool_parameters["type"] = "object"
                            if "properties" not in tool_parameters:
                                tool_parameters["properties"] = {}
                            if "required" not in tool_parameters:
                                tool_parameters["required"] = []
                        logger.debug(f"🔧 Dict tool {tool_name} with parameters: {tool_parameters}")
                    
                    if tool_name:
                        gemini_tool = {
                            "function_declarations": [{
                                "name": tool_name,
                                "description": tool_description,
                                "parameters": tool_parameters
                            }]
                        }
                        gemini_tools.append(gemini_tool)
                        logger.info(f"✅ Added tool to Gemini: {tool_name}")
                        logger.debug(f"🔧 Full Gemini tool config: {json.dumps(gemini_tool, indent=2)}")
                    else:
                        logger.warning(f"⚠️ Skipping tool {i+1} - no name found")
                
                logger.info(f"✅ Prepared {len(gemini_tools)} tools for Gemini")
                
                # Log the final tools configuration for debugging
                if gemini_tools:
                    logger.debug("🔧 FINAL GEMINI TOOLS CONFIGURATION:")
                    for i, tool in enumerate(gemini_tools):
                        logger.debug(f"  Tool {i+1}: {json.dumps(tool, indent=2)}")
            else:
                logger.info("⚠️ No tools available for this request")
            
            # Generate LLM response with function calling capability
            logger.info("🤖 Generating LLM response with function calling...")
            
            try:
                # Generate response with tools if available
                if gemini_tools:
                    logger.info("🔧 Generating response with tools enabled")
                    response = await self._llm.generate_content_async(
                        gemini_messages,
                        tools=gemini_tools
                    )
                else:
                    logger.info("💬 Generating response without tools")
                    response = await self._llm.generate_content_async(gemini_messages)
                
                response_text = ""
                tool_calls = []
                
                logger.debug("📝 Extracting response text and tool calls...")
                
                # Extract response text and tool calls
                if response and hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    logger.debug(f"📝 Processing candidate with content: {hasattr(candidate, 'content')}")
                    
                    if hasattr(candidate, 'content') and candidate.content:
                        # Extract text content
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            logger.debug(f"📝 Found {len(candidate.content.parts)} content parts")
                            
                            for j, part in enumerate(candidate.content.parts):
                                logger.debug(f"📝 Processing part {j+1}: has_text={hasattr(part, 'text')}, has_function_call={hasattr(part, 'function_call')}")
                                
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                                    logger.debug(f"📝 Added text part {j+1}: {part.text[:50]}...")
                                
                                # Check for function calls
                                elif hasattr(part, 'function_call') and part.function_call:
                                    function_call = part.function_call
                                    logger.info(f"🔧 FOUND FUNCTION CALL: {function_call.name}")
                                    logger.debug(f"🔧 Function call args: {dict(function_call.args) if function_call.args else {}}")
                                    
                                    tool_call = {
                                        "name": function_call.name,
                                        "args": dict(function_call.args) if function_call.args else {},
                                        "id": f"tool_call_{len(tool_calls) + 1}",
                                        "type": "tool_call"
                                    }
                                    tool_calls.append(tool_call)
                                    logger.info(f"✅ Added tool call: {function_call.name} with args: {tool_call['args']}")
                                else:
                                    logger.debug(f"📝 Part {j+1} has no text or function_call content")
                        else:
                            logger.debug("📝 Candidate content has no parts")
                    else:
                        logger.debug("📝 Candidate has no content")
                else:
                    logger.debug("📝 Response has no candidates")
                
                # Log the extraction results
                logger.info(f"📝 Extracted response_text length: {len(response_text)}")
                logger.info(f"🔧 Extracted tool_calls count: {len(tool_calls)}")
                if response_text:
                    logger.debug(f"📝 Response text preview: {response_text[:200]}...")
                if tool_calls:
                    for i, tc in enumerate(tool_calls):
                        logger.info(f"🔧 Tool call {i+1}: {tc['name']} with {len(tc['args'])} arguments")
                
                # Fallback text extraction
                elif response and hasattr(response, 'text') and response.text:
                    response_text = response.text
                    logger.info(f"✅ Got response text: {response_text[:100]}...")
                
                if not response_text and not tool_calls:
                    logger.warning("⚠️ No response text or tool calls extracted, using fallback")
                    response_text = "I'm not sure how to respond to that."
                
                new_state = state_dict.copy()
                
                # Handle tool calls vs direct response
                if tool_calls:
                    logger.info(f"🔧 PROCESSING {len(tool_calls)} TOOL CALLS...")
                    
                    # Set the first tool call for execution
                    new_state["current_tool"] = tool_calls[0]
                    logger.info(f"🎯 Setting up execution for first tool: {tool_calls[0]['name']}")
                    logger.debug(f"🎯 Tool arguments: {tool_calls[0]['args']}")
                    
                    # Add assistant message with tool calls (only include response_text if it exists)
                    assistant_message = {
                        "role": "assistant",
                        "content": response_text,  # Use actual response_text, even if empty
                        "tool_calls": tool_calls
                    }
                    new_state["messages"].append(assistant_message)
                    logger.info(f"📝 Added assistant message with {len(tool_calls)} tool calls")
                    
                    logger.info(f"✅ TOOL EXECUTION SETUP COMPLETE: {tool_calls[0]['name']}")
                
                else:
                    logger.info("💬 NO TOOL CALLS FOUND - providing direct response...")
                    
                    # Log why no tool calls were found
                    if gemini_tools:
                        logger.warning(f"⚠️ Expected tool calls but found none. Tools were available: {[t['function_declarations'][0]['name'] for t in gemini_tools]}")
                        logger.debug(f"📝 Response object type: {type(response)}")
                        logger.debug(f"📝 Response has candidates: {hasattr(response, 'candidates') and bool(response.candidates)}")
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            logger.debug(f"📝 Candidate has content: {hasattr(candidate, 'content')}")
                            if hasattr(candidate, 'content') and candidate.content:
                                logger.debug(f"📝 Content has parts: {hasattr(candidate.content, 'parts') and bool(candidate.content.parts)}")
                    
                    # Direct response without tools
                    new_state["messages"].append({
                        "role": "assistant",
                        "content": response_text
                    })
                    new_state["current_tool"] = None
                    
                    logger.info(f"💬 Added direct response: {response_text[:50]}...")
                
            except Exception as e:
                logger.warning(f"⚠️ Error generating content: {e}")
                logger.error(f"🔍 Detailed error info: {type(e).__name__}: {str(e)}")
                logger.error(f"📝 Messages count: {len(gemini_messages)}")
                logger.error(f"🔧 Tools count: {len(gemini_tools)}")
                # Log the last few messages for debugging
                if gemini_messages:
                    for i, msg in enumerate(gemini_messages[-3:]):  # Last 3 messages
                        logger.error(f"📄 Message {i}: role={msg.get('role', 'unknown')}, content_length={len(str(msg.get('parts', [])))})")
                
                response_text = "I encountered an error generating a response. Please try again."
                
                new_state = state_dict.copy()
                new_state["messages"].append({
                    "role": "assistant",
                    "content": response_text
                })
                new_state["current_tool"] = None
            
            logger.info("✅ Agent node completed successfully")
            return new_state
            
        except Exception as e:
            logger.error(f"❌ Error in agent node: {str(e)}")
            new_state = state_dict.copy()
            new_state["error"] = str(e)
            new_state["messages"].append({
                "role": "assistant",
                "content": "I encountered an error processing your request. Please try again."
            })
            new_state["current_tool"] = None
            logger.info("🔙 Returning error state")
        return new_state
    
    async def tool_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool based on the current_tool in the state.
        
        This node handles the execution of tools and manages the results.
        """
        logger.info("🔧 Entering tool_node...")
        
        # Convert AgentState to dict if needed
        if hasattr(state, 'model_dump'):
            state_dict = state.model_dump()
            logger.debug("📦 Converted AgentState to dict in tool_node")
        else:
            state_dict = state
            logger.debug("📦 Using state as dict directly in tool_node")
        
        current_tool = state_dict.get("current_tool")
        logger.info(f"🔧 Current tool to execute: {current_tool}")
        
        if not current_tool:
            logger.warning("⚠️ No current tool to execute")
            new_state = state_dict.copy()
            new_state["error"] = "No tool specified for execution"
            logger.debug("❌ Returning state with error: No tool specified")
            return new_state
        
        # Get the original tools from the tools manager (not the serialized ones from state)
        original_tools = self._tools_manager.get_tools() if self._tools_manager else []
        logger.info(f"🔧 Available tools count: {len(original_tools)}")
        
        # Find the matching tool by name
        tool_name = current_tool.get("name")
        logger.info(f"🔍 Finding tool to execute: {tool_name}")
        
        tool_to_execute = None
        for tool in original_tools:
            if hasattr(tool, 'name') and tool.name == tool_name:
                tool_to_execute = tool
                logger.info(f"✅ Found matching tool: {tool_name}")
                break
            elif isinstance(tool, dict) and tool.get('name') == tool_name:
                tool_to_execute = tool
                logger.debug(f"🔧 Tool {tool_name} (dict with name key)")
                break
        
        if not tool_to_execute:
            logger.error(f"❌ Tool {tool_name} not found in available tools")
            new_state = state_dict.copy()
            new_state["error"] = f"Tool {tool_name} not found"
            new_state["current_tool"] = None
            logger.debug(f"❌ Returning state with error: Tool {tool_name} not found")
            return new_state
        
        try:
            # Execute the tool
            logger.info(f"🔄 Executing tool: {current_tool['name']} with args: {current_tool['args']}")
            
            # Add debug logging for method availability
            logger.debug(f"🔧 Tool type: {type(tool_to_execute)}")
            logger.debug(f"🔧 Has invoke: {hasattr(tool_to_execute, 'invoke')}")
            logger.debug(f"🔧 Has ainvoke: {hasattr(tool_to_execute, 'ainvoke')}")
            logger.debug(f"🔧 Has run: {hasattr(tool_to_execute, 'run')}")
            logger.debug(f"🔧 Has arun: {hasattr(tool_to_execute, 'arun')}")
            logger.debug(f"🔧 Is callable: {callable(tool_to_execute)}")
            
            # Execute the tool
            if hasattr(tool_to_execute, 'ainvoke'):
                logger.debug("🔄 Using ainvoke method")
                tool_result = await tool_to_execute.ainvoke(current_tool["args"])
            elif hasattr(tool_to_execute, 'invoke'):
                logger.debug("🔄 Using invoke method")
                tool_result = tool_to_execute.invoke(current_tool["args"])
            elif hasattr(tool_to_execute, 'arun'):
                logger.debug("🔄 Using arun method (LangChain async)")
                tool_result = await tool_to_execute.arun(**current_tool["args"])
            elif hasattr(tool_to_execute, 'run'):
                logger.debug("🔄 Using run method (LangChain sync)")
                tool_result = tool_to_execute.run(**current_tool["args"])
            elif callable(tool_to_execute):
                logger.debug("🔄 Using direct call method")
                tool_result = tool_to_execute(**current_tool["args"])
            else:
                logger.error(f"❌ Tool {current_tool['name']} cannot be executed (no invoke methods)")
                tool_result = f"Tool {current_tool['name']} cannot be executed"
            
            logger.info(f"✅ Tool execution completed. Result length: {len(str(tool_result))}")
            
        except Exception as e:
            logger.error(f"❌ Error executing tool {current_tool['name']}: {str(e)}")
            tool_result = f"Error executing tool: {str(e)}"
        
        # Create tool output entry
        tool_output = {
            "tool": current_tool["name"],
            "args": current_tool["args"],
            "result": tool_result
        }
        
        # Update state with tool result
        new_state = state_dict.copy()
        new_state["last_tool_outputs"] = new_state.get("last_tool_outputs", [])
        new_state["last_tool_outputs"].append(tool_output)
        
        logger.info(f"📝 Added tool output to state. Total outputs: {len(new_state['last_tool_outputs'])}")
        
        # Add the tool result as a tool message to conversation
        tool_message = {
            "role": "tool",
            "name": current_tool["name"],
            "content": str(tool_result),
            "tool_call_id": current_tool.get("id", "")
        }
        
        new_state["messages"].append(tool_message)
        logger.info("📝 Added tool result message to conversation")
        
        # Clear the current tool
        new_state["current_tool"] = None
        logger.info("🧹 Cleared current_tool from state")
        
        logger.info("✅ Tool node completed successfully")
        return new_state
    
    def should_continue(self, state: Dict[str, Any]) -> str:
        """
        Router function that determines the next step in the workflow.
        
        Returns the name of the next node or END to finish.
        """
        logger.info("🤔 Determining next step in workflow...")
        
        # Convert AgentState to dict if needed
        if hasattr(state, 'model_dump'):
            state_dict = state.model_dump()
            logger.debug("📦 Converted AgentState to dict in should_continue")
        else:
            state_dict = state
            logger.debug("📦 Using state as dict directly in should_continue")
            
        current_tool = state_dict.get("current_tool")
        error = state_dict.get("error")
        last_tool_outputs = state_dict.get("last_tool_outputs", [])
        
        logger.info(f"🔧 Current tool: {current_tool}")
        logger.info(f"❌ Error present: {bool(error)}")
        logger.info(f"🔧 Tool outputs count: {len(last_tool_outputs)}")
        
        # If there's an error, end the conversation
        if error:
            logger.info("❌ Error detected, ending workflow")
            return END
        
        # If there's a tool to execute and we haven't executed many tools yet, go to tool node
        if current_tool and len(last_tool_outputs) < 3:  # Limit to 3 tool executions max
            logger.info(f"🔧 Tool execution needed: {current_tool['name']} (execution #{len(last_tool_outputs) + 1})")
            return "tool_node"
        elif current_tool and len(last_tool_outputs) >= 3:
            logger.warning("⚠️ Maximum tool executions reached (3), ending workflow")
        
        # Otherwise, end the conversation
        logger.info("🏁 Ending workflow")
        return END
    
    def _create_graph(self) -> StateGraph:
        """
        Create the LangGraph workflow for agent processing.
        
        This function defines the nodes and edges of the graph that
        processes chat messages and generates responses.
        """
        logger.info("📊 Creating LangGraph workflow...")
        
        # Create a new graph with AgentState
        graph = StateGraph(AgentState)
        logger.debug("📊 StateGraph created with AgentState")
        
        # Add nodes
        logger.info("🔗 Adding nodes to graph...")
        graph.add_node("agent_node", self.agent_node)
        logger.debug("🧠 Added agent_node")
        
        graph.add_node("tool_node", self.tool_node)
        logger.debug("🔧 Added tool_node")
        
        # Set entry point
        logger.info("🚪 Setting entry point to agent_node")
        graph.set_entry_point("agent_node")
        
        # Add conditional routing from agent
        logger.info("🔗 Adding conditional edges...")
        graph.add_conditional_edges(
            "agent_node",
            self.should_continue,
            {
                "tool_node": "tool_node",
                END: END
            }
        )
        logger.debug("🔀 Conditional edges added from agent_node")
        
        # After tool execution, go back to agent
        logger.info("🔗 Adding edge from tool_node to agent_node")
        graph.add_edge("tool_node", "agent_node")
        
        # Compile the graph
        logger.info("⚙️ Compiling graph...")
        compiled_graph = graph.compile()
        logger.info("✅ Graph compilation completed")
        
        return compiled_graph
    
    async def process(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Process messages through the agent graph.
        
        This method initializes the state with the provided messages and
        runs the graph to generate a response.
        """
        logger.info("🚀 Starting message processing...")
        logger.info(f"📝 Processing {len(messages)} messages")
        
        if not self._graph:
            logger.info("📊 Graph not initialized, initializing now...")
            await self.init()
        
        # Initialize the state using the AgentState model (non-streaming by default)
        logger.info("🏗️ Initializing agent state...")
        initial_state = AgentState(
            messages=messages,
            tools=self._tools_manager.get_tools() if self._tools_manager else [],
            last_tool_outputs=[],
            current_tool=None,
            error=None,
            streaming=False  # Disable streaming for normal processing
        )
        
        tools_count = len(initial_state.tools)
        logger.info(f"🔧 Available tools in state: {tools_count}")
        
        # Run the graph
        try:
            logger.info("🔄 Running agent graph...")
            final_state = await self._graph.ainvoke(initial_state.model_dump())
            logger.info("✅ Graph execution completed")
            
            # Extract the last assistant message as the response
            logger.info("📝 Extracting response from final state...")
            assistant_messages = [msg for msg in final_state["messages"] if msg["role"] == "assistant"]
            response = assistant_messages[-1]["content"] if assistant_messages else "I'm not sure how to respond to that."
            
            logger.info(f"💬 Response extracted: {response[:100]}...")
            logger.info(f"🔧 Tool outputs count: {len(final_state.get('last_tool_outputs', []))}")
            
            result = {
                "response": response,
                "tool_outputs": final_state.get("last_tool_outputs", []),
                "error": final_state.get("error")
            }
            
            logger.info("✅ Process completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in agent graph: {str(e)}")
            error_result = {
                "response": "I encountered an error processing your request. Please try again.",
                "tool_outputs": [],
                "error": str(e)
            }
            
            logger.info("🔙 Returning error result")
            return error_result
    
    async def process_stream(self, messages: List[Dict[str, str]]) -> AsyncIterable[Dict[str, Any]]:
        """
        Process messages through the agent graph with streaming.
        
        This method initializes the state with the provided messages and
        streams the response through the graph workflow.
        """
        logger.info("🌊 Starting streaming message processing...")
        logger.info(f"📝 Processing {len(messages)} messages in streaming mode")
        
        if not self._graph:
            logger.info("📊 Graph not initialized, initializing now...")
            await self.init()
        
        try:
            # Always use the graph workflow for streaming
            logger.info("🌊 Using LangGraph workflow for streaming...")
            
            initial_state = AgentState(
            messages=messages,
            tools=self._tools_manager.get_tools() if self._tools_manager else [],
            last_tool_outputs=[],
            current_tool=None,
                error=None,
                streaming=True  # Mark as streaming mode
            )
            
            logger.info(f"🔧 Available tools for workflow: {len(initial_state.tools)}")
            logger.info("🌊 Starting graph streaming...")
            
            async for chunk in self._graph.astream(initial_state.model_dump()):
                node_name = list(chunk.keys())[0] if chunk else None
                node_state = list(chunk.values())[0] if chunk else {}
                
                logger.debug(f"📦 Received chunk from node: {node_name}")
                
                if node_name and node_state:
                    messages = node_state.get("messages", [])
                    
                    # Check if we need to stream LLM response directly
                    if node_state.get("needs_streaming_response") and node_state.get("streaming_messages"):
                        logger.info("🌊 Streaming LLM response directly...")
                        
                        try:
                            response_stream = self._llm.generate_content(
                                node_state["streaming_messages"], 
                                stream=True
                            )
                            
                            accumulated_text = ""
                            chunk_count = 0
                            
                            for chunk_response in response_stream:
                                chunk_count += 1
                                
                                if chunk_response and hasattr(chunk_response, 'text') and chunk_response.text:
                                    chunk_text = chunk_response.text
                                    accumulated_text += chunk_text
                                    
                                    logger.debug(f"🌊 Chunk {chunk_count}: '{chunk_text[:30]}...' (length: {len(chunk_text)})")
                                    
                                    # Yield the streaming chunk
                                    yield {
                                        "type": "message_chunk",
                                        "data": {
                                            "content": chunk_text,
                                            "accumulated_content": accumulated_text,
                                            "role": "assistant"
                                        },
                                        "node": "agent_node"
                                    }
                            
                            logger.info(f"✅ Streaming completed. Total chunks: {chunk_count}, Final length: {len(accumulated_text)}")
                            
                            # Yield the complete message
                            yield {
                                "type": "message_complete",
                                "data": {
                                    "content": accumulated_text,
                                    "role": "assistant"
                                },
                                "node": "agent_node"
                            }
                            
                        except Exception as e:
                            logger.error(f"❌ Error in streaming LLM response: {e}")
                            yield {
                                "type": "error",
                                "data": {"error": str(e)},
                                "node": "agent_node"
                            }
                    
                    # Handle regular messages from the workflow
                    elif messages:
                        latest_message = messages[-1]
                        
                        if latest_message.get("role") == "assistant" and latest_message.get("content") and not latest_message.get("streaming"):
                            logger.info(f"💬 Assistant message from {node_name}: {latest_message['content'][:50]}...")
                            yield {
                                "type": "message",
                                "data": {
                                    "content": latest_message["content"],
                                    "role": "assistant"
                                },
                                "node": node_name
                            }
                        
                        elif latest_message.get("role") == "tool":
                            logger.info(f"🔧 Tool output from {node_name}: {latest_message['content'][:50]}...")
                            yield {
                                "type": "tool_output",
                                "data": {
                                    "content": latest_message["content"],
                                    "tool_call_id": latest_message.get("tool_call_id", "")
                                },
                                "node": node_name
                            }
                    
                    if node_state.get("error"):
                        logger.error(f"❌ Error in node {node_name}: {node_state['error']}")
                        yield {
                            "type": "error",
                            "data": {"error": node_state["error"]},
                            "node": node_name
                        }
            
            # Signal completion
            logger.info("🏁 Streaming process completed")
            yield {
                "type": "completion",
                "data": {},
                "node": "end"
            }
            
        except Exception as e:
            logger.error(f"❌ Error in streaming agent: {str(e)}")
            yield {
                "type": "error",
                "data": {"error": str(e)},
                "node": "error"
            }


# Singleton instance getter
_agent_processor_instance = None

def get_agent_processor():
    """Get the singleton instance of AgentProcessor"""
    global _agent_processor_instance
    if _agent_processor_instance is None:
        logger.info("🏗️ Creating new AgentProcessor singleton instance")
        _agent_processor_instance = AgentProcessor()
    else:
        logger.debug("♻️ Returning existing AgentProcessor singleton instance")
    return _agent_processor_instance

async def init_agent_processor():
    """Initialize the agent processor"""
    logger.info("🚀 Initializing agent processor...")
    processor = get_agent_processor()
    await processor.init()
    logger.info("✅ Agent processor initialization completed")
    return processor

def close_agent_processor():
    """Close the agent processor"""
    logger.info("🔄 Closing agent processor...")
    processor = get_agent_processor()
    processor.close()
    logger.info("✅ Agent processor closed successfully")
