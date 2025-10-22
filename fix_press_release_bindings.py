"""
Fix Press Release template bindings to use latest approved element versions
and add content templates for instance field injection
"""
from storage.supabase_storage import SupabaseStorage
import os
from dotenv import load_dotenv

load_dotenv()

storage = SupabaseStorage(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("FIXING PRESS RELEASE TEMPLATE BINDINGS")
print("=" * 80)

# Get Press Release template
templates = storage.get_many('deliverable_templates')
pr_template = next((t for t in templates if 'Press Release' in t['name']), None)

if not pr_template:
    print("❌ Press Release template not found")
    exit(1)

print(f"\nTemplate: {pr_template['name']} ({pr_template['id']})")

# Get all approved elements
all_elements = storage.get_many('unf_elements', filters={'status': 'approved'})

# Find latest versions by name
element_map = {}
for elem in all_elements:
    name = elem['name']
    if name not in element_map or elem['version'] > element_map[name]['version']:
        element_map[name] = elem

print(f"\nLatest approved elements:")
for name, elem in sorted(element_map.items()):
    print(f"  {name}: {elem['id']} (v{elem['version']})")

# Define the correct section → element mapping for Press Release
# Based on typical press release structure
section_element_map = {
    'Headline': 'Key Messages',      # Extract headline from key messages
    'Lede': 'Vision Statement',      # Lede with instance fields (who, what, when, where, why)
    'Key Facts': 'Key Messages',     # Key facts/messages
    'Quote 1': 'Principles',         # First quote from principles
    'Quote 2': 'Problem',            # Second quote from problem statement
    'Boilerplate': 'Boilerplate'     # About company section
}

# Define content templates for sections that need instance field injection
content_templates = {
    'Lede': '{content}',  # Vision Statement already has {where}, {when}, {who}, {what}, {why} placeholders
    'Boilerplate': '{content}',  # Boilerplate already has {who} placeholder
    'Quote 1': '"{content}" — {quote1_speaker}, {quote1_title}',  # Format quote with speaker
    'Quote 2': '"{content}" — {quote2_speaker}, {quote2_title}'   # Format second quote
}

print(f"\n\nUpdating bindings...")

# Get bindings
bindings = storage.get_many('template_section_bindings', filters={'template_id': pr_template['id']})

for binding in bindings:
    section_name = binding['section_name']

    if section_name in section_element_map:
        element_name = section_element_map[section_name]

        if element_name in element_map:
            new_elem = element_map[element_name]
            new_elem_ids = [new_elem['id']]
            old_elem_ids = binding.get('element_ids', [])

            # Get content template if defined
            content_template = content_templates.get(section_name)

            # Only update element_ids (content_template column doesn't exist in this table)
            if old_elem_ids != new_elem_ids:
                print(f"\n  Updating {section_name}:")
                print(f"    Old element: {old_elem_ids}")
                print(f"    New element: {new_elem_ids} ({element_name} v{new_elem['version']})")

                storage.update_one(
                    'template_section_bindings',
                    binding['id'],
                    {'element_ids': new_elem_ids}
                )
                print(f"    ✅ Updated")
            else:
                print(f"\n  {section_name}: Already up to date ({element_name} v{new_elem['version']})")
        else:
            print(f"\n  ⚠️  {section_name}: Element '{element_name}' not found")
    else:
        print(f"\n  ⚠️  {section_name}: No mapping defined")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
