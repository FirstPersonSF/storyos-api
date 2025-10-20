"""
Deliverable Template Models

Templates, section bindings, and instance fields
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum


class TemplateStatus(str, Enum):
    """Template status"""
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


# ============================================================================
# INSTANCE FIELDS
# ============================================================================

class InstanceFieldType(str, Enum):
    """Instance field data types"""
    TEXT = "text"
    DATE = "date"
    NUMBER = "number"
    EMAIL = "email"
    URL = "url"


class InstanceField(BaseModel):
    """Metadata field required by specific Deliverables"""
    name: str = Field(..., description="Field name (e.g., 'who', 'what', 'when')")
    field_type: InstanceFieldType = Field(InstanceFieldType.TEXT, description="Data type")
    required: bool = Field(True, description="Is this field required?")
    description: Optional[str] = Field(None, description="Field help text")
    default_value: Optional[str] = Field(None, description="Default value")


# ============================================================================
# SECTION BINDINGS
# ============================================================================

class BindingRule(BaseModel):
    """Rules for how to use Element content in a section"""
    quantity: Optional[int] = Field(None, description="Number of Elements to use")
    transformation: Optional[str] = Field(None, description="e.g., 'excerpt', 'summary', 'full'")
    max_length: Optional[int] = Field(None, description="Max characters/words")
    format: Optional[str] = Field(None, description="e.g., 'bullet', 'paragraph', 'quote'")


class SectionBindingBase(BaseModel):
    """Base Section Binding model"""
    section_name: str = Field(..., max_length=100, description="Template section name")
    section_order: int = Field(..., description="Section order")
    element_ids: List[UUID4] = Field(default_factory=list, description="UNF Element IDs to pull from")
    binding_rules: Optional[BindingRule] = Field(None, description="How to use the Elements")


class SectionBindingCreate(SectionBindingBase):
    """Create a Section Binding"""
    template_id: UUID4


class SectionBinding(SectionBindingBase):
    """Section Binding database model"""
    id: UUID4
    template_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DELIVERABLE TEMPLATES
# ============================================================================

class ValidationRule(BaseModel):
    """Template-level validation rule"""
    rule_type: str = Field(..., description="e.g., 'require_boilerplate', 'max_sections'")
    params: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class TemplateBase(BaseModel):
    """Base Deliverable Template model"""
    name: str = Field(..., max_length=200, description="Template name")
    version: str = Field("1.0", description="Template version")
    validation_rules: List[ValidationRule] = Field(default_factory=list)
    instance_fields: List[InstanceField] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TemplateCreate(TemplateBase):
    """Create a Deliverable Template"""
    story_model_id: UUID4 = Field(..., description="Story Model to use")
    default_voice_id: UUID4 = Field(..., description="Default Brand Voice")
    status: TemplateStatus = Field(TemplateStatus.DRAFT)


class TemplateUpdate(BaseModel):
    """Update a Template"""
    name: Optional[str] = None
    story_model_id: Optional[UUID4] = None
    default_voice_id: Optional[UUID4] = None
    validation_rules: Optional[List[ValidationRule]] = None
    instance_fields: Optional[List[InstanceField]] = None
    status: Optional[TemplateStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class DeliverableTemplate(TemplateBase):
    """Deliverable Template database model"""
    id: UUID4
    story_model_id: UUID4
    default_voice_id: UUID4
    status: TemplateStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateWithBindings(DeliverableTemplate):
    """Template with all section bindings"""
    section_bindings: List[SectionBinding] = Field(default_factory=list)
