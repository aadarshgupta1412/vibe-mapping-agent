"""
Vibe Mapper Service

This module provides functionality to map vague "vibe" terms to structured product attributes.
It serves as a tool within the LangGraph conversation flow.
"""

from typing import Dict, List, Any, Optional

# Sample vibe-to-attribute mappings
# In a real implementation, these could be more extensive or even learned from data
VIBE_MAPPINGS = {
    "casual": {
        "style": ["relaxed", "everyday", "comfortable"],
        "fabric": ["cotton", "denim", "jersey", "linen"],
        "fit": ["relaxed", "regular"],
        "occasion": ["everyday", "weekend", "casual outing"]
    },
    "formal": {
        "style": ["elegant", "sophisticated", "tailored"],
        "fabric": ["silk", "satin", "wool", "polyester blend"],
        "fit": ["tailored", "slim"],
        "occasion": ["work", "business", "formal event"]
    },
    "cute": {
        "style": ["playful", "feminine", "youthful"],
        "pattern": ["floral", "polka dot", "heart"],
        "color": ["pastel", "pink", "light blue", "lavender"],
        "occasion": ["date", "casual outing", "brunch"]
    },
    "edgy": {
        "style": ["bold", "statement", "modern"],
        "color": ["black", "dark", "metallic"],
        "fabric": ["leather", "denim", "mesh"],
        "occasion": ["night out", "concert", "party"]
    },
    "boho": {
        "style": ["bohemian", "free-spirited", "artistic"],
        "pattern": ["paisley", "floral", "ethnic"],
        "fabric": ["cotton", "linen", "crochet"],
        "fit": ["flowy", "relaxed"],
        "occasion": ["festival", "beach", "casual outing"]
    }
}

class VibeMapper:
    """
    Maps vibe terms to structured product attributes.
    """
    
    def __init__(self):
        self.vibe_mappings = VIBE_MAPPINGS
    
    def map_vibe_to_attributes(self, vibe_terms: List[str]) -> Dict[str, Any]:
        """
        Maps a list of vibe terms to structured product attributes.
        
        Args:
            vibe_terms: List of vibe terms to map
            
        Returns:
            Dictionary of structured attributes
        """
        attributes = {
            "style": [],
            "fabric": [],
            "fit": [],
            "pattern": [],
            "color": [],
            "occasion": []
        }
        
        # Map each vibe term to attributes
        for term in vibe_terms:
            term = term.lower()
            if term in self.vibe_mappings:
                mapping = self.vibe_mappings[term]
                
                # Add mapped attributes to our result
                for attr_key, attr_values in mapping.items():
                    if attr_key in attributes:
                        attributes[attr_key].extend(attr_values)
        
        # Remove duplicates
        for attr_key in attributes:
            attributes[attr_key] = list(set(attributes[attr_key]))
            
        # Remove empty attributes
        attributes = {k: v for k, v in attributes.items() if v}
        
        return attributes
    
    def extract_vibe_terms(self, query: str) -> List[str]:
        """
        Extracts potential vibe terms from a user query.
        
        In a real implementation, this would use an LLM to identify vibe terms.
        For now, we'll use a simple keyword matching approach.
        
        Args:
            query: User query string
            
        Returns:
            List of identified vibe terms
        """
        query = query.lower()
        found_terms = []
        
        for term in self.vibe_mappings.keys():
            if term in query:
                found_terms.append(term)
                
        return found_terms

# Create a singleton instance
vibe_mapper = VibeMapper()

# Function to be used as a tool in LangGraph
def map_vibe_query(query: str) -> Dict[str, Any]:
    """
    Maps a vibe-based query to structured attributes.
    This function can be used as a tool in the LangGraph flow.
    
    Args:
        query: User query string
        
    Returns:
        Dictionary with extracted vibe terms and mapped attributes
    """
    # Extract vibe terms from the query
    vibe_terms = vibe_mapper.extract_vibe_terms(query)
    
    # Map vibe terms to attributes
    attributes = vibe_mapper.map_vibe_to_attributes(vibe_terms)
    
    return {
        "vibe_terms": vibe_terms,
        "attributes": attributes
    }
