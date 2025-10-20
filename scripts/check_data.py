#!/usr/bin/env python3
"""
Check what data is in the database
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.supabase_storage import SupabaseStorage
from services.unf_service import UNFService
from services.voice_service import VoiceService
from services.story_model_service import StoryModelService
from services.template_service import TemplateService

load_dotenv()

def main():
    print("=" * 80)
    print("CHECKING STORYOS DATABASE")
    print("=" * 80)

    storage = SupabaseStorage()

    unf_service = UNFService(storage)
    voice_service = VoiceService(storage)
    story_model_service = StoryModelService(storage)
    template_service = TemplateService(storage)

    # Check layers
    layers = unf_service.list_layers()
    print(f"\n📦 UNF Layers: {len(layers)}")
    for layer in layers:
        print(f"  - {layer.name} (order: {layer.order_index})")

    # Check elements
    elements = unf_service.list_elements()
    print(f"\n🎯 UNF Elements: {len(elements)}")
    for elem in elements:
        print(f"  - {elem.name} (Layer: {elem.layer_id}, Version: {elem.version}, Status: {elem.status})")

    # Check voices
    voices = voice_service.list_voices()
    print(f"\n🎤 Brand Voices: {len(voices)}")
    for voice in voices:
        print(f"  - {voice.name} (v{voice.version}, Status: {voice.status})")

    # Check story models
    models = story_model_service.list_story_models()
    print(f"\n📋 Story Models: {len(models)}")
    for model in models:
        print(f"  - {model.name}")

    # Check templates
    templates = template_service.list_templates()
    print(f"\n📄 Deliverable Templates: {len(templates)}")
    for template in templates:
        print(f"  - {template.name} (v{template.version}, Status: {template.status})")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
