"""
Tools module for the Vibe Mapping Agent.

This module provides tools that can be used by the agent to perform specific tasks,
such as finding apparels based on various filters using the Supabase database.
"""

import logging
from typing import Any, Dict, List, Optional, Union
import json

from langchain.tools import BaseTool, tool

from app.core.config import settings
from app.core.database import get_supabase_client

# Set up logger
logger = logging.getLogger(__name__)

# Define valid values for enum-like fields
VALID_SIZES = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL']
VALID_CATEGORIES = ['dress', 'shirt', 'blouse', 'pants', 'skirt', 'jacket', 'top']
VALID_FITS = ['flowy', 'relaxed', 'body hugging', 'bodycon', 'tailored', 'regular', 'loose', 'fitted']

class ToolsManager:
    """
    Manager for tools used by the agent.
    
    This class provides a collection of tools that can be used by the agent
    to perform specific tasks, such as finding apparels based on attributes.
    """
    
    def __init__(self):
        """Initialize the ToolsManager."""
        self._tools = None
        self._supabase = None
        logger.info("🔧 ToolsManager initialized")
    
    def init(self):
        """Initialize the tools."""
        logger.info("🚀 Initializing ToolsManager...")
        
        if self._tools:
            logger.info("✅ Tools already initialized, returning existing tools")
            return self._tools
        
        # Initialize Supabase client
        try:
            logger.info("🔗 Connecting to Supabase client...")
            self._supabase = get_supabase_client()
            logger.info("✅ Supabase client initialized successfully for tools")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self._supabase = None
        
        # Initialize the tools
        logger.info("🛠️ Creating tool instances...")
        self._tools = self.get_tools()
        logger.info(f"✅ ToolsManager initialization complete with {len(self._tools)} tools")
        return self._tools
    
    def close(self):
        """Close any resources."""
        logger.info("🔄 Closing ToolsManager resources...")
        self._supabase = None
        logger.info("✅ ToolsManager resources closed")
    
    def get_tools(self) -> List[BaseTool]:
        """
        Get all available tools from this ToolsManager instance.
        
        Returns:
            List[BaseTool]: A list of available tools.
        """
        logger.info("📋 Getting tools list...")
        
        all_tools = [
            self._find_apparels_wrapper(),
            self._get_apparel_details_wrapper(),
        ]
        
        tool_names = [getattr(tool, "name", str(tool)) for tool in all_tools]
        logger.info(f"✅ Returning {len(all_tools)} tools: {tool_names}")
        
        return all_tools
    
    def _normalize_size(self, size: str) -> str:
        """Normalize size input to uppercase and validate."""
        if not size:
            return None
        
        normalized = size.upper().strip()
        return normalized if normalized in VALID_SIZES else None
    
    def _normalize_text_filter(self, text: str) -> str:
        """
        Normalize text input for better matching.
        
        This function:
        - Strips whitespace
        - Converts to lowercase for consistency
        - Handles common variations and abbreviations
        """
        if not text:
            return None
        
        # Basic normalization
        normalized = text.strip().lower()
        
        # Handle common variations and abbreviations
        text_mappings = {
            # Category variations
            'tshirt': 't-shirt',
            't shirt': 't-shirt', 
            'tee': 't-shirt',
            'jeans': 'denim',
            'trouser': 'trousers',
            'pant': 'pants',
            
            # Color variations
            'navy': 'navy blue',
            'royal': 'royal blue',
            
            # Fabric variations
            'denim': 'cotton', # Since denim is cotton-based
            
            # Fit variations  
            'tight': 'fitted',
            'loose': 'relaxed',
            'baggy': 'relaxed',
            'slim fit': 'slim',
            'regular fit': 'regular',
            
            # Length variations
            'long': 'maxi',
            'short': 'mini',
            'medium': 'midi',
        }
        
        # Apply mappings
        for key, value in text_mappings.items():
            if normalized == key:
                normalized = value
                break
        
        return normalized
    
    def _validate_price_range(self, min_price: Optional[int], max_price: Optional[int]) -> tuple:
        """Validate and adjust price range."""
        if min_price is not None and min_price < 0:
            min_price = 0
        
        if max_price is not None and max_price < 0:
            max_price = None
        
        if min_price is not None and max_price is not None and min_price > max_price:
            # Swap them
            min_price, max_price = max_price, min_price
        
        return min_price, max_price
    
    def _build_search_query(self, base_query, filters: Dict[str, Any]):
        """Build the Supabase query with proper filtering logic."""
        query = base_query
        applied_filters = {}
        
        # Text-based filters with case-insensitive partial matching
        text_filters = [
            'category', 'color_or_print', 'fabric', 'fit', 'occasion', 
            'sleeve_length', 'neckline', 'length', 'pant_type'
        ]
        
        for field in text_filters:
            value = filters.get(field)
            if value:
                # Normalize the input text
                normalized_value = self._normalize_text_filter(value)
                if not normalized_value:
                    continue
                    
                # Handle multiple values separated by commas or "and"
                if ',' in normalized_value or ' and ' in normalized_value:
                    # Multiple values - use OR logic
                    value_parts = [self._normalize_text_filter(v.strip()) 
                                 for v in normalized_value.replace(' and ', ',').split(',') 
                                 if v.strip()]
                    value_parts = [v for v in value_parts if v]  # Remove None values
                    
                    if len(value_parts) > 1:
                        or_conditions = []
                        for part in value_parts:
                            or_conditions.append(f"{field}.ilike.%{part}%")
                        query = query.or_(','.join(or_conditions))
                        applied_filters[field] = value_parts
                    elif len(value_parts) == 1:
                        query = query.ilike(field, f'%{value_parts[0]}%')
                        applied_filters[field] = value_parts[0]
                else:
                    query = query.ilike(field, f'%{normalized_value}%')
                    applied_filters[field] = normalized_value
        
        # Size filter - now properly validated
        size = filters.get('size')
        if size:
            normalized_size = self._normalize_size(size)
            if normalized_size:
                query = query.contains('available_sizes', [normalized_size])
                applied_filters['size'] = normalized_size
            else:
                logger.warning(f"Invalid size provided: {size}")
        
        # Price filters with validation
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        
        if min_price is not None or max_price is not None:
            min_price, max_price = self._validate_price_range(min_price, max_price)
            
            if min_price is not None:
                query = query.gte('price', min_price)
                applied_filters['min_price'] = min_price
            
            if max_price is not None:
                query = query.lte('price', max_price)
                applied_filters['max_price'] = max_price
        
        return query, applied_filters

    def _find_apparels_wrapper(self) -> BaseTool:
        """Create wrapper for find_apparels tool."""
        
        @tool
        def find_apparels(
            category: Optional[str] = None,
            color_or_print: Optional[str] = None,
            fabric: Optional[str] = None,
            fit: Optional[str] = None,
            occasion: Optional[str] = None,
            size: Optional[str] = None,
            sleeve_length: Optional[str] = None,
            neckline: Optional[str] = None,
            length: Optional[str] = None,
            pant_type: Optional[str] = None,
            max_price: Optional[int] = None,
            min_price: Optional[int] = None,
            limit: Optional[int] = 20,
            sort_by: Optional[str] = "name",
            sort_order: Optional[str] = "asc",
        ) -> Dict[str, Any]:
            """
            Find apparels from the database based on specified filters.
            
            This tool searches the apparels table in Supabase and returns matching items
            based on the provided criteria. All filters are optional and can be combined.
            
            Args:
                category: Type of apparel (e.g., "dress", "shirt", "pants")
                color_or_print: Color or print pattern (e.g., "red", "floral", "striped") 
                fabric: Fabric type (e.g., "cotton", "silk", "linen", "denim")
                fit: Fit type (e.g., "slim", "regular", "loose", "tailored")
                occasion: Occasion type (e.g., "casual", "formal", "party", "wedding")
                size: Size filter (e.g., "S", "M", "L") - checks if size is available
                sleeve_length: Sleeve length (e.g., "short", "long", "sleeveless")
                neckline: Neckline type (e.g., "round", "v-neck", "scoop")
                length: Length (e.g., "mini", "midi", "maxi", "knee-length")
                pant_type: Type of pants (e.g., "jeans", "trousers", "shorts")
                max_price: Maximum price filter
                min_price: Minimum price filter
                limit: Maximum number of results to return (default: 20, max: 100)
                sort_by: Field to sort by (default: "name", options: "name", "price")
                sort_order: Sort order (default: "asc", options: "asc", "desc")
            
            Returns:
                A dictionary containing:
                - success: Boolean indicating if the operation was successful
                - apparels: List of apparels matching the criteria
                - count: Number of results found
                - total_in_db: Total apparels in database (for context)
                - message: A message describing the results
                - filters_applied: Dictionary of filters that were applied
                - suggestions: Alternative suggestions if no results found
            """
            logger.info("🔍 TOOL CALLED: find_apparels")
            
            # Log all input parameters
            params = {
                'category': category,
                'color_or_print': color_or_print,
                'fabric': fabric,
                'fit': fit,
                'occasion': occasion,
                'size': size,
                'sleeve_length': sleeve_length,
                'neckline': neckline,
                'length': length,
                'pant_type': pant_type,
                'max_price': max_price,
                'min_price': min_price,
                'limit': limit,
                'sort_by': sort_by,
                'sort_order': sort_order,
            }
            
            # Filter out None values for cleaner logging
            non_none_params = {k: v for k, v in params.items() if v is not None}
            logger.info(f"📝 Tool parameters received: {non_none_params}")
            
            if not self._supabase:
                error_result = {
                    "success": False,
                    "apparels": [],
                    "count": 0,
                    "total_in_db": 0,
                    "message": "Database connection not available. Please try again later.",
                    "filters_applied": {},
                    "suggestions": []
                }
                logger.error("❌ Supabase client not available")
                logger.info(f"📤 Tool response size: {len(json.dumps(error_result))} chars")
                return error_result
            
            try:
                logger.info("🔧 Validating and processing inputs...")
                
                # Validate and adjust inputs
                limit = min(max(1, limit or 20), 100)  # Ensure between 1-100
                sort_by = sort_by if sort_by in ['name', 'price', 'id'] else 'name'
                sort_order = sort_order if sort_order in ['asc', 'desc'] else 'asc'
                
                logger.debug(f"📊 Processed inputs - limit: {limit}, sort_by: {sort_by}, sort_order: {sort_order}")
                
                # Get total count for context
                logger.info("📊 Getting total apparel count from database...")
                total_response = self._supabase.table('apparels').select('id', count='exact').execute()
                total_in_db = total_response.count if total_response.count else 0
                logger.info(f"📈 Total apparels in database: {total_in_db}")
                
                # Check if database is empty
                if total_in_db == 0:
                    empty_result = {
                        "success": True,
                        "apparels": [],
                        "count": 0,
                        "total_in_db": 0,
                        "message": "The apparel database appears to be empty. No items are currently available.",
                        "filters_applied": {},
                        "suggestions": ["Please contact support to ensure the database is properly populated with apparel items."]
                    }
                    logger.warning("⚠️ Database is empty")
                    logger.info(f"📤 Tool response size: {len(json.dumps(empty_result))} chars")
                    return empty_result
                
                # Start building the query
                logger.info("🔗 Building Supabase query...")
                query = self._supabase.table('apparels').select('*')
                
                # Apply filters using the helper method
                filters = {
                    'category': category,
                    'color_or_print': color_or_print,
                    'fabric': fabric,
                    'fit': fit,
                    'occasion': occasion,
                    'size': size,
                    'sleeve_length': sleeve_length,
                    'neckline': neckline,
                    'length': length,
                    'pant_type': pant_type,
                    'min_price': min_price,
                    'max_price': max_price,
                }
                
                logger.info("🎯 Applying filters to query...")
                query, applied_filters = self._build_search_query(query, filters)
                logger.info(f"🎯 Applied filters: {applied_filters}")
                
                # Apply sorting
                logger.info(f"📊 Applying sorting: {sort_by} {sort_order}")
                if sort_order == 'desc':
                    query = query.order(sort_by, desc=True)
                else:
                    query = query.order(sort_by)
                
                # Apply limit
                logger.info(f"📏 Applying limit: {limit}")
                query = query.limit(limit)
                
                # Execute the query
                logger.info("🚀 Executing Supabase query...")
                response = query.execute()
                logger.info(f"✅ Query executed successfully, response data length: {len(response.data) if response.data else 0}")
                
                if response.data:
                    apparels = response.data
                    count = len(apparels)
                    
                    logger.info(f"🎉 Found {count} apparels")
                    
                    # Log details about found apparels
                    if count > 0:
                        apparel_ids = [apparel.get('id', 'unknown') for apparel in apparels[:5]]  # Log first 5 IDs
                        logger.info(f"📋 Found apparel IDs (first 5): {apparel_ids}")
                    
                    # Generate enhanced message
                    if count > 0:
                        filter_desc = []
                        if applied_filters:
                            for key, value in applied_filters.items():
                                if isinstance(value, list):
                                    filter_desc.append(f"{key.replace('_', ' ')}: {' or '.join(map(str, value))}")
                                else:
                                    filter_desc.append(f"{key.replace('_', ' ')}: {value}")
                        
                        if filter_desc:
                            message = f"Found {count} apparel(s) matching: {', '.join(filter_desc)}"
                        else:
                            message = f"Found {count} apparel(s) from our collection"
                        
                        if count == limit and total_in_db > limit:
                            message += f" (showing first {limit} of possibly more results)"
                    else:
                        message = "No apparels found matching your criteria."
                    
                    result = {
                        "success": True,
                        "apparels": apparels,
                        "count": count,
                        "total_in_db": total_in_db,
                        "message": message,
                        "filters_applied": applied_filters,
                        "suggestions": self._generate_suggestions(applied_filters) if count == 0 else []
                    }
                    
                    logger.info(f"📤 Tool response size: {len(json.dumps(result, default=str))} chars")
                    logger.info(f"✅ TOOL SUCCESS: find_apparels returned {count} results")
                    return result
                else:
                    no_results = {
                        "success": True,
                        "apparels": [],
                        "count": 0,
                        "total_in_db": total_in_db,
                        "message": "No apparels found matching your criteria",
                        "filters_applied": applied_filters,
                        "suggestions": self._generate_suggestions(applied_filters)
                    }
                    logger.info("📤 No results found")
                    logger.info(f"📤 Tool response size: {len(json.dumps(no_results))} chars")
                    return no_results
                    
            except Exception as e:
                error_msg = f"Error in find_apparels tool: {str(e)}"
                logger.error(f"❌ {error_msg}")
                logger.exception("Full exception details:")
                
                error_result = {
                    "success": False,
                    "apparels": [],
                    "count": 0,
                    "total_in_db": 0,
                    "message": f"An error occurred while searching: {str(e)}",
                    "filters_applied": {},
                    "suggestions": []
                }
                logger.info(f"📤 Tool error response size: {len(json.dumps(error_result))} chars")
                return error_result
        
        return find_apparels
    
    def _generate_suggestions(self, failed_filters: Dict[str, Any]) -> List[str]:
        """Generate helpful suggestions when no results are found."""
        suggestions = []
        
        if 'size' in failed_filters:
            suggestions.append(f"Try different sizes like {', '.join(VALID_SIZES[:5])}")
        
        if 'category' in failed_filters:
            suggestions.append(f"Try browsing other categories like {', '.join(VALID_CATEGORIES[:3])}")
        
        if 'max_price' in failed_filters or 'min_price' in failed_filters:
            suggestions.append("Try adjusting your price range")
        
        if len(failed_filters) > 3:
            suggestions.append("Try using fewer filters to see more options")
        
        return suggestions

    def _get_apparel_details_wrapper(self) -> BaseTool:
        """Create wrapper for get_apparel_details tool."""
        
        @tool
        def get_apparel_details(apparel_id: str) -> Dict[str, Any]:
            """
            Get detailed information about a specific apparel item by ID.
            
            This tool retrieves complete details for a single apparel item from the database.
            
            Args:
                apparel_id: The unique identifier of the apparel item (e.g., "D001", "D002")
            
            Returns:
                A dictionary containing:
                - success: Boolean indicating if the operation was successful
                - apparel: Complete details of the apparel item
                - message: A message describing the result
            """
            logger.info("🔍 TOOL CALLED: get_apparel_details")
            logger.info(f"📝 Tool parameter - apparel_id: {apparel_id}")
            
            if not self._supabase:
                error_result = {
                    "success": False,
                    "apparel": None,
                    "message": "Database connection not available"
                }
                logger.error("❌ Supabase client not available")
                logger.info(f"📤 Tool response size: {len(json.dumps(error_result))} chars")
                return error_result
            
            if not apparel_id or not apparel_id.strip():
                invalid_result = {
                    "success": False,
                    "apparel": None,
                    "message": "Please provide a valid apparel ID"
                }
                logger.warning("⚠️ Invalid apparel_id provided")
                logger.info(f"📤 Tool response size: {len(json.dumps(invalid_result))} chars")
                return invalid_result
            
            try:
                logger.info(f"🔗 Querying database for apparel ID: {apparel_id.strip()}")
                
                # Query for the specific apparel item
                response = self._supabase.table('apparels').select('*').eq('id', apparel_id.strip()).execute()
                logger.info(f"✅ Query executed, response data length: {len(response.data) if response.data else 0}")
                
                if response.data and len(response.data) > 0:
                    apparel = response.data[0]
                    logger.info(f"🎉 Found apparel: {apparel.get('name', 'unknown name')}")
                    
                    result = {
                        "success": True,
                        "apparel": apparel,
                        "message": f"Found details for {apparel.get('name', apparel_id)}"
                    }
                    logger.info(f"📤 Tool response size: {len(json.dumps(result, default=str))} chars")
                    logger.info(f"✅ TOOL SUCCESS: get_apparel_details found item")
                    return result
                else:
                    not_found_result = {
                        "success": False,
                        "apparel": None,
                        "message": f"No apparel found with ID: {apparel_id}"
                    }
                    logger.warning(f"⚠️ No apparel found with ID: {apparel_id}")
                    logger.info(f"📤 Tool response size: {len(json.dumps(not_found_result))} chars")
                    return not_found_result
                    
            except Exception as e:
                error_msg = f"Error in get_apparel_details tool: {str(e)}"
                logger.error(f"❌ {error_msg}")
                logger.exception("Full exception details:")
                
                error_result = {
                    "success": False,
                    "apparel": None,
                    "message": f"An error occurred while fetching details: {str(e)}"
                }
                logger.info(f"📤 Tool error response size: {len(json.dumps(error_result))} chars")
                return error_result
        
        return get_apparel_details


# Singleton instance getter
_tools_manager_instance = None

def get_tools_manager():
    """Get the singleton instance of ToolsManager"""
    global _tools_manager_instance
    if _tools_manager_instance is None:
        logger.info("🆕 Creating new ToolsManager instance")
        _tools_manager_instance = ToolsManager()
    else:
        logger.debug("♻️ Returning existing ToolsManager instance")
    return _tools_manager_instance

def init_tools_manager():
    """Initialize the tools manager"""
    logger.info("🚀 Initializing tools manager singleton...")
    manager = get_tools_manager()
    tools = manager.init()
    logger.info(f"✅ Tools manager initialized with {len(tools) if tools else 0} tools")
    return manager

def close_tools_manager():
    """Close the tools manager"""
    logger.info("🔄 Closing tools manager singleton...")
    manager = get_tools_manager()
    manager.close()
    logger.info("✅ Tools manager closed")
