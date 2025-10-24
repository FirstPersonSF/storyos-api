"""
Update template bindings to use approved v1.5 elements

This script directly updates the database to fix Lede and Boilerplate bindings
that were pointing to superseded element versions.
"""
import sys
import os
from uuid import UUID
from dotenv import load_dotenv
from storage.postgres_storage import PostgresStorage

# Load environment variables
load_dotenv()

# Initialize storage
storage = PostgresStorage()

# Template ID (Press Release template)
template_id = UUID('06c9b4bd-c188-475f-b972-dc1e92998cfb')

# New approved element IDs (v1.5)
new_vision_id = UUID('5882a148-cdd6-4a39-a718-1ca36ccdfcfc')  # Vision Statement v1.5
new_boilerplate_id = UUID('e19ab470-1f95-4759-abe4-df7fe95353f2')  # Boilerplate v1.5

print("=" * 80)
print("UPDATING TEMPLATE BINDINGS")
print("=" * 80)

# Get all bindings for this template
bindings = storage.get_many('public.template_section_bindings', filters={'template_id': template_id})

print(f"\nFound {len(bindings)} bindings for template {template_id}")

for binding in bindings:
    print(f"\n[{binding['section_name']}]")
    print(f"  Current element_ids: {binding['element_ids']}")

    if binding['section_name'] == 'Lede':
        print(f"  → Updating to Vision Statement v1.5: {new_vision_id}")

        # Update the binding
        storage.update(
            'public.template_section_bindings',
            binding['id'],
            {'element_ids': [str(new_vision_id)]}
        )
        print("  ✓ Updated")

    elif binding['section_name'] == 'Boilerplate':
        print(f"  → Updating to Boilerplate v1.5: {new_boilerplate_id}")

        # Update the binding
        storage.update(
            'public.template_section_bindings',
            binding['id'],
            {'element_ids': [str(new_boilerplate_id)]}
        )
        print("  ✓ Updated")

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

# Verify updates
updated_bindings = storage.get_many('public.template_section_bindings', filters={'template_id': template_id})

for binding in updated_bindings:
    if binding['section_name'] in ['Lede', 'Boilerplate']:
        print(f"\n[{binding['section_name']}]")
        print(f"  element_ids: {binding['element_ids']}")

        # Check if element exists and is approved
        if binding['element_ids']:
            element_id = binding['element_ids'][0]
            element = storage.get_one('public.unf_elements', UUID(element_id))
            if element:
                print(f"  Element: {element['name']} v{element['version']}")
                print(f"  Status: {element['status']}")

                if element['status'] == 'approved':
                    print("  ✓ Element is approved")
                else:
                    print(f"  ✗ WARNING: Element status is '{element['status']}'")

print("\n✓ Binding update complete!")
