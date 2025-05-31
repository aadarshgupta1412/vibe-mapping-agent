#!/usr/bin/env python3
"""
Debug script to understand the tools structure.
"""

import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tools import get_tools_manager

def debug_tools():
    """Debug the tools structure to understand available methods."""
    print("🔍 Debugging tools structure...")
    
    # Initialize tools manager
    tools_manager = get_tools_manager()
    tools_manager.init()
    
    # Get tools
    tools = tools_manager.get_tools()
    
    print(f"📝 Found {len(tools)} tools")
    
    for i, tool in enumerate(tools):
        print(f"\n🔧 Tool {i+1}:")
        print(f"   Type: {type(tool)}")
        print(f"   Name: {getattr(tool, 'name', 'N/A')}")
        print(f"   Description: {getattr(tool, 'description', 'N/A')}")
        
        print("   Available methods:")
        for attr in dir(tool):
            if not attr.startswith('_'):
                attr_obj = getattr(tool, attr)
                if callable(attr_obj):
                    print(f"     - {attr}() [callable]")
                else:
                    print(f"     - {attr} [attribute]")
        
        # Test specific methods
        print("   Method availability:")
        print(f"     - invoke: {hasattr(tool, 'invoke')}")
        print(f"     - ainvoke: {hasattr(tool, 'ainvoke')}")
        print(f"     - run: {hasattr(tool, 'run')}")
        print(f"     - arun: {hasattr(tool, 'arun')}")
        print(f"     - __call__: {hasattr(tool, '__call__')}")
        
        # Check if it's a LangChain tool wrapper
        if hasattr(tool, 'func'):
            print(f"     - func: {getattr(tool, 'func', 'N/A')}")
            actual_func = getattr(tool, 'func', None)
            if actual_func:
                print(f"     - func callable: {callable(actual_func)}")
                print(f"     - func type: {type(actual_func)}")

if __name__ == "__main__":
    debug_tools() 