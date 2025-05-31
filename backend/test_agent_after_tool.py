#!/usr/bin/env python3
"""
Test script to debug agent response generation after tool execution.

This script simulates the exact state after a tool call to see why
the agent fails to generate a response.
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent_processor import init_agent_processor
from app.models.agent_state import AgentState

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_agent_after_tool():
    """Test agent response generation after tool execution"""
    logger.info("🧪 Testing agent response after tool execution...")
    
    # Initialize the agent processor
    agent_processor = await init_agent_processor()
    
    # Simulate the conversation state AFTER a tool has been executed
    messages_after_tool = [
        {
            "role": "user",
            "content": "Find me cotton casual wear in size M"
        },
        {
            "role": "assistant", 
            "content": "",
            "tool_calls": [{
                "name": "find_apparels",
                "args": {"fabric": "cotton", "occasion": "casual", "size": "M"},
                "id": "tool_call_1",
                "type": "tool_call"
            }]
        },
        {
            "role": "tool",
            "name": "find_apparels", 
            "content": "{'success': True, 'apparels': [], 'count': 0, 'total_in_db': 70, 'message': 'No apparels found matching your criteria', 'filters_applied': {'fabric': 'cotton', 'occasion': 'casual', 'size': 'M'}, 'suggestions': ['Try different sizes like XXS, XS, S, M, L']}",
            "tool_call_id": "tool_call_1"
        }
    ]
    
    logger.info("📝 Simulated conversation state after tool execution:")
    for i, msg in enumerate(messages_after_tool):
        logger.info(f"  {i+1}. {msg['role']}: {msg.get('content', 'N/A')[:100]}...")
    
    # Create state that simulates being after tool execution
    state = {
        "messages": messages_after_tool,
        "tools": [],
        "last_tool_outputs": [{
            "tool": "find_apparels",
            "args": {"fabric": "cotton", "occasion": "casual", "size": "M"},
            "result": "{'success': True, 'apparels': [], 'count': 0, 'total_in_db': 70, 'message': 'No apparels found matching your criteria', 'filters_applied': {'fabric': 'cotton', 'occasion': 'casual', 'size': 'M'}, 'suggestions': ['Try different sizes like XXS, XS, S, M, L']}"
        }],
        "current_tool": None,
        "error": None,
        "streaming": False
    }
    
    logger.info("🧠 Testing agent_node with post-tool state...")
    
    try:
        # Call agent_node directly with the post-tool state
        result = await agent_processor.agent_node(state)
        
        logger.info("✅ Agent node completed successfully!")
        logger.info(f"📝 Final messages count: {len(result['messages'])}")
        
        # Check the last message
        if result['messages']:
            last_msg = result['messages'][-1]
            logger.info(f"🤖 Last message role: {last_msg.get('role')}")
            logger.info(f"💬 Last message content: {last_msg.get('content', 'N/A')[:200]}...")
        
        if result.get('error'):
            logger.error(f"❌ Error in result: {result['error']}")
            
    except Exception as e:
        logger.error(f"❌ Exception in agent_node: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_after_tool()) 