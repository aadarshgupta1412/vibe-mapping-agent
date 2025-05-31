#!/usr/bin/env python3
"""
Test script to verify tools work with the correct schema.

This script tests the find_apparels tool with various filters to ensure
it works correctly with the available_sizes array field.
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tools import init_tools_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_tools():
    """Test the tools with various filter combinations"""
    logger.info("🔧 Testing tools with various filters...")
    
    try:
        # Initialize tools manager
        tools_manager = init_tools_manager()
        tools = tools_manager.get_tools()
        
        # Find the find_apparels tool
        find_apparels_tool = None
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == 'find_apparels':
                find_apparels_tool = tool
                break
        
        if not find_apparels_tool:
            logger.error("❌ find_apparels tool not found")
            return
        
        logger.info("✅ Found find_apparels tool")
        
        # Test cases
        test_cases = [
            {
                "name": "No filters (get all)",
                "args": {}
            },
            {
                "name": "Cotton fabric filter",
                "args": {"fabric": "cotton"}
            },
            {
                "name": "Size M filter", 
                "args": {"size": "M"}
            },
            {
                "name": "Cotton fabric + Size M",
                "args": {"fabric": "cotton", "size": "M"}
            },
            {
                "name": "Casual occasion",
                "args": {"occasion": "casual"}
            },
            {
                "name": "Price range",
                "args": {"min_price": 20, "max_price": 60}
            },
            {
                "name": "Complex filter",
                "args": {
                    "fabric": "cotton",
                    "size": "M", 
                    "occasion": "casual",
                    "max_price": 50
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n🧪 Test {i}: {test_case['name']}")
            logger.info(f"   Args: {test_case['args']}")
            
            try:
                result = find_apparels_tool.invoke(test_case['args'])
                
                logger.info(f"   ✅ Success: {result['success']}")
                logger.info(f"   📊 Count: {result['count']}")
                logger.info(f"   📊 Total in DB: {result['total_in_db']}")
                logger.info(f"   💬 Message: {result['message']}")
                
                if result['filters_applied']:
                    logger.info(f"   🔍 Filters applied: {result['filters_applied']}")
                
                if result['apparels']:
                    logger.info(f"   👕 Sample items:")
                    for item in result['apparels'][:2]:  # Show first 2 items
                        sizes = item.get('available_sizes', [])
                        logger.info(f"      - {item['name']} (sizes: {sizes}, fabric: {item.get('fabric', 'N/A')})")
                
                if result['suggestions']:
                    logger.info(f"   💡 Suggestions: {result['suggestions']}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
        
        # Test get_apparel_details tool
        logger.info(f"\n🧪 Testing get_apparel_details tool...")
        
        get_details_tool = None
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == 'get_apparel_details':
                get_details_tool = tool
                break
        
        if get_details_tool:
            try:
                result = get_details_tool.invoke({"apparel_id": "D001"})
                logger.info(f"   ✅ Success: {result['success']}")
                logger.info(f"   💬 Message: {result['message']}")
                
                if result['apparel']:
                    item = result['apparel']
                    logger.info(f"   👕 Item: {item['name']}")
                    logger.info(f"   📏 Available sizes: {item.get('available_sizes', [])}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tools()) 