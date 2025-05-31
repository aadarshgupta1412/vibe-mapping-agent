"""
Product Service

This module provides functionality to load and filter product data.
It serves as a tool within the LangGraph conversation flow.
"""

from typing import Dict, List, Any, Optional
import json

# Mock product data
# In a real implementation, this would be loaded from a database or external API
MOCK_PRODUCTS = [
    {
        "id": "T001",
        "name": "Sun-Dapple Floral Top",
        "category": "top",
        "price": 72,
        "fabric": "Linen",
        "fit": "Relaxed",
        "color": "Pastel yellow",
        "pattern": "Floral",
        "style": ["casual", "feminine"],
        "occasion": ["everyday", "casual outing"]
    },
    {
        "id": "D004",
        "name": "Meadow Flatter Dress",
        "category": "dress",
        "price": 110,
        "fabric": "Rayon",
        "fit": "Relaxed",
        "color": "Pastel floral",
        "pattern": "Floral",
        "style": ["cute", "feminine"],
        "occasion": ["brunch", "date"]
    },
    {
        "id": "J002",
        "name": "Urban Edge Jeans",
        "category": "bottom",
        "price": 95,
        "fabric": "Denim",
        "fit": "Slim",
        "color": "Dark blue",
        "pattern": "Solid",
        "style": ["casual", "edgy"],
        "occasion": ["everyday", "casual outing"]
    },
    {
        "id": "B005",
        "name": "Power Move Blazer",
        "category": "outerwear",
        "price": 150,
        "fabric": "Wool blend",
        "fit": "Tailored",
        "color": "Black",
        "pattern": "Solid",
        "style": ["formal", "sophisticated"],
        "occasion": ["work", "business"]
    },
    {
        "id": "S003",
        "name": "Silky Evening Skirt",
        "category": "bottom",
        "price": 85,
        "fabric": "Silk",
        "fit": "A-line",
        "color": "Deep burgundy",
        "pattern": "Solid",
        "style": ["formal", "elegant"],
        "occasion": ["formal event", "evening"]
    }
]

class ProductService:
    """
    Service for loading and filtering product data.
    """
    
    def __init__(self):
        self.products = MOCK_PRODUCTS
    
    def filter_products(self, filters: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
        """
        Filter products based on provided attributes.
        
        Args:
            filters: Dictionary of attribute filters
            limit: Maximum number of products to return
            
        Returns:
            List of filtered products
        """
        results = []
        
        for product in self.products:
            match_score = 0
            max_possible_score = 0
            
            for attr_key, attr_values in filters.items():
                if attr_key not in product:
                    continue
                    
                max_possible_score += 1
                
                # Handle list attributes (like style, occasion)
                if isinstance(product[attr_key], list):
                    product_values = product[attr_key]
                    if isinstance(attr_values, list):
                        # Check if any of the filter values match any of the product values
                        if any(val.lower() in [pv.lower() for pv in product_values] for val in attr_values):
                            match_score += 1
                    else:
                        # Single filter value
                        if attr_values.lower() in [pv.lower() for pv in product_values]:
                            match_score += 1
                
                # Handle string attributes
                elif isinstance(product[attr_key], str):
                    product_value = product[attr_key].lower()
                    if isinstance(attr_values, list):
                        # Check if any of the filter values match the product value
                        if any(val.lower() in product_value for val in attr_values):
                            match_score += 1
                    else:
                        # Single filter value
                        if attr_values.lower() in product_value:
                            match_score += 1
            
            # Calculate match percentage
            match_percentage = match_score / max_possible_score if max_possible_score > 0 else 0
            
            # Add product to results if it matches at least one filter
            if match_score > 0:
                results.append({
                    "product": product,
                    "match_percentage": match_percentage
                })
        
        # Sort by match percentage (descending)
        results.sort(key=lambda x: x["match_percentage"], reverse=True)
        
        # Return only the products, not the match percentages
        return [item["product"] for item in results[:limit]]

# Create a singleton instance
product_service = ProductService()

# Function to be used as a tool in LangGraph
def filter_products_by_attributes(attributes: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """
    Filter products based on attributes.
    This function can be used as a tool in the LangGraph flow.
    
    Args:
        attributes: Dictionary of attributes to filter by
        limit: Maximum number of products to return
        
    Returns:
        List of filtered products
    """
    return product_service.filter_products(attributes, limit)
