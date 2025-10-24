"""
Fix Manifesto template section bindings

The Manifesto template should have bindings to:
- Problem → Problem element
- Agitate → Megatrends element
- Solve → Vision Statement + Principles elements
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from storage.supabase_storage import SupabaseStorage

# Load environment
load_dotenv()

storage = SupabaseStorage()

print("=" * 80)
print("FIXING MANIFESTO TEMPLATE BINDINGS")
print("=" * 80)

# Get Manifesto template
templates = storage.get_many('deliverable_templates')
manifesto_templates = [t for t in templates if 'Manifesto' in t['name']]

if not manifesto_templates:
    print("❌ No Manifesto template found")
    sys.exit(1)

manifesto = manifesto_templates[0]
print(f"\n✅ Found Manifesto template: {manifesto['name']} (ID: {manifesto['id']})")

# Get all UNF elements
elements = storage.get_many('unf_elements')
element_map = {e['name']: e['id'] for e in elements}

print(f"\n📚 Available UNF Elements ({len(elements)}):")
for name in sorted(element_map.keys()):
    print(f"  - {name}")

# Check for required elements
required_elements = ['Problem', 'Megatrends', 'Vision Statement', 'Principles']
missing = [e for e in required_elements if e not in element_map]

if missing:
    print(f"\n❌ Missing required elements: {', '.join(missing)}")
    sys.exit(1)

print(f"\n✅ All required elements found")

# Get current bindings
bindings = storage.get_many('template_section_bindings')
manifesto_bindings = [b for b in bindings if b['template_id'] == manifesto['id']]

print(f"\n📋 Current Manifesto bindings ({len(manifesto_bindings)}):")
for binding in sorted(manifesto_bindings, key=lambda x: x.get('order', 999)):
    elem_names = []
    for elem_id in binding.get('element_ids', []):
        elem = next((e for e in elements if e['id'] == elem_id), None)
        elem_names.append(elem['name'] if elem else f"Unknown ({elem_id})")

    print(f"  {binding['section_name']}: {', '.join(elem_names) if elem_names else 'NO ELEMENTS'}")

# Delete existing bindings
if manifesto_bindings:
    print(f"\n🗑️  Deleting {len(manifesto_bindings)} existing bindings...")
    for binding in manifesto_bindings:
        storage.delete_one('template_section_bindings', binding['id'])
    print("  ✅ Deleted")

# Create correct bindings
print(f"\n➕ Creating correct bindings...")

new_bindings = [
    {
        'template_id': manifesto['id'],
        'section_name': 'Problem',
        'order': 1,
        'element_ids': [element_map['Problem']]
    },
    {
        'template_id': manifesto['id'],
        'section_name': 'Agitate',
        'order': 2,
        'element_ids': [element_map['Megatrends']]
    },
    {
        'template_id': manifesto['id'],
        'section_name': 'Solve',
        'order': 3,
        'element_ids': [element_map['Vision Statement'], element_map['Principles']]
    }
]

for binding_data in new_bindings:
    binding = storage.create_one('template_section_bindings', binding_data)
    elem_names = []
    for elem_id in binding_data['element_ids']:
        elem = next((e for e in elements if e['id'] == elem_id), None)
        elem_names.append(elem['name'] if elem else f"Unknown ({elem_id})")

    print(f"  ✅ {binding_data['section_name']}: {', '.join(elem_names)}")

# Verify
final_bindings = [b for b in storage.get_many('template_section_bindings') if b['template_id'] == manifesto['id']]

print("\n" + "=" * 80)
print("✅ MANIFESTO BINDINGS FIXED")
print("=" * 80)
print(f"\nFinal bindings ({len(final_bindings)}):")
for binding in sorted(final_bindings, key=lambda x: x.get('order', 999)):
    elem_names = []
    for elem_id in binding.get('element_ids', []):
        elem = next((e for e in elements if e['id'] == elem_id), None)
        elem_names.append(elem['name'] if elem else f"Unknown ({elem_id})")

    print(f"  {binding['section_name']}: {', '.join(elem_names)}")
