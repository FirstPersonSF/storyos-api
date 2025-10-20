"""
Deliverable Template API Routes
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from models.templates import (
    DeliverableTemplate, TemplateCreate, TemplateUpdate,
    TemplateWithBindings, SectionBinding, SectionBindingCreate,
    TemplateStatus
)
from services.template_service import TemplateService
from api.dependencies import get_template_service


router = APIRouter(prefix="/templates", tags=["Templates"])


# ============================================================================
# TEMPLATES
# ============================================================================

@router.get("", response_model=List[DeliverableTemplate])
def list_templates(
    status: Optional[TemplateStatus] = None,
    service: TemplateService = Depends(get_template_service)
):
    """
    List all Deliverable Templates

    - **status**: Filter by status (draft, approved, archived)
    """
    return service.list_templates(status=status)


@router.post("", response_model=DeliverableTemplate, status_code=201)
def create_template(
    template_data: TemplateCreate,
    service: TemplateService = Depends(get_template_service)
):
    """Create a new Deliverable Template"""
    return service.create_template(template_data)


@router.get("/{template_id}", response_model=TemplateWithBindings)
def get_template(
    template_id: UUID,
    service: TemplateService = Depends(get_template_service)
):
    """Get a specific Template by ID (includes section bindings)"""
    template = service.get_template_with_bindings(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=DeliverableTemplate)
def update_template(
    template_id: UUID,
    update_data: TemplateUpdate,
    service: TemplateService = Depends(get_template_service)
):
    """Update a Template"""
    try:
        return service.update_template(template_id, update_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# SECTION BINDINGS
# ============================================================================

@router.get("/{template_id}/bindings", response_model=List[SectionBinding])
def list_section_bindings(
    template_id: UUID,
    service: TemplateService = Depends(get_template_service)
):
    """List all section bindings for a template"""
    return service.list_section_bindings(template_id)


@router.post("/{template_id}/bindings", response_model=SectionBinding, status_code=201)
def create_section_binding(
    template_id: UUID,
    binding_data: SectionBindingCreate,
    service: TemplateService = Depends(get_template_service)
):
    """Create a new section binding for a template"""
    # Ensure binding is for the correct template
    if binding_data.template_id != template_id:
        raise HTTPException(
            status_code=400,
            detail="Binding template_id does not match URL template_id"
        )

    return service.create_section_binding(binding_data)
