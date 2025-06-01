#!/usr/bin/env python3
"""
Script to add sample apparel data to the database.

This script populates the apparels table with sample data for testing the tools.
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

# Sample apparel data
SAMPLE_APPARELS = [
    {
        "id": "D001",
        "name": "Classic Cotton T-Shirt",
        "category": "top",
        "fabric": "cotton",
        "color_or_print": "white",
        "available_sizes": ["S", "M", "L", "XL"],
        "fit": "regular",
        "occasion": "casual",
        "sleeve_length": "short",
        "neckline": "crew",
        "price": 25
    },
    {
        "id": "D002", 
        "name": "Cotton Casual Shirt",
        "category": "top",
        "fabric": "cotton",
        "color_or_print": "blue",
        "available_sizes": ["M", "L", "XL"],
        "fit": "slim",
        "occasion": "casual",
        "sleeve_length": "long",
        "neckline": "button-down",
        "price": 45
    },
    {
        "id": "D003",
        "name": "Cotton Blend Jeans",
        "category": "bottom",
        "fabric": "cotton",
        "color_or_print": "blue",
        "available_sizes": ["XS", "S", "M", "L"],
        "fit": "regular",
        "occasion": "casual",
        "pant_type": "jeans",
        "length": "full",
        "price": 65
    },
    {
        "id": "D004",
        "name": "Formal Cotton Shirt",
        "category": "top",
        "fabric": "cotton",
        "color_or_print": "white",
        "available_sizes": ["M", "L", "XL", "XXL"],
        "fit": "regular",
        "occasion": "formal",
        "sleeve_length": "long",
        "neckline": "button-down",
        "price": 55
    },
    {
        "id": "D005",
        "name": "Cotton Summer Dress",
        "category": "dress",
        "fabric": "cotton",
        "color_or_print": "floral",
        "available_sizes": ["XS", "S", "M"],
        "fit": "loose",
        "occasion": "casual",
        "sleeve_length": "short",
        "neckline": "round",
        "length": "knee",
        "price": 40
    },
    {
        "id": "D006",
        "name": "Polyester Sports Top",
        "category": "top",
        "fabric": "polyester",
        "color_or_print": "black",
        "available_sizes": ["S", "M", "L"],
        "fit": "athletic",
        "occasion": "sports",
        "sleeve_length": "short",
        "neckline": "crew",
        "price": 30
    },
    {
        "id": "D007",
        "name": "Cotton Casual Pants",
        "category": "bottom",
        "fabric": "cotton",
        "color_or_print": "khaki",
        "available_sizes": ["M", "L", "XL"],
        "fit": "regular",
        "occasion": "casual",
        "pant_type": "chinos",
        "length": "full",
        "price": 50
    },
    {
        "id": "D008",
        "name": "Linen Casual Shirt",
        "category": "top",
        "fabric": "linen",
        "color_or_print": "beige",
        "available_sizes": ["S", "M", "L", "XL"],
        "fit": "relaxed",
        "occasion": "casual",
        "sleeve_length": "short",
        "neckline": "button-down",
        "price": 48
    },
    {
        "id": "D009",
        "name": "Cotton V-Neck T-Shirt",
        "category": "top",
        "fabric": "cotton",
        "color_or_print": "gray",
        "available_sizes": ["XS", "S", "M", "L"],
        "fit": "slim",
        "occasion": "casual",
        "sleeve_length": "short",
        "neckline": "v-neck",
        "price": 28
    },
    {
        "id": "D010",
        "name": "Cotton Formal Blazer",
        "category": "top",
        "fabric": "cotton",
        "color_or_print": "navy",
        "available_sizes": ["L", "XL", "XXL"],
        "fit": "tailored",
        "occasion": "formal",
        "sleeve_length": "long",
        "price": 120
    }
]

async def add_sample_data():
    """Add sample apparel data to the database"""
    logger.info("🚀 Adding sample apparel data to database...")
    
    try:
        # Initialize database
        db_manager = init_db()
        client = get_supabase_client()
        logger.info("✅ Database initialized")
        
        # Check current count
        current_response = client.table('apparels').select('id', count='exact').execute()
        current_count = current_response.count if current_response.count else 0
        logger.info(f"📊 Current records in database: {current_count}")
        
        if current_count > 0:
            user_input = input(f"Database already has {current_count} records. Do you want to add more sample data? (y/N): ")
            if user_input.lower() not in ['y', 'yes']:
                logger.info("🛑 Cancelled - no data added")
                return
        
        # Insert sample data
        logger.info(f"📦 Inserting {len(SAMPLE_APPARELS)} sample records...")
        
        for i, apparel in enumerate(SAMPLE_APPARELS, 1):
            try:
                response = client.table('apparels').insert(apparel).execute()
                logger.info(f"✅ Inserted record {i}/{len(SAMPLE_APPARELS)}: {apparel['name']}")
            except Exception as e:
                if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                    logger.warning(f"⚠️ Record {i} already exists: {apparel['name']}")
                else:
                    logger.error(f"❌ Failed to insert record {i}: {e}")
        
        # Verify final count
        final_response = client.table('apparels').select('id', count='exact').execute()
        final_count = final_response.count if final_response.count else 0
        added_count = final_count - current_count
        
        logger.info(f"🎉 Successfully added {added_count} new records!")
        logger.info(f"📊 Total records in database: {final_count}")
        
        # Show a sample of what was added
        sample_response = client.table('apparels').select('*').limit(3).execute()
        if sample_response.data:
            logger.info("📋 Sample records:")
            for record in sample_response.data:
                logger.info(f"   - {record.get('name', 'N/A')} ({record.get('fabric', 'N/A')}, {record.get('size', 'N/A')})")
        
    except Exception as e:
        logger.error(f"❌ Error adding sample data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_sample_data()) 