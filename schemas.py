"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# 3D Character Model schema for the shop
class CharacterModel(BaseModel):
    """
    3D Character models for sale
    Collection name: "charactermodel"
    """
    name: str = Field(..., description="Model name")
    description: Optional[str] = Field(None, description="Description of the model")
    price: float = Field(..., ge=0, description="Price in USD")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Thumbnail image URL")
    preview_url: Optional[HttpUrl] = Field(None, description="Optional 3D viewer or video preview URL")
    tags: List[str] = Field(default_factory=list, description="Tags like stylized, sci-fi, fantasy")
    formats: List[str] = Field(default_factory=lambda: ["FBX", "OBJ", "GLB"], description="Included file formats")
    polycount: Optional[str] = Field(None, description="Polycount info, e.g., 25k tris")
    rigged: bool = Field(default=False, description="Whether rigging is included")
    animated: bool = Field(default=False, description="Whether animation clips are included")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating 0-5")
    downloads: int = Field(default=0, ge=0, description="Number of purchases/downloads")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
