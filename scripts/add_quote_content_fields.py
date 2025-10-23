#!/usr/bin/env python3
"""
Add quote content fields to Press Release template

Quotes should be instance data (actual text from real people),
not extracted from reusable Elements.
"""
import os
import sys
import ujson as json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.supabase_storage import SupabaseStorage

# Load environment variables
load_dotenv()

PRESS_RELEASE_TEMPLATE_ID = "06c9b4bd-c188-475f-b972-dc1e92998cfb"

def add_quote_fields():
    """Add quote content fields to Press Release template"""
    print("=" * 80)
    print("Add Quote Content Fields to Press Release Template")
    print("=" * 80)
    print()

    # Initialize storage
    storage = SupabaseStorage()

    # Get current template
    print(f"Fetching Press Release template (ID: {PRESS_RELEASE_TEMPLATE_ID})...")
    template = storage.get_one("deliverable_templates", PRESS_RELEASE_TEMPLATE_ID)

    if not template:
        print(f"❌ ERROR: Template not found!")
        return False

    print(f"✅ Found template: {template.get('name')}")

    # Get current instance fields (parse if it's a JSON string)
    instance_fields = template.get('instance_fields', [])
    if isinstance(instance_fields, str):
        instance_fields = json.loads(instance_fields)

    print(f"\nCurrent instance fields: {len(instance_fields)}")
    for field in instance_fields:
        print(f"  • {field['name']} ({field['field_type']}) - {field['description']}")

    # Check if quote content fields already exist
    has_quote1_content = any(f['name'] == 'quote1_content' for f in instance_fields)
    has_quote2_content = any(f['name'] == 'quote2_content' for f in instance_fields)

    if has_quote1_content and has_quote2_content:
        print("\n⚠️  Quote content fields already exist!")
        return True

    # Add quote content fields after quote speaker/title fields
    new_fields = []
    for field in instance_fields:
        new_fields.append(field)

        # After quote1_title, add quote1_content
        if field['name'] == 'quote1_title' and not has_quote1_content:
            new_fields.append({
                "name": "quote1_content",
                "field_type": "text",
                "required": True,
                "description": "Quote text from executive",
                "default_value": None
            })

        # After quote2_title, add quote2_content
        if field['name'] == 'quote2_title' and not has_quote2_content:
            new_fields.append({
                "name": "quote2_content",
                "field_type": "text",
                "required": False,
                "description": "Quote text from customer",
                "default_value": None
            })

    # Update template
    print(f"\nAdding quote content fields...")
    success = storage.update_one(
        "deliverable_templates",
        PRESS_RELEASE_TEMPLATE_ID,
        {"instance_fields": json.dumps(new_fields)}
    )

    if success:
        print("\n✅ Migration completed successfully!")
        print("\nUpdated instance fields:")
        for field in new_fields:
            print(f"  • {field['name']} ({field['field_type']}) - {field['description']}")

        print("\n" + "=" * 80)
        print("Next Steps:")
        print("  1. Update quote extraction logic to use instance data")
        print("  2. Update frontend to show quote content fields")
        print("  3. Test with a new press release deliverable")
        print("=" * 80)
        return True
    else:
        print("\n❌ Migration failed!")
        return False


if __name__ == "__main__":
    try:
        success = add_quote_fields()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
