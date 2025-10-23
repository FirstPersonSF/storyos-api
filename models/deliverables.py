"""
Deliverable Models

Final outputs with provenance and impact tracking
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum


class DeliverableStatus(str, Enum):
    """Deliverable status"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"


# ============================================================================
# VALIDATION LOG
# ============================================================================

class ValidationLogEntry(BaseModel):
    """Single validation check result"""
    timestamp: datetime
    rule: str = Field(..., description="Validation rule that was checked")
    passed: bool = Field(..., description="Did it pass?")
    message: Optional[str] = Field(None, description="Details or error message")


# ============================================================================
# IMPACT ALERTS
# ============================================================================

class ImpactAlert(BaseModel):
    """Alert when source Elements have been updated"""
    element_id: UUID4
    element_name: str
    old_version: str
    new_version: str
    status: str = Field(..., description="'update_available' or 'update_pending'")


# ============================================================================
# DELIVERABLES
# ============================================================================

class DeliverableBase(BaseModel):
    """Base Deliverable model"""
    name: str = Field(..., min_length=1, max_length=200, description="Deliverable name (required)")
    instance_data: Dict[str, Any] = Field(default_factory=dict, description="Instance-specific fields (who, what, when, etc.)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeliverableCreate(DeliverableBase):
    """Create a new Deliverable"""
    template_id: UUID4 = Field(..., description="Template to use")
    voice_id: Optional[UUID4] = Field(None, description="Override default Voice")
    status: DeliverableStatus = Field(DeliverableStatus.DRAFT)


class DeliverableUpdate(BaseModel):
    """Update a Deliverable"""
    name: Optional[str] = None
    voice_id: Optional[UUID4] = None
    story_model_id: Optional[UUID4] = None
    instance_data: Optional[Dict[str, Any]] = None
    status: Optional[DeliverableStatus] = None
    rendered_content: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class Deliverable(DeliverableBase):
    """Deliverable database model"""
    id: UUID4
    template_id: UUID4
    template_version: str
    story_model_id: UUID4
    voice_id: UUID4
    voice_version: str
    status: DeliverableStatus
    version: int = Field(1, description="Version number (increments with each update)")
    prev_deliverable_id: Optional[UUID4] = Field(None, description="Previous version of this deliverable")
    element_versions: Dict[str, str] = Field(default_factory=dict, description="Snapshot of Element versions used")
    rendered_content: Dict[str, str] = Field(default_factory=dict, description="Final rendered text by section")
    validation_log: List[ValidationLogEntry] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliverableWithAlerts(Deliverable):
    """Deliverable with impact alerts"""
    alerts: List[ImpactAlert] = Field(default_factory=list, description="Elements that have been updated")
    has_updates: bool = Field(False, description="Are there any pending updates?")


class DeliverableRenderRequest(BaseModel):
    """Request to render a Deliverable"""
    deliverable_id: UUID4
    force_refresh: bool = Field(False, description="Force re-fetch of all Elements")


class DeliverableRenderResponse(BaseModel):
    """Rendered Deliverable output"""
    deliverable_id: UUID4
    sections: Dict[str, str] = Field(..., description="Rendered content by section")
    validation_passed: bool
    validation_log: List[ValidationLogEntry]
    provenance: Dict[str, Any] = Field(..., description="Full audit trail")
