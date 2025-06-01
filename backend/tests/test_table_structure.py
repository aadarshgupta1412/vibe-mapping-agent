#!/usr/bin/env python3
"""
Test script to check database table structure and data.

This script investigates the Supabase database to understand the table structure and available data.
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, check_connection, get_supabase_client
from app.core.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def investigate_database():
    """Investigate the database structure and data"""
    logger.info("🔍 Investigating database structure...")
    
    try:
        # Initialize database
        logger.info("🚀 Initializing database...")
        db_manager = init_db()
        
        # Get client
        client = get_supabase_client()
        logger.info("✅ Got Supabase client")
        
        # Test connection
        connection_ok = await check_connection()
        if not connection_ok:
            logger.error("❌ Database connection failed")
            return
        
        logger.info("✅ Database connection verified")
        
        # Try different possible table names
        possible_tables = ['apparels', 'apparel', 'clothing', 'items', 'products']
        
        for table_name in possible_tables:
            logger.info(f"🔍 Checking table: {table_name}")
            
            try:
                # Try to get count
                count_response = client.table(table_name).select('*', count='exact').limit(1).execute()
                total_count = count_response.count if count_response.count is not None else 0
                
                logger.info(f"✅ Table '{table_name}' exists! Total rows: {total_count}")
                
                if total_count > 0:
                    # Get a few sample records
                    sample_response = client.table(table_name).select('*').limit(3).execute()
                    
                    if sample_response.data:
                        logger.info(f"📊 Sample data from '{table_name}':")
                        for i, record in enumerate(sample_response.data, 1):
                            logger.info(f"   Record {i}: {record}")
                            
                        # Show column structure
                        if sample_response.data:
                            columns = list(sample_response.data[0].keys())
                            logger.info(f"📋 Columns in '{table_name}': {columns}")
                    
                    # If this is the apparels table, let's check for specific data
                    if table_name == 'apparels':
                        logger.info("🔍 Checking for specific fabric and size data...")
                        
                        # Check for cotton fabric
                        cotton_response = client.table(table_name).select('*').ilike('fabric', '%cotton%').limit(3).execute()
                        logger.info(f"🧵 Records with cotton fabric: {len(cotton_response.data) if cotton_response.data else 0}")
                        if cotton_response.data:
                            for record in cotton_response.data:
                                logger.info(f"   Cotton item: {record.get('name', 'N/A')} - Fabric: {record.get('fabric', 'N/A')}")
                        
                        # Check for size M
                        size_m_response = client.table(table_name).select('*').eq('size', 'M').limit(3).execute()
                        logger.info(f"👕 Records with size M: {len(size_m_response.data) if size_m_response.data else 0}")
                        if size_m_response.data:
                            for record in size_m_response.data:
                                logger.info(f"   Size M item: {record.get('name', 'N/A')} - Size: {record.get('size', 'N/A')}")
                        
                        # Check what sizes are available
                        all_sizes_response = client.table(table_name).select('size').execute()
                        if all_sizes_response.data:
                            unique_sizes = set(record.get('size') for record in all_sizes_response.data if record.get('size'))
                            logger.info(f"📏 Available sizes: {sorted(unique_sizes)}")
                        
                        # Check what fabrics are available
                        all_fabrics_response = client.table(table_name).select('fabric').execute()
                        if all_fabrics_response.data:
                            unique_fabrics = set(record.get('fabric') for record in all_fabrics_response.data if record.get('fabric'))
                            logger.info(f"🧵 Available fabrics: {sorted(unique_fabrics)}")
                
                else:
                    logger.info(f"⚠️ Table '{table_name}' is empty")
                    
            except Exception as e:
                logger.warning(f"❌ Table '{table_name}' doesn't exist or error: {e}")
        
        # Test the exact query that's failing in the tool
        logger.info("🔧 Testing the exact problematic query...")
        try:
            # This is the exact query from the tool
            total_response = client.table('apparels').select('id', count='exact').execute()
            total_count = total_response.count if total_response.count is not None else 0
            logger.info(f"📊 Total count query result: {total_count}")
            logger.info(f"📊 Response object: {total_response}")
            logger.info(f"📊 Response data: {total_response.data}")
            
        except Exception as e:
            logger.error(f"❌ Total count query failed: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error investigating database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_database()) 