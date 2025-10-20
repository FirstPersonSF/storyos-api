"""
Story Model API Routes
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from models.story_models import StoryModel, StoryModelCreate
from services.story_model_service import StoryModelService
from api.dependencies import get_story_model_service


router = APIRouter(prefix="/story-models", tags=["Story Models"])


@router.get("", response_model=List[StoryModel])
def list_story_models(service: StoryModelService = Depends(get_story_model_service)):
    """List all Story Models"""
    return service.list_story_models()


@router.post("", response_model=StoryModel, status_code=201)
def create_story_model(
    model_data: StoryModelCreate,
    service: StoryModelService = Depends(get_story_model_service)
):
    """Create a new Story Model"""
    return service.create_story_model(model_data)


@router.get("/{model_id}", response_model=StoryModel)
def get_story_model(
    model_id: UUID,
    service: StoryModelService = Depends(get_story_model_service)
):
    """Get a specific Story Model by ID"""
    model = service.get_story_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Story Model not found")
    return model


@router.get("/by-name/{name}", response_model=StoryModel)
def get_story_model_by_name(
    name: str,
    service: StoryModelService = Depends(get_story_model_service)
):
    """Get a Story Model by name"""
    model = service.get_story_model_by_name(name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Story Model '{name}' not found")
    return model
