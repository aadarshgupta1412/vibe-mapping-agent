from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.core.database import Base


# Product model
class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    fabric = Column(String)
    fit = Column(String)
    color = Column(String)
    pattern = Column(String)
    style = Column(JSON)  # Array of style tags
    occasion = Column(JSON)  # Array of occasion tags
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "fabric": self.fabric,
            "fit": self.fit,
            "color": self.color,
            "pattern": self.pattern,
            "style": self.style,
            "occasion": self.occasion
        }

# User Preferences model
class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    preferences = Column(JSON)  # Store preferences as JSON
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "preferences": self.preferences
        }

# Vibe to Attribute Mapping model
class VibeMapping(Base):
    __tablename__ = "vibe_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    vibe_term = Column(String, unique=True, index=True)
    attributes = Column(JSON)  # Store attribute mappings as JSON
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "vibe_term": self.vibe_term,
            "attributes": self.attributes
        }
