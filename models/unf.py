"""
Unified Narrative Framework (UNF) Models

Layers and Elements
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum


class ElementStatus(str, Enum):
    """Element status values"""
    DRAFT = "draft"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


# ============================================================================
# LAYERS
# ============================================================================

class LayerBase(BaseModel):
    """Base Layer model"""
    name: str = Field(..., max_length=100, description="Layer name (e.g., Category, Vision, Messaging)")
    description: Optional[str] = Field(None, description="Layer purpose and contents")
    order_index: Optional[int] = Field(None, description="Display order")


class LayerCreate(LayerBase):
    """Create a new Layer"""
    pass


class Layer(LayerBase):
    """Layer database model"""
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ELEMENTS
# ============================================================================

class ElementBase(BaseModel):
    """Base Element model"""
    name: str = Field(..., max_length=200, description="Element name (e.g., Problem, Vision Statement)")
    content: Optional[str] = Field(None, description="The actual narrative content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ElementCreate(ElementBase):
    """Create a new Element"""
    layer_id: UUID4 = Field(..., description="Parent Layer ID")
    version: str = Field("1.0", description="Version number")
    status: ElementStatus = Field(ElementStatus.DRAFT, description="Element status")


class ElementUpdate(BaseModel):
    """Update an existing Element (creates new version)"""
    content: Optional[str] = None
    status: Optional[ElementStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class Element(ElementBase):
    """Element database model"""
    id: UUID4
    layer_id: UUID4
    version: str
    status: ElementStatus
    prev_element_id: Optional[UUID4] = Field(None, description="Previous version ID (for version chain)")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ElementWithLayer(Element):
    """Element with parent Layer details"""
    layer_name: str
