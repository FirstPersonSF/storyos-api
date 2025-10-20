"""
Story Model Models

Narrative structures and constraints
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4


# ============================================================================
# STORY MODELS
# ============================================================================

class Section(BaseModel):
    """Story Model Section definition"""
    name: str = Field(..., description="Section name (e.g., Problem, Lede, Quote)")
    intent: str = Field(..., description="Purpose of this section")
    order: int = Field(..., description="Section order in narrative")
    required: bool = Field(True, description="Is this section required?")


class SectionConstraint(BaseModel):
    """Validation constraint for a section"""
    section_name: str
    constraint_type: str = Field(..., description="e.g., 'max_words', 'requires_element', 'format'")
    params: Dict[str, Any] = Field(default_factory=dict, description="Constraint parameters")


class StoryModelBase(BaseModel):
    """Base Story Model"""
    name: str = Field(..., max_length=100, description="Model name (e.g., PAS, Inverted Pyramid)")
    description: Optional[str] = Field(None, description="Model purpose and use cases")
    sections: List[Section] = Field(default_factory=list, description="Ordered list of sections")
    constraints: List[SectionConstraint] = Field(default_factory=list, description="Validation rules")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StoryModelCreate(StoryModelBase):
    """Create a new Story Model"""
    pass


class StoryModel(StoryModelBase):
    """Story Model database model"""
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
