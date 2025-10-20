"""
UNF API Routes

Endpoints for Layers and Elements
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from models.unf import Layer, LayerCreate, Element, ElementCreate, ElementUpdate, ElementStatus
from services.unf_service import UNFService
from api.dependencies import get_unf_service


router = APIRouter(prefix="/unf", tags=["UNF"])


# ============================================================================
# LAYERS
# ============================================================================

@router.get("/layers", response_model=List[Layer])
def list_layers(service: UNFService = Depends(get_unf_service)):
    """List all UNF Layers"""
    return service.list_layers()


@router.post("/layers", response_model=Layer, status_code=201)
def create_layer(
    layer_data: LayerCreate,
    service: UNFService = Depends(get_unf_service)
):
    """Create a new UNF Layer"""
    return service.create_layer(layer_data)


@router.get("/layers/{layer_id}", response_model=Layer)
def get_layer(
    layer_id: UUID,
    service: UNFService = Depends(get_unf_service)
):
    """Get a specific Layer by ID"""
    layer = service.get_layer(layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    return layer


# ============================================================================
# ELEMENTS
# ============================================================================

@router.get("/elements", response_model=List[Element])
def list_elements(
    layer_id: Optional[UUID] = None,
    status: Optional[ElementStatus] = None,
    service: UNFService = Depends(get_unf_service)
):
    """
    List Elements with optional filters

    - **layer_id**: Filter by Layer
    - **status**: Filter by status (draft, approved, superseded, archived)
    """
    return service.list_elements(layer_id=layer_id, status=status)


@router.post("/elements", response_model=Element, status_code=201)
def create_element(
    element_data: ElementCreate,
    service: UNFService = Depends(get_unf_service)
):
    """Create a new UNF Element"""
    return service.create_element(element_data)


@router.get("/elements/{element_id}", response_model=Element)
def get_element(
    element_id: UUID,
    service: UNFService = Depends(get_unf_service)
):
    """Get a specific Element by ID"""
    element = service.get_element(element_id)
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    return element


@router.put("/elements/{element_id}", response_model=Element)
def update_element(
    element_id: UUID,
    update_data: ElementUpdate,
    service: UNFService = Depends(get_unf_service)
):
    """
    Update an Element (creates new version)

    This follows the version chain pattern:
    - Creates new Element with updated content
    - Links to previous version via prev_element_id
    - Marks old version as 'superseded'
    """
    try:
        return service.update_element(element_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/elements/{element_id}/versions", response_model=List[Element])
def get_element_versions(
    element_id: UUID,
    service: UNFService = Depends(get_unf_service)
):
    """Get the full version history for an Element (newest to oldest)"""
    return service.get_element_version_chain(element_id)


@router.get("/elements/latest/approved", response_model=List[Element])
def get_latest_approved_elements(
    layer_id: Optional[UUID] = None,
    service: UNFService = Depends(get_unf_service)
):
    """Get the latest approved version of each Element"""
    return service.get_latest_approved_elements(layer_id=layer_id)
