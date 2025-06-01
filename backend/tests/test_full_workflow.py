#!/usr/bin/env python3
"""
Test script to verify the full workflow works end-to-end.

This script tests the complete flow: user message -> LLM -> tool calling -> response
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

async def test_full_workflow():
    """Test the complete workflow with sample user queries"""
    logger.info("🚀 Testing full workflow...")
    
    try:
        # Initialize the agent processor
        agent_processor = await init_agent_processor()
        logger.info("✅ Agent processor initialized")
        
        # Test cases that should trigger tool calls
        test_cases = [
            {
                "name": "Cotton fabric search",
                "messages": [
                    {"role": "user", "content": "Find me cotton shirts"}
                ]
            },
            {
                "name": "Size-specific search", 
                "messages": [
                    {"role": "user", "content": "Show me size M clothing"}
                ]
            },
            {
                "name": "Complex search",
                "messages": [
                    {"role": "user", "content": "I need cotton shirts in size M for casual occasions under $50"}
                ]
            },
            {
                "name": "General clothing search",
                "messages": [
                    {"role": "user", "content": "What clothing do you have available?"}
                ]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n🧪 Test {i}: {test_case['name']}")
            logger.info(f"   User query: {test_case['messages'][0]['content']}")
            
            try:
                # Process the message through the agent
                result = await agent_processor.process(test_case['messages'])
                
                logger.info(f"   ✅ Success: {result.get('success', True)}")
                logger.info(f"   💬 Response: {result['response'][:200]}...")
                
                if result.get('tool_outputs'):
                    logger.info(f"   🔧 Tool outputs: {len(result['tool_outputs'])}")
                    for j, tool_output in enumerate(result['tool_outputs'], 1):
                        logger.info(f"      Tool {j}: {tool_output['tool']} -> {str(tool_output['result'])[:100]}...")
                
                if result.get('error'):
                    logger.warning(f"   ⚠️ Error: {result['error']}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error in test case: {e}")
        
        # Test a non-tool query
        logger.info(f"\n🧪 Test: Non-tool query")
        try:
            result = await agent_processor.process([
                {"role": "user", "content": "Hello, how are you today?"}
            ])
            
            logger.info(f"   ✅ Success: {result.get('success', True)}")
            logger.info(f"   💬 Response: {result['response']}")
            logger.info(f"   🔧 Tool outputs: {len(result.get('tool_outputs', []))}")
            
        except Exception as e:
            logger.error(f"   ❌ Error in non-tool test: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error in workflow test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_workflow()) 