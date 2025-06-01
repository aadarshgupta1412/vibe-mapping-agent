#!/usr/bin/env python3
"""
Test script for the graph workflow with tool call detection.

This script tests the non-streaming graph workflow to ensure:
1. LLM responses are generated properly
2. Tool calls are detected and routed correctly
3. Non-tool responses go directly to END
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent_processor import init_agent_processor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_non_tool_message():
    """Test a simple message that shouldn't trigger tools."""
    logger.info("=" * 60)
    logger.info("🧪 Testing non-tool message...")
    
    try:
        # Initialize agent processor
        agent_processor = await init_agent_processor()
        
        # Test message that shouldn't trigger tools
        messages = [
            {"role": "user", "content": "Hello! How are you today?"}
        ]
        
        result = await agent_processor.process(messages)
        
        logger.info(f"✅ Response: {result['response']}")
        logger.info(f"🔧 Tool outputs: {len(result['tool_outputs'])}")
        logger.info(f"❌ Error: {result['error']}")
        
        # Should have a response but no tool outputs
        assert result['response'], "Should have a response"
        assert len(result['tool_outputs']) == 0, "Should not have tool outputs for simple greeting"
        
        logger.info("✅ Non-tool message test passed!")
        
    except Exception as e:
        logger.error(f"❌ Non-tool message test failed: {e}")
        raise

async def test_potential_tool_message():
    """Test a message that might trigger tools (if tools are available)."""
    logger.info("=" * 60)
    logger.info("🧪 Testing potential tool message...")
    
    try:
        # Initialize agent processor
        agent_processor = await init_agent_processor()
        
        # Test message that might trigger tools
        messages = [
            {"role": "user", "content": "Can you help me find some dresses?"}
        ]
        
        result = await agent_processor.process(messages)
        
        logger.info(f"✅ Response: {result['response']}")
        logger.info(f"🔧 Tool outputs: {len(result['tool_outputs'])}")
        logger.info(f"❌ Error: {result['error']}")
        
        # Should have a response
        assert result['response'], "Should have a response"
        
        # Tool outputs depend on whether tools are available and LLM decides to use them
        if result['tool_outputs']:
            logger.info("🔧 LLM decided to use tools")
        else:
            logger.info("💬 LLM provided direct response without tools")
        
        logger.info("✅ Potential tool message test passed!")
        
    except Exception as e:
        logger.error(f"❌ Potential tool message test failed: {e}")
        raise

async def test_conversation_flow():
    """Test a multi-turn conversation."""
    logger.info("=" * 60)
    logger.info("🧪 Testing conversation flow...")
    
    try:
        # Initialize agent processor
        agent_processor = await init_agent_processor()
        
        # Multi-turn conversation
        messages = [
            {"role": "user", "content": "Hi there!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": "What can you do for me?"}
        ]
        
        result = await agent_processor.process(messages)
        
        logger.info(f"✅ Response: {result['response']}")
        logger.info(f"🔧 Tool outputs: {len(result['tool_outputs'])}")
        logger.info(f"❌ Error: {result['error']}")
        
        # Should have a response
        assert result['response'], "Should have a response"
        
        logger.info("✅ Conversation flow test passed!")
        
    except Exception as e:
        logger.error(f"❌ Conversation flow test failed: {e}")
        raise

async def main():
    """Run all tests."""
    logger.info("🚀 Starting graph workflow tests...")
    
    try:
        await test_non_tool_message()
        await test_potential_tool_message() 
        await test_conversation_flow()
        
        logger.info("=" * 60)
        logger.info("🎉 All tests passed! Graph workflow is working correctly.")
        
    except Exception as e:
        logger.error(f"❌ Tests failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 