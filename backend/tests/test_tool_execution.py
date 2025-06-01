#!/usr/bin/env python3
"""
Test script for tool execution with debug logging.
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent_processor import init_agent_processor

# Set up debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_tool_execution():
    """Test tool execution with debug logging."""
    logger.info("🧪 Testing tool execution with debug logging...")
    
    try:
        # Initialize agent processor
        agent_processor = await init_agent_processor()
        
        # Very specific request that should trigger the find_apparels tool
        messages = [
            {"role": "user", "content": "Find me a red dress"}
        ]
        
        result = await agent_processor.process(messages)
        
        logger.info(f"✅ Response: {result['response']}")
        logger.info(f"🔧 Tool outputs: {len(result['tool_outputs'])}")
        logger.info(f"❌ Error: {result['error']}")
        
        # Print tool outputs if any
        if result['tool_outputs']:
            for i, output in enumerate(result['tool_outputs']):
                logger.info(f"🔧 Tool {i+1}: {output['tool']} -> {str(output['result'])[:200]}...")
        
        logger.info("✅ Test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_tool_execution()) 