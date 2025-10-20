"""
FastAPI Dependencies

Provides shared service instances for dependency injection
"""
from functools import lru_cache
from storage.supabase_storage import SupabaseStorage
from services.unf_service import UNFService
from services.voice_service import VoiceService
from services.story_model_service import StoryModelService
from services.template_service import TemplateService
from services.deliverable_service import DeliverableService
from services.relationship_service import PostgresRelationshipService


@lru_cache()
def get_storage():
    """Get storage instance (cached)"""
    return SupabaseStorage()


def get_unf_service():
    """Get UNF service instance"""
    return UNFService(get_storage())


def get_voice_service():
    """Get Voice service instance"""
    return VoiceService(get_storage())


def get_story_model_service():
    """Get Story Model service instance"""
    return StoryModelService(get_storage())


def get_template_service():
    """Get Template service instance"""
    return TemplateService(get_storage())


def get_relationship_service():
    """Get Relationship service instance"""
    return PostgresRelationshipService(get_storage())


def get_deliverable_service():
    """Get Deliverable service instance"""
    storage = get_storage()
    return DeliverableService(
        storage,
        get_unf_service(),
        get_voice_service(),
        get_template_service(),
        get_story_model_service(),
        get_relationship_service()
    )
