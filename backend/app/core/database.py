import logging
from typing import Any, Dict, List, Optional

from supabase import create_client, Client

from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Singleton database manager for Supabase connections"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._supabase = None
        self._initialized = True
        logger.info("DatabaseManager instance created")
    
    def init(self):
        """Initialize database connections"""
        # Initialize Supabase client
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            self._init_supabase()
            logger.info("Supabase client initialized")
    
    def _init_supabase(self):
        """Initialize Supabase client"""
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        try:
            # Create client with basic parameters - compatible with gotrue 2.8.1 and httpx 0.25.2
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("✅ Supabase client created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create Supabase client: {e}")
            self._supabase = None
            raise
    
    async def check_connection(self):
        """Check if the Supabase connection is working"""
        try:
            # Just check if we have a valid client
            client = self.get_supabase_client()
            if client is not None:
                # Test with a simple query to verify the connection works
                try:
                    # Try to get table info (this is a lightweight operation)
                    response = client.table('apparels').select('id').limit(1).execute()
                    logger.info("✅ Supabase connection verified successfully")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ Supabase connection test failed: {e}")
                    return False
            else:
                logger.error("❌ Supabase client is None")
                return False
        except Exception as e:
            logger.error(f"❌ Supabase connection error: {e}")
            return False
    
    def close(self):
        """Close database connections"""
        # Clear Supabase client
        self._supabase = None
        logger.info("Supabase client cleared")
    
    def get_supabase_client(self) -> Client:
        """Get Supabase client"""
        if self._supabase is None:
            self._init_supabase()
        return self._supabase


# Create a singleton instance
db_manager = DatabaseManager()


# Convenience functions that use the singleton
def get_supabase_client() -> Client:
    """Get Supabase client from the singleton manager"""
    return db_manager.get_supabase_client()


def init_db():
    """Initialize database connections using the singleton manager
    
    Returns:
        DatabaseManager: The initialized database manager instance
    """
    db_manager.init()
    return db_manager


async def check_connection():
    """Check if the database connection is working"""
    return await db_manager.check_connection()


def close_db():
    """Close database connections using the singleton manager"""
    db_manager.close()
