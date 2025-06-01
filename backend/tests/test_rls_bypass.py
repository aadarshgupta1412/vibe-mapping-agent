#!/usr/bin/env python3
"""
Test script to verify that RLS is bypassed with service role key.

This script tests if we can see the actual data in the database
when using the service role key instead of anon key.
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_supabase_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_rls_bypass():
    """Test if service role key bypasses RLS and can see data"""
    logger.info("🔍 Testing RLS bypass with service role key...")
    
    try:
        # Initialize database
        db_manager = init_db()
        client = get_supabase_client()
        logger.info("✅ Database initialized")
        
        # Test 1: Get total count (this should work even with RLS)
        logger.info("📊 Testing total count...")
        count_response = client.table('apparels').select('*', count='exact').limit(1).execute()
        total_count = count_response.count if count_response.count is not None else 0
        logger.info(f"📊 Total count in database: {total_count}")
        
        # Test 2: Try to get actual data (this fails with anon key + RLS)
        logger.info("📝 Testing data retrieval...")
        data_response = client.table('apparels').select('*').limit(5).execute()
        
        if data_response.data:
            logger.info(f"✅ Successfully retrieved {len(data_response.data)} records!")
            
            # Show a sample of the data
            for i, record in enumerate(data_response.data[:3], 1):
                logger.info(f"   Record {i}: {record.get('name', 'N/A')} ({record.get('fabric', 'N/A')})")
            
            logger.info("🎉 SUCCESS: Service role key is working and bypassing RLS!")
            return True
            
        else:
            logger.warning("⚠️ No data retrieved - this suggests RLS is still blocking access")
            logger.warning("💡 Make sure you're using the SERVICE_ROLE key, not the anon key")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing RLS bypass: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rls_bypass())
    
    if success:
        print("\n🎉 RLS BYPASS SUCCESSFUL!")
        print("✅ Your tools should now work properly")
    else:
        print("\n❌ RLS BYPASS FAILED!")
        print("💡 Please check that you're using the service_role key in your .env file") 