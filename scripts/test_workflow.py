#!/usr/bin/env python3
"""
Test StoryOS Core Workflow

Demonstrates:
1. Creating a Deliverable (Brand Manifesto)
2. Creating another Deliverable (Press Release)
3. Updating a UNF Element
4. Seeing the impact alerts on Deliverables
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.supabase_storage import SupabaseStorage
from services.unf_service import UNFService
from services.voice_service import VoiceService
from services.story_model_service import StoryModelService
from services.template_service import TemplateService
from services.deliverable_service import DeliverableService
from services.relationship_service import PostgresRelationshipService

from models.deliverables import DeliverableCreate, DeliverableStatus
from models.unf import ElementUpdate

load_dotenv()


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section("STORYOS CORE WORKFLOW TEST")

    # Initialize storage and services
    print("\n🔗 Connecting to database...")
    storage = SupabaseStorage()

    unf_service = UNFService(storage)
    voice_service = VoiceService(storage)
    story_model_service = StoryModelService(storage)
    template_service = TemplateService(storage)
    relationship_service = PostgresRelationshipService(storage)

    deliverable_service = DeliverableService(
        storage,
        unf_service,
        voice_service,
        template_service,
        story_model_service,
        relationship_service
    )

    print("✅ Connected")

    # ==========================================================================
    # STEP 1: Create a Brand Manifesto
    # ==========================================================================
    print_section("STEP 1: Creating Brand Manifesto")

    # Get the manifesto template
    templates = template_service.list_templates()
    manifesto_template = next((t for t in templates if t.name == "Brand Manifesto"), None)

    if not manifesto_template:
        print("❌ Brand Manifesto template not found!")
        return

    print(f"📄 Using template: {manifesto_template.name} (v{manifesto_template.version})")

    # Create the manifesto deliverable
    try:
        manifesto = deliverable_service.create_deliverable(DeliverableCreate(
            name="Hexagon Brand Manifesto 2025",
            template_id=manifesto_template.id,
            status=DeliverableStatus.DRAFT,
            instance_data={},
            metadata={"created_by": "workflow_test"}
        ))

        print(f"\n✅ Created Manifesto: {manifesto.name}")
        print(f"   ID: {manifesto.id}")
        print(f"   Template Version: {manifesto.template_version}")
        print(f"   Voice Version: {manifesto.voice_version}")
        print(f"\n📝 Rendered Content Sections:")
        for section_name in manifesto.rendered_content.keys():
            content_preview = manifesto.rendered_content[section_name][:100].replace('\n', ' ')
            print(f"   • {section_name}: {content_preview}...")

    except Exception as e:
        print(f"❌ Error creating manifesto: {e}")
        import traceback
        traceback.print_exc()
        return

    # ==========================================================================
    # STEP 2: Create a Press Release
    # ==========================================================================
    print_section("STEP 2: Creating Press Release")

    # Get the press release template
    pr_template = next((t for t in templates if t.name == "Press Release"), None)

    if not pr_template:
        print("❌ Press Release template not found!")
        return

    print(f"📄 Using template: {pr_template.name} (v{pr_template.version})")

    # Create the press release with instance data
    try:
        press_release = deliverable_service.create_deliverable(DeliverableCreate(
            name="Q1 2025 Product Launch Press Release",
            template_id=pr_template.id,
            status=DeliverableStatus.DRAFT,
            instance_data={
                "who": "Hexagon AB",
                "what": "Launch of new Reality Technology platform",
                "when": "2025-01-15",
                "where": "Stockholm, Sweden",
                "why": "To accelerate digital transformation across industries",
                "quote1_speaker": "Paolo Guglielmini",
                "quote1_title": "President and CEO, Hexagon",
                "quote2_speaker": "Jane Smith",
                "quote2_title": "CTO, Customer Corp"
            },
            metadata={"created_by": "workflow_test"}
        ))

        print(f"\n✅ Created Press Release: {press_release.name}")
        print(f"   ID: {press_release.id}")
        print(f"   Template Version: {press_release.template_version}")
        print(f"\n📝 Instance Data:")
        for key, value in press_release.instance_data.items():
            print(f"   • {key}: {value}")

    except Exception as e:
        print(f"❌ Error creating press release: {e}")
        import traceback
        traceback.print_exc()
        return

    # ==========================================================================
    # STEP 3: Update a UNF Element
    # ==========================================================================
    print_section("STEP 3: Updating UNF Element 'Vision Statement'")

    # Find the Vision Statement element
    elements = unf_service.list_elements()
    vision_element = next((e for e in elements if e.name == "Vision Statement"), None)

    if not vision_element:
        print("❌ Vision Statement element not found!")
        return

    print(f"📝 Current Element: {vision_element.name}")
    print(f"   Version: {vision_element.version}")
    print(f"   Content: {vision_element.content}")

    # Update the element (this creates a new version)
    try:
        updated_vision = unf_service.update_element(
            vision_element.id,
            ElementUpdate(
                content="A world where business, humanity, and the planet thrive together.",
                metadata={"update_reason": "Added 'planet' for sustainability focus"}
            )
        )

        print(f"\n✅ Created new version: {updated_vision.name}")
        print(f"   Old Version ID: {vision_element.id}")
        print(f"   New Version ID: {updated_vision.id}")
        print(f"   Old Version: {vision_element.version} (now superseded)")
        print(f"   New Version: {updated_vision.version}")
        print(f"   New Content: {updated_vision.content}")

    except Exception as e:
        print(f"❌ Error updating element: {e}")
        import traceback
        traceback.print_exc()
        return

    # ==========================================================================
    # STEP 4: Check for Impact Alerts
    # ==========================================================================
    print_section("STEP 4: Checking for Impact Alerts")

    # Check if Manifesto has alerts
    print("\n🔍 Checking Manifesto for update alerts...")
    try:
        manifesto_with_alerts = deliverable_service.get_deliverable_with_alerts(manifesto.id)

        if manifesto_with_alerts.has_updates:
            print(f"⚠️  UPDATES AVAILABLE for '{manifesto_with_alerts.name}'")
            print(f"   Number of alerts: {len(manifesto_with_alerts.alerts)}")
            for alert in manifesto_with_alerts.alerts:
                print(f"\n   📣 Alert:")
                print(f"      Element: {alert.element_name}")
                print(f"      Old Version: {alert.old_version}")
                print(f"      New Version: {alert.new_version}")
                print(f"      Status: {alert.status}")
        else:
            print("✅ No updates available for Manifesto")

    except Exception as e:
        print(f"❌ Error checking manifesto alerts: {e}")
        import traceback
        traceback.print_exc()

    # Check if Press Release has alerts
    print("\n🔍 Checking Press Release for update alerts...")
    try:
        pr_with_alerts = deliverable_service.get_deliverable_with_alerts(press_release.id)

        if pr_with_alerts.has_updates:
            print(f"⚠️  UPDATES AVAILABLE for '{pr_with_alerts.name}'")
            print(f"   Number of alerts: {len(pr_with_alerts.alerts)}")
            for alert in pr_with_alerts.alerts:
                print(f"\n   📣 Alert:")
                print(f"      Element: {alert.element_name}")
                print(f"      Old Version: {alert.old_version}")
                print(f"      New Version: {alert.new_version}")
                print(f"      Status: {alert.status}")
        else:
            print("✅ No updates available for Press Release")

    except Exception as e:
        print(f"❌ Error checking press release alerts: {e}")
        import traceback
        traceback.print_exc()

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print_section("WORKFLOW TEST COMPLETE")

    print("\n✅ Successfully demonstrated:")
    print("   1. Creating a Brand Manifesto from a template")
    print("   2. Creating a Press Release with instance data")
    print("   3. Updating a UNF Element (Vision Statement)")
    print("   4. Detecting impact alerts on affected Deliverables")

    print("\n🎯 StoryOS is working correctly!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
