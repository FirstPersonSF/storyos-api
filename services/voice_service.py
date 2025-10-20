"""
Brand Voice Service

Manages Brand Voice configurations
"""
from typing import List, Optional
from uuid import UUID
import ujson as json

from models.voice import BrandVoice, BrandVoiceCreate, BrandVoiceUpdate, VoiceStatus
from storage.postgres_storage import PostgresStorage


class VoiceService:
    """Service for Brand Voice management"""

    def __init__(self, storage: PostgresStorage):
        self.storage = storage

    def create_voice(self, voice_data: BrandVoiceCreate) -> BrandVoice:
        """Create a new Brand Voice"""
        data = voice_data.model_dump(exclude_unset=True)

        # Convert complex fields to JSON
        for field in ['traits', 'tone_rules', 'style_guardrails', 'lexicon', 'metadata']:
            if field in data and data[field] is not None:
                if not isinstance(data[field], str):
                    data[field] = json.dumps(data[field].model_dump() if hasattr(data[field], 'model_dump') else data[field])

        # Handle status enum
        if 'status' in data and isinstance(data['status'], VoiceStatus):
            data['status'] = data['status'].value

        voice_id = self.storage.insert_one(
            "brand_voices",
            data,
            returning="id"
        )

        return self.get_voice(voice_id)

    def get_voice(self, voice_id: UUID) -> Optional[BrandVoice]:
        """Get a Brand Voice by ID"""
        row = self.storage.get_one("brand_voices", voice_id)
        if not row:
            return None

        # Parse JSON fields back to objects
        for field in ['traits', 'tone_rules', 'style_guardrails', 'lexicon', 'metadata']:
            if field in row and isinstance(row[field], str):
                row[field] = json.loads(row[field])

        return BrandVoice(**row)

    def update_voice(
        self,
        voice_id: UUID,
        update_data: BrandVoiceUpdate
    ) -> BrandVoice:
        """Update a Brand Voice"""
        data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # Convert complex fields to JSON
        for field in ['traits', 'tone_rules', 'style_guardrails', 'lexicon', 'metadata']:
            if field in data and data[field] is not None:
                if not isinstance(data[field], str):
                    data[field] = json.dumps(data[field].model_dump() if hasattr(data[field], 'model_dump') else data[field])

        # Handle status enum
        if 'status' in data and isinstance(data['status'], VoiceStatus):
            data['status'] = data['status'].value

        self.storage.update_one("brand_voices", voice_id, data)
        return self.get_voice(voice_id)

    def list_voices(self, status: Optional[VoiceStatus] = None) -> List[BrandVoice]:
        """List all Brand Voices with optional status filter"""
        filters = {}
        if status:
            filters['status'] = status.value

        rows = self.storage.get_many(
            "brand_voices",
            filters=filters if filters else None,
            order_by="created_at DESC"
        )

        # Parse JSON fields
        voices = []
        for row in rows:
            for field in ['traits', 'tone_rules', 'style_guardrails', 'lexicon', 'metadata']:
                if field in row and isinstance(row[field], str):
                    row[field] = json.loads(row[field])
            voices.append(BrandVoice(**row))

        return voices

    def apply_voice_filter(
        self,
        content: str,
        voice: BrandVoice
    ) -> tuple[str, List[str]]:
        """
        Apply Brand Voice rules to content

        Returns:
            (filtered_content, violations)

        For prototype: Simple lexicon checking
        Future: LLM-based tone transformation
        """
        violations = []
        filtered_content = content

        # Check banned terms
        if voice.lexicon and hasattr(voice.lexicon, 'banned'):
            for banned_term in voice.lexicon.banned:
                if banned_term.lower() in content.lower():
                    violations.append(f"Contains banned term: '{banned_term}'")

        # Check required terms (warn if missing)
        if voice.lexicon and hasattr(voice.lexicon, 'required'):
            for required_term in voice.lexicon.required:
                if required_term not in content:
                    violations.append(f"Missing required phrase: '{required_term}'")

        return filtered_content, violations
