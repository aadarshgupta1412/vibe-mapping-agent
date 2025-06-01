#!/usr/bin/env python3
"""
Test script for tool calling functionality.

This script tests whether the LLM can successfully identify when to use tools
and execute them properly in the workflow.
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

async def test_specific_apparel_search():
    """Test a very specific request that should trigger tools."""
    logger.info("=" * 60)
    logger.info("🧪 Testing specific apparel search...")
    
    try:
        # Initialize agent processor
        agent_processor = await init_agent_processor()
        
        # Very specific request that should trigger the find_apparels tool
        messages = [
            {"role": "user", "content": "I need to find a red cotton dress in size M for a casual occasion. Can you search for this specific combination?"}
        ]
        
        result = await agent_processor.process(messages)
        
        logger.info(f"✅ Response: {result['response']}")
        logger.info(f"🔧 Tool outputs: {len(result['tool_outputs'])}")
        logger.info(f"❌ Error: {result['error']}")
        
        # Print tool outputs if any
        if result['tool_outputs']:
            for i, output in enumerate(result['tool_outputs']):
                logger.info(f"🔧 Tool {i+1}: {output['tool']} -> {str(output['result'])[:200]}...")
        
        # Should have a response
        assert result['response'], "Should have a response"
        
        logger.info("✅ Specific apparel search test completed!")
        
    except Exception as e:
        logger.error(f"❌ Specific apparel search test failed: {e}")
        raise

async def test_direct_tool_request():
    """Test requesting to use a specific tool directly."""
    logger.info("=" * 60)
    logger.info("🧪 Testing direct tool request...")
    
    try:
        # Initialize agent processor
        agent_processor = await init_agent_processor()
        
        # Direct request to use the tool
        messages = [
            {"role": "user", "content": "Please use the find_apparels function to search for dresses that are blue and suitable for formal occasions."}
        ]
        
        result = await agent_processor.process(messages)
        
        logger.info(f"✅ Response: {result['response']}")
        logger.info(f"🔧 Tool outputs: {len(result['tool_outputs'])}")
        logger.info(f"❌ Error: {result['error']}")
        
        # Print tool outputs if any
        if result['tool_outputs']:
            for i, output in enumerate(result['tool_outputs']):
                logger.info(f"🔧 Tool {i+1}: {output['tool']} -> {str(output['result'])[:200]}...")
        
        # Should have a response
        assert result['response'], "Should have a response"
        
        logger.info("✅ Direct tool request test completed!")
        
    except Exception as e:
        logger.error(f"❌ Direct tool request test failed: {e}")
        raise

async def test_apparel_details_lookup():
    """Test requesting details for a specific apparel item."""
    logger.info("=" * 60)
    logger.info("🧪 Testing apparel details lookup...")
    
    try:
        # Initialize agent processor
        agent_processor = await init_agent_processor()
        
        # Request details for a specific apparel ID
        messages = [
            {"role": "user", "content": "Can you get me details for apparel ID 'ap_001'? I want to know more about this specific item."}
        ]
        
        result = await agent_processor.process(messages)
        
        logger.info(f"✅ Response: {result['response']}")
        logger.info(f"🔧 Tool outputs: {len(result['tool_outputs'])}")
        logger.info(f"❌ Error: {result['error']}")
        
        # Print tool outputs if any
        if result['tool_outputs']:
            for i, output in enumerate(result['tool_outputs']):
                logger.info(f"🔧 Tool {i+1}: {output['tool']} -> {str(output['result'])[:200]}...")
        
        # Should have a response
        assert result['response'], "Should have a response"
        
        logger.info("✅ Apparel details lookup test completed!")
        
    except Exception as e:
        logger.error(f"❌ Apparel details lookup test failed: {e}")
        raise

async def main():
    """Run all tool calling tests."""
    logger.info("🚀 Starting tool calling tests...")
    
    try:
        await test_specific_apparel_search()
        await test_direct_tool_request()
        await test_apparel_details_lookup()
        
        logger.info("=" * 60)
        logger.info("🎉 All tool calling tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Tool calling tests failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 