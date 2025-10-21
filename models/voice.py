"""
Brand Voice Models

Tone, style, and lexicon configurations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum


class VoiceStatus(str, Enum):
    """Brand Voice status"""
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


# ============================================================================
# BRAND VOICE
# ============================================================================

class ToneRules(BaseModel):
    """Tone configuration"""
    formality: Optional[str] = Field(None, description="e.g., 'medium-high'")
    point_of_view: Optional[str] = Field(None, description="e.g., 'third-person'")
    sentence_length: Optional[str] = Field(None, description="e.g., '15-25 words average'")
    voice: Optional[str] = Field(None, description="e.g., 'active voice required'")
    contractions: Optional[str] = Field(None, description="e.g., 'allowed in informal materials'")
    tense: Optional[str] = Field(None, description="e.g., 'present tense preferred'")


class StyleGuardrails(BaseModel):
    """Style do's and don'ts"""
    do: List[str] = Field(default_factory=list, description="Encouraged practices")
    dont: List[str] = Field(default_factory=list, description="Discouraged practices")
    punctuation: Optional[str] = Field(None, description="Punctuation preferences")


class Lexicon(BaseModel):
    """Required and banned terms"""
    required: List[str] = Field(default_factory=list, description="Required phrases")
    banned: List[str] = Field(default_factory=list, description="Banned terms")
    preferred: List[str] = Field(default_factory=list, description="Preferred terms")


class BrandVoiceBase(BaseModel):
    """Base Brand Voice model"""
    name: str = Field(..., max_length=100, description="Voice name (e.g., Corporate, Product)")
    version: str = Field("1.0", description="Voice version")
    traits: List[str] = Field(default_factory=list, description="Personality traits")
    tone_rules: Optional[ToneRules] = Field(None, description="Tone configuration")
    style_guardrails: Optional[StyleGuardrails] = Field(None, description="Style guidelines")
    lexicon: Optional[Lexicon] = Field(None, description="Required and banned terms")
    readability_range: Optional[str] = Field(None, description="Target reading level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BrandVoiceCreate(BrandVoiceBase):
    """Create a new Brand Voice"""
    parent_voice_id: Optional[UUID4] = Field(None, description="Parent voice for inheritance")
    status: VoiceStatus = Field(VoiceStatus.DRAFT, description="Voice status")


class BrandVoiceUpdate(BaseModel):
    """Update a Brand Voice"""
    name: Optional[str] = None
    traits: Optional[List[str]] = None
    tone_rules: Optional[ToneRules] = None
    style_guardrails: Optional[StyleGuardrails] = None
    lexicon: Optional[Lexicon] = None
    readability_range: Optional[str] = None
    status: Optional[VoiceStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class BrandVoice(BrandVoiceBase):
    """Brand Voice database model"""
    id: UUID4
    parent_voice_id: Optional[UUID4] = None
    status: VoiceStatus
    rules: Optional[Dict[str, Any]] = Field(None, description="Phase 2: Voice transformation rules (lexicon, terminology, tone)")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
