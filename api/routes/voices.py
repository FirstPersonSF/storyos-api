"""
Brand Voice API Routes
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from models.voice import BrandVoice, BrandVoiceCreate, BrandVoiceUpdate, VoiceStatus
from services.voice_service import VoiceService
from api.dependencies import get_voice_service


router = APIRouter(prefix="/voices", tags=["Brand Voices"])


@router.get("", response_model=List[BrandVoice])
def list_voices(
    status: Optional[VoiceStatus] = None,
    service: VoiceService = Depends(get_voice_service)
):
    """
    List all Brand Voices

    - **status**: Filter by status (draft, approved, archived)
    """
    return service.list_voices(status=status)


@router.post("", response_model=BrandVoice, status_code=201)
def create_voice(
    voice_data: BrandVoiceCreate,
    service: VoiceService = Depends(get_voice_service)
):
    """Create a new Brand Voice"""
    return service.create_voice(voice_data)


@router.get("/{voice_id}", response_model=BrandVoice)
def get_voice(
    voice_id: UUID,
    service: VoiceService = Depends(get_voice_service)
):
    """Get a specific Brand Voice by ID"""
    voice = service.get_voice(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Brand Voice not found")
    return voice


@router.put("/{voice_id}", response_model=BrandVoice)
def update_voice(
    voice_id: UUID,
    update_data: BrandVoiceUpdate,
    service: VoiceService = Depends(get_voice_service)
):
    """Update a Brand Voice"""
    try:
        return service.update_voice(voice_id, update_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
