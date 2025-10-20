"""
Update template bindings to use latest element versions
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
print("UPDATING TEMPLATE BINDINGS TO LATEST ELEMENT VERSIONS")
print("=" * 80)

# Get Press Release template
templates = storage.get_many('deliverable_templates')
pr_template = next((t for t in templates if 'Press Release' in t['name']), None)

if not pr_template:
    print("❌ Press Release template not found")
    exit(1)

# Get bindings
bindings = storage.get_many('template_section_bindings', filters={'template_id': pr_template['id']})

# Get all elements
all_elements = storage.get_many('unf_elements')

# Find latest approved versions by name
element_map = {}
for elem in all_elements:
    if elem['status'] == 'approved':
        name = elem['name']
        if name not in element_map or elem['version'] > element_map[name]['version']:
            element_map[name] = elem

print(f"\nLatest approved elements:")
for name, elem in sorted(element_map.items()):
    print(f"  {name}: {elem['id']} (v{elem['version']})")

print(f"\n\nUpdating bindings...")

for binding in bindings:
    section_name = binding['section_name']
    elem_ids = binding.get('element_ids', [])

    updated_ids = []
    changed = False

    for elem_id in elem_ids:
        old_elem = storage.get_one('unf_elements', elem_id)
        if old_elem:
            # Find latest version of this element
            latest = element_map.get(old_elem['name'])
            if latest and latest['id'] != elem_id:
                print(f"\n  {section_name}: {old_elem['name']} v{old_elem['version']} → v{latest['version']}")
                print(f"    Old ID: {elem_id}")
                print(f"    New ID: {latest['id']}")
                updated_ids.append(latest['id'])
                changed = True
            else:
                updated_ids.append(elem_id)
        else:
            updated_ids.append(elem_id)

    if changed:
        storage.update_one(
            'template_section_bindings',
            binding['id'],
            {'element_ids': updated_ids}
        )
        print(f"    ✅ Updated binding")

print("\n" + "=" * 80)
print("✅ TEMPLATE BINDINGS UPDATED")
print("=" * 80)
