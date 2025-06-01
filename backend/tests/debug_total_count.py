#!/usr/bin/env python3
"""
Debug script to test the total count query used in tools.py
"""

import asyncio
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_supabase_client
from app.services.tools import init_tools_manager

def test_total_count_query():
    """Test the exact same query that tools.py uses"""
    print("🔍 Testing total count query...")
    
    try:
        # Test 1: Direct database client
        print("\n📊 Test 1: Direct database client")
        client = get_supabase_client()
        total_response = client.table('apparels').select('id', count='exact').execute()
        total_in_db = total_response.count if total_response.count else 0
        
        print(f"   Direct query result: {total_in_db}")
        print(f"   Response count attribute: {total_response.count}")
        print(f"   Response data length: {len(total_response.data)}")
        print(f"   Response type: {type(total_response)}")
        
        # Test 2: Through tools manager
        print("\n🔧 Test 2: Through tools manager")
        tools_manager = init_tools_manager()
        tools = tools_manager.get_tools()
        
        # Find the find_apparels tool
        find_apparels_tool = None
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == 'find_apparels':
                find_apparels_tool = tool
                break
        
        if find_apparels_tool:
            print("   Found find_apparels tool")
            
            # Execute with no filters to get all items
            result = find_apparels_tool.invoke({})
            print(f"   Tool result total_in_db: {result.get('total_in_db', 'NOT_FOUND')}")
            print(f"   Tool result count: {result.get('count', 'NOT_FOUND')}")
            print(f"   Tool result success: {result.get('success', 'NOT_FOUND')}")
            print(f"   Tool result message: {result.get('message', 'NOT_FOUND')}")
        else:
            print("   ❌ find_apparels tool not found")
        
        # Test 3: Different query variations
        print("\n📊 Test 3: Different query variations")
        
        # Test with limit 1
        response1 = client.table('apparels').select('*', count='exact').limit(1).execute()
        print(f"   With limit(1): count={response1.count}, data_len={len(response1.data)}")
        
        # Test without count
        response2 = client.table('apparels').select('*').limit(5).execute()
        print(f"   Without count: data_len={len(response2.data)}")
        
        # Test with just count
        response3 = client.table('apparels').select('*', count='exact').execute()
        print(f"   Full query: count={response3.count}, data_len={len(response3.data)}")
        
    except Exception as e:
        print(f"❌ Error testing total count: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_total_count_query() 