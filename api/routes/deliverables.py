"""
Deliverable API Routes
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from models.deliverables import (
    Deliverable, DeliverableCreate, DeliverableUpdate,
    DeliverableWithAlerts, DeliverableStatus, ValidationLogEntry
)
from services.deliverable_service import DeliverableService
from api.dependencies import get_deliverable_service


router = APIRouter(prefix="/deliverables", tags=["Deliverables"])


@router.get("", response_model=List[Deliverable])
def list_deliverables(
    status: Optional[DeliverableStatus] = None,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    List all Deliverables

    - **status**: Filter by status (draft, review, approved, published)
    """
    return service.list_deliverables(status=status)


@router.get("/with-alerts", response_model=List[DeliverableWithAlerts])
def list_deliverables_with_alerts(
    status: Optional[DeliverableStatus] = None,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    List all Deliverables with impact alerts in a single efficient call

    This is much more efficient than calling /{id}/with-alerts for each deliverable
    as it uses a single database transaction and reuses element/template lookups.
    """
    try:
        deliverables = service.list_deliverables(status=status)

        # Get alerts for all deliverables in a single pass
        deliverables_with_alerts = []
        for deliverable in deliverables:
            alerts = service._check_for_updates(deliverable)
            deliverables_with_alerts.append(DeliverableWithAlerts(
                **deliverable.model_dump(),
                alerts=alerts,
                has_updates=len(alerts) > 0
            ))

        return deliverables_with_alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading deliverables with alerts: {str(e)}")


@router.post("", response_model=Deliverable, status_code=201)
def create_deliverable(
    deliverable_data: DeliverableCreate,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    Create a new Deliverable

    This assembles content from UNF Elements, applies Brand Voice,
    and tracks dependencies for impact alerts.
    """
    try:
        return service.create_deliverable(deliverable_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating deliverable: {str(e)}")


@router.get("/{deliverable_id}", response_model=Deliverable)
def get_deliverable(
    deliverable_id: UUID,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """Get a specific Deliverable by ID"""
    deliverable = service.get_deliverable(deliverable_id)
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    return deliverable


@router.get("/{deliverable_id}/with-alerts", response_model=DeliverableWithAlerts)
def get_deliverable_with_alerts(
    deliverable_id: UUID,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    Get a Deliverable with impact alerts

    Returns alerts if any UNF Elements used by this Deliverable have been updated
    """
    try:
        deliverable = service.get_deliverable_with_alerts(deliverable_id)
        if not deliverable:
            raise HTTPException(status_code=404, detail="Deliverable not found")
        return deliverable
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading deliverable: {str(e)}")


@router.get("/{deliverable_id}/versions", response_model=List[Deliverable])
def get_deliverable_versions(
    deliverable_id: UUID,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    Get all versions of a Deliverable

    Returns version history sorted by version number (newest first).
    Traces the full version chain through prev_deliverable_id links.
    """
    versions = service.get_deliverable_versions(deliverable_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    return versions


@router.put("/{deliverable_id}")
def update_deliverable(
    deliverable_id: UUID,
    update_data: DeliverableUpdate,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """Update a Deliverable"""
    try:
        deliverable = service.update_deliverable(deliverable_id, update_data)
        # Use model_dump with mode='json' to properly serialize datetime objects
        return deliverable.model_dump(mode='json')
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{deliverable_id}/validate", response_model=List[ValidationLogEntry])
def validate_deliverable(
    deliverable_id: UUID,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    Run validation checks on a Deliverable

    Checks instance fields, constraints, and other validation rules
    """
    try:
        return service.validate_deliverable(deliverable_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{deliverable_id}/refresh", response_model=Deliverable)
def refresh_deliverable(
    deliverable_id: UUID,
    force: bool = False,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    Refresh a Deliverable with latest element versions

    Re-renders content using the most recent approved versions
    of all elements used in the deliverable.

    This implements the "Update Available" → "Refresh" workflow.

    **Parameters:**
    - **force**: If True, refreshes even if draft element updates exist (default: False).
                 Normally, refresh is blocked when elements have draft versions pending approval.
    """
    try:
        return service.refresh_deliverable(deliverable_id, force=force)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing deliverable: {str(e)}")


@router.post("/{deliverable_id}/preview")
def preview_deliverable_with_drafts(
    deliverable_id: UUID,
    service: DeliverableService = Depends(get_deliverable_service)
):
    """
    Preview deliverable with draft element versions

    Temporarily renders the deliverable using draft versions of elements
    where drafts exist. Does not save changes to database.

    Returns the same structure as a regular deliverable, but with
    rendered_content showing what it would look like with drafts applied.

    This implements the "Update Pending" → "Preview" workflow.

    **Returns:**
    - **deliverable_id**: The deliverable ID
    - **preview_rendered_content**: Content with draft elements applied
    - **original_rendered_content**: Current deliverable content
    - **draft_elements_used**: List of elements that have draft versions
    - **preview_note**: Info message
    """
    try:
        return service.preview_deliverable_with_drafts(deliverable_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing deliverable: {str(e)}")
