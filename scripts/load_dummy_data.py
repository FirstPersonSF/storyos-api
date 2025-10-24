#!/usr/bin/env python3
"""
Load StoryOS Dummy Data

Loads all test data from Documentation/StoryOS - Prototype DummyData.md
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.supabase_storage import SupabaseStorage
from services.unf_service import UNFService
from services.voice_service import VoiceService
from services.story_model_service import StoryModelService
from services.template_service import TemplateService
from services.deliverable_service import DeliverableService
from services.relationship_service import PostgresRelationshipService

from models.unf import LayerCreate, ElementCreate, ElementStatus
from models.voice import BrandVoiceCreate, VoiceStatus, ToneRules, StyleGuardrails, Lexicon
from models.story_models import StoryModelCreate, Section, SectionConstraint
from models.templates import TemplateCreate, TemplateStatus, SectionBindingCreate, InstanceField, InstanceFieldType

# Load environment
load_dotenv()


def main():
    print("=" * 80)
    print("LOADING STORYOS DUMMY DATA")
    print("=" * 80)

    # Initialize storage and services
    print("\n🔗 Connecting to database...")
    storage = SupabaseStorage()

    unf_service = UNFService(storage)
    voice_service = VoiceService(storage)
    story_model_service = StoryModelService(storage)
    template_service = TemplateService(storage)
    relationship_service = PostgresRelationshipService(storage)

    # DeliverableService needs all other services
    deliverable_service = DeliverableService(
        storage,
        unf_service,
        voice_service,
        template_service,
        story_model_service,
        relationship_service
    )

    print("✅ Connected")

    # Track created IDs
    layer_ids = {}
    element_ids = {}
    voice_ids = {}
    model_ids = {}
    template_ids = {}

    # ========================================================================
    # 1. CREATE UNF LAYERS
    # ========================================================================
    print("\n📦 Creating UNF Layers...")

    layers_data = [
        {"name": "Category", "description": "Industry context and problem definition", "order_index": 1},
        {"name": "Vision", "description": "Aspirational future state and principles", "order_index": 2},
        {"name": "Messaging", "description": "Key messages and boilerplate", "order_index": 3}
    ]

    for layer_data in layers_data:
        # Check if layer already exists
        existing_layers = unf_service.list_layers()
        existing_layer = next((l for l in existing_layers if l.name == layer_data["name"]), None)

        if existing_layer:
            layer_ids[existing_layer.name] = existing_layer.id
            print(f"  ℹ️  Layer already exists: {existing_layer.name}")
        else:
            layer = unf_service.create_layer(LayerCreate(**layer_data))
            layer_ids[layer.name] = layer.id
            print(f"  ✅ Created Layer: {layer.name}")

    # ========================================================================
    # 2. CREATE UNF ELEMENTS
    # ========================================================================
    print("\n🎯 Creating UNF Elements...")

    elements_data = [
        # Category Layer
        {
            "layer_name": "Category",
            "name": "Megatrends",
            "content": "Industries everywhere are transforming faster than ever before, driven by automation, digitalisation, and the pressure to operate more responsibly. The boundaries between physical and digital realities are blurring as technologies like AI, robotics, and Digital Twins redefine how work gets done. Yet progress brings complexity—data is abundant, but turning it into measurable improvement remains the next great challenge. The companies that can unify data, systems, and people will lead this new era of transformation.",
            "version": "1.0",
            "status": ElementStatus.APPROVED
        },
        {
            "layer_name": "Category",
            "name": "Problem",
            "content": "Today's industries must balance growth with responsibility. They need to deliver higher efficiency, quality, and safety while reducing waste and carbon impact. Despite rapid advances in technology, many organisations still struggle to connect their data and use it to drive real-world outcomes. Data often sits in silos, and digital tools are underutilised. The result is a widening gap between what companies know and what they can act on—a gap that limits progress toward a more responsible future.",
            "version": "1.0",
            "status": ElementStatus.APPROVED
        },
        # Vision Layer
        {
            "layer_name": "Vision",
            "name": "Vision Statement",
            "content": "A world where business and humanity thrive.",
            "version": "1.0",
            "status": ElementStatus.APPROVED
        },
        {
            "layer_name": "Vision",
            "name": "Principles",
            "content": """1. **Empowering** – We unlock human potential through technology and data.
2. **Entrepreneurial** – We act with curiosity, speed, and ownership to make progress.
3. **Real** – We stay grounded, practical, and focused on creating measurable impact.
4. **Responsible** – We make decisions that are good for people, profit, and the planet.
5. **Innovative** – We continuously improve how technology serves humanity.""",
            "version": "1.0",
            "status": ElementStatus.APPROVED
        },
        # Messaging Layer
        {
            "layer_name": "Messaging",
            "name": "Key Messages",
            "content": """Key Message 1
Headline: Transform data into real-world outcomes
Proof: Our Reality Technology connects physical and digital realities to improve performance and sustainability.
Benefit: Enables industries to act faster and more responsibly.

Key Message 2
Headline: Capture, create, and shape reality
Proof: We unify sensors, software, and AI to bridge the gap from data to action.
Benefit: Turns data into decisions that improve efficiency and safety.

Key Message 3
Headline: Empower industries to innovate responsibly
Proof: Our tools accelerate digital transformation without sacrificing quality or responsibility.
Benefit: Helps customers achieve progress that benefits people and the planet.

Key Message 4
Headline: The leader in Reality Technology
Proof: No other company combines robotics and software at this scale.
Benefit: Ensures trusted solutions that drive autonomy and efficiency worldwide.

Key Message 5
Headline: Shape reality
Proof: We deliver precision, innovation, and measurable results.
Benefit: Inspires confidence to build a world where business and humanity thrive.""",
            "version": "1.0",
            "status": ElementStatus.APPROVED
        },
        {
            "layer_name": "Messaging",
            "name": "Boilerplate",
            "content": "Hexagon is the global leader in Reality Technology. Driven by deep domain expertise across its divisions, Hexagon enables customers to shape reality with precision robotics and software that transform data into real-world outcomes for people, processes, and the planet. The company's portfolio unites physical and digital realities to create measurable improvements in productivity, quality, safety, and sustainability.",
            "version": "1.0",
            "status": ElementStatus.APPROVED
        }
    ]

    for elem_data in elements_data:
        layer_name = elem_data.pop("layer_name")
        elem_data["layer_id"] = layer_ids[layer_name]

        element = unf_service.create_element(ElementCreate(**elem_data))
        element_ids[element.name] = element.id
        print(f"  ✅ Created Element: {layer_name}/{element.name}")

    # ========================================================================
    # 3. CREATE BRAND VOICES
    # ========================================================================
    print("\n🎤 Creating Brand Voices...")

    # Corporate Voice v1.0
    corporate_voice = voice_service.create_voice(BrandVoiceCreate(
        name="Corporate Brand Voice",
        version="1.0",
        traits=["Confident", "Precise", "Grounded", "Optimistic", "Professional"],
        tone_rules=ToneRules(
            formality="medium-high",
            point_of_view="third-person",
            sentence_length="15-25 words average",
            voice="active voice required",
            contractions="allowed in informal materials",
            tense="present tense preferred"
        ),
        style_guardrails=StyleGuardrails(
            do=[
                "Use clear, declarative sentences",
                "Lead with evidence and measurable impact"
            ],
            dont=[
                "Overpromise or use emotionally charged language",
                "Use jargon that obscures meaning"
            ],
            punctuation="Avoid exclamation marks and rhetorical questions"
        ),
        lexicon=Lexicon(
            required=["When it has to be right", "We measure what matters"],
            banned=["Reality Technology", "Empowering an autonomous, sustainable future", "Smart Digital Reality"]
        ),
        readability_range="Standard – Grade 11-13",
        status=VoiceStatus.APPROVED
    ))
    voice_ids["corporate"] = corporate_voice.id
    print(f"  ✅ Created Voice: {corporate_voice.name}")

    # Product Voice v1.0 (inherits from Corporate)
    product_voice = voice_service.create_voice(BrandVoiceCreate(
        name="Product Division Voice",
        version="1.0",
        parent_voice_id=corporate_voice.id,
        traits=["Technical", "Concise", "Solution-oriented"],
        tone_rules=ToneRules(
            formality="medium",
            point_of_view="third-person or first-person plural",
            sentence_length="10-20 words average",
            contractions="allowed when clarity maintained"
        ),
        lexicon=Lexicon(
            required=["precision measurement", "autonomous systems", "sensor integration"],
            banned=[]  # Inherits from parent
        ),
        readability_range="Technical – Grade 13-15",
        status=VoiceStatus.APPROVED
    ))
    voice_ids["product"] = product_voice.id
    print(f"  ✅ Created Voice: {product_voice.name}")

    # ========================================================================
    # 4. CREATE STORY MODELS
    # ========================================================================
    print("\n📋 Creating Story Models...")

    # PAS Story Model
    pas_model = story_model_service.create_story_model(StoryModelCreate(
        name="PAS (Problem-Agitate-Solve)",
        description="Classic persuasion model: Problem → Agitate → Solve",
        sections=[
            Section(name="Problem", intent="Define the central challenge", order=1, required=True),
            Section(name="Agitate", intent="Illustrate urgency and consequences", order=2, required=True),
            Section(name="Solve", intent="Present the solution", order=3, required=True)
        ],
        constraints=[
            SectionConstraint(
                section_name="Problem",
                constraint_type="max_words",
                params={"max_words": 120}
            ),
            SectionConstraint(
                section_name="Solve",
                constraint_type="requires_element",
                params={"element_name": "Vision Statement"}
            )
        ]
    ))
    model_ids["pas"] = pas_model.id
    print(f"  ✅ Created Story Model: {pas_model.name}")

    # Inverted Pyramid Story Model
    pyramid_model = story_model_service.create_story_model(StoryModelCreate(
        name="Inverted Pyramid",
        description="Journalism structure: Most important information first",
        sections=[
            Section(name="Headline", intent="Capture the essence", order=1, required=True),
            Section(name="Lede", intent="Who, what, when, where, why", order=2, required=True),
            Section(name="Key Facts", intent="Supporting details", order=3, required=True),
            Section(name="Quote 1", intent="Executive perspective", order=4, required=True),
            Section(name="Quote 2", intent="Customer/external perspective", order=5, required=False),
            Section(name="Boilerplate", intent="Company description", order=6, required=True)
        ],
        constraints=[
            SectionConstraint(
                section_name="Headline",
                constraint_type="max_words",
                params={"max_words": 10}
            ),
            SectionConstraint(
                section_name="Lede",
                constraint_type="requires_fields",
                params={"fields": ["who", "what", "when", "where", "why"]}
            )
        ]
    ))
    model_ids["pyramid"] = pyramid_model.id
    print(f"  ✅ Created Story Model: {pyramid_model.name}")

    # Add section strategies to Inverted Pyramid model
    section_strategies = {
        'Headline': {
            'extraction_strategy': 'field_extraction',
            'field_path': 'headline',  # Extract from Key Messages element's 'headline' field
            'constraints': {'max_words': 10}
        },
        'Lede': {
            'extraction_strategy': 'composed',  # LLM composes from instance_data + Vision Statement
            'composition_sources': ['instance_data.who', 'instance_data.what', 'instance_data.when', 'instance_data.where', 'instance_data.why', 'element.Vision Statement'],
            'constraints': {}
        },
        'Key Facts': {
            'extraction_strategy': 'field_extraction',
            'field_path': 'proof',  # Extract 'proof' fields from Key Messages (select 3)
            'selection_count': 3,
            'constraints': {'format': 'markdown'}
        },
        'Quote 1': {
            'extraction_strategy': 'instance_data',  # Comes from instance_data.quote1_text, quote1_speaker, quote1_title
            'instance_fields': ['quote1_text', 'quote1_speaker', 'quote1_title'],
            'constraints': {}
        },
        'Quote 2': {
            'extraction_strategy': 'instance_data',  # Comes from instance_data.quote2_text, quote2_speaker, quote2_title
            'instance_fields': ['quote2_text', 'quote2_speaker', 'quote2_title'],
            'constraints': {}
        },
        'Boilerplate': {
            'extraction_strategy': 'full_content',  # Use full Boilerplate element
            'constraints': {}
        }
    }
    storage.update_one('story_models', pyramid_model.id, {
        'section_strategies': section_strategies
    })
    print(f"  ✅ Added section strategies to Inverted Pyramid")

    # ========================================================================
    # 5. CREATE DELIVERABLE TEMPLATES
    # ========================================================================
    print("\n📄 Creating Deliverable Templates...")

    # Brand Manifesto Template
    manifesto_template = template_service.create_template(TemplateCreate(
        name="Brand Manifesto",
        version="1.0",
        story_model_id=model_ids["pas"],
        default_voice_id=voice_ids["corporate"],
        instance_fields=[],  # No instance fields needed
        status=TemplateStatus.APPROVED
    ))
    template_ids["manifesto"] = manifesto_template.id
    print(f"  ✅ Created Template: {manifesto_template.name}")

    # Create section bindings for Manifesto
    template_service.create_section_binding(SectionBindingCreate(
        template_id=manifesto_template.id,
        section_name="Problem",
        section_order=1,
        element_ids=[element_ids["Problem"]]
    ))

    template_service.create_section_binding(SectionBindingCreate(
        template_id=manifesto_template.id,
        section_name="Agitate",
        section_order=2,
        element_ids=[element_ids["Megatrends"]]
    ))

    template_service.create_section_binding(SectionBindingCreate(
        template_id=manifesto_template.id,
        section_name="Solve",
        section_order=3,
        element_ids=[element_ids["Vision Statement"], element_ids["Principles"]]
    ))

    print(f"  ✅ Created {3} section bindings for Manifesto")

    # Press Release Template
    press_release_template = template_service.create_template(TemplateCreate(
        name="Press Release",
        version="1.0",
        story_model_id=model_ids["pyramid"],
        default_voice_id=voice_ids["corporate"],
        instance_fields=[
            InstanceField(name="who", field_type=InstanceFieldType.TEXT, required=True, description="Organization name"),
            InstanceField(name="what", field_type=InstanceFieldType.TEXT, required=True, description="Announcement"),
            InstanceField(name="when", field_type=InstanceFieldType.DATE, required=True, description="Date"),
            InstanceField(name="where", field_type=InstanceFieldType.TEXT, required=True, description="Location"),
            InstanceField(name="why", field_type=InstanceFieldType.TEXT, required=True, description="Reason/benefit"),
            InstanceField(name="quote1_text", field_type=InstanceFieldType.TEXT, required=True, description="Executive quote (full quote text)"),
            InstanceField(name="quote1_speaker", field_type=InstanceFieldType.TEXT, required=True, description="Executive name"),
            InstanceField(name="quote1_title", field_type=InstanceFieldType.TEXT, required=True, description="Executive title"),
            InstanceField(name="quote2_text", field_type=InstanceFieldType.TEXT, required=False, description="Customer quote (full quote text)"),
            InstanceField(name="quote2_speaker", field_type=InstanceFieldType.TEXT, required=False, description="Customer name"),
            InstanceField(name="quote2_title", field_type=InstanceFieldType.TEXT, required=False, description="Customer title"),
        ],
        status=TemplateStatus.APPROVED
    ))
    template_ids["press_release"] = press_release_template.id
    print(f"  ✅ Created Template: {press_release_template.name}")

    # Create section bindings for Press Release
    template_service.create_section_binding(SectionBindingCreate(
        template_id=press_release_template.id,
        section_name="Headline",
        section_order=1,
        element_ids=[element_ids["Key Messages"]]
    ))

    template_service.create_section_binding(SectionBindingCreate(
        template_id=press_release_template.id,
        section_name="Lede",
        section_order=2,
        element_ids=[element_ids["Vision Statement"]]
    ))

    template_service.create_section_binding(SectionBindingCreate(
        template_id=press_release_template.id,
        section_name="Key Facts",
        section_order=3,
        element_ids=[element_ids["Key Messages"]]
    ))

    template_service.create_section_binding(SectionBindingCreate(
        template_id=press_release_template.id,
        section_name="Quote 1",
        section_order=4,
        element_ids=[]  # Quotes come from instance_data, not UNF
    ))

    template_service.create_section_binding(SectionBindingCreate(
        template_id=press_release_template.id,
        section_name="Quote 2",
        section_order=5,
        element_ids=[]  # Quotes come from instance_data, not UNF
    ))

    template_service.create_section_binding(SectionBindingCreate(
        template_id=press_release_template.id,
        section_name="Boilerplate",
        section_order=6,
        element_ids=[element_ids["Boilerplate"]]
    ))

    print(f"  ✅ Created {6} section bindings for Press Release")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("✅ DUMMY DATA LOADED SUCCESSFULLY")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"  • Layers: {len(layer_ids)}")
    print(f"  • Elements: {len(element_ids)}")
    print(f"  • Brand Voices: {len(voice_ids)}")
    print(f"  • Story Models: {len(model_ids)}")
    print(f"  • Deliverable Templates: {len(template_ids)}")

    print(f"\n🎯 Created IDs:")
    print(f"\nLayers:")
    for name, id in layer_ids.items():
        print(f"  {name}: {id}")

    print(f"\nElements:")
    for name, id in element_ids.items():
        print(f"  {name}: {id}")

    print(f"\nVoices:")
    for name, id in voice_ids.items():
        print(f"  {name}: {id}")

    print(f"\nStory Models:")
    for name, id in model_ids.items():
        print(f"  {name}: {id}")

    print(f"\nTemplates:")
    for name, id in template_ids.items():
        print(f"  {name}: {id}")

    print(f"\n✅ Ready to create Deliverables and test workflows!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
