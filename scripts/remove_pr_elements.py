"""
Remove PR-specific UNF elements that should be instance_data instead

These elements should NOT be in the UNF as they are deliverable-specific:
- PR Headline
- PR Lede
- PR Key Facts
- PR Quote - Executive
- PR Quote - Customer

They should be composed from instance_data fields instead.
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
print("REMOVING PR-SPECIFIC UNF ELEMENTS")
print("=" * 80)

# Get all UNF elements
elements = storage.get_many('unf_elements')

# Find PR-specific elements
pr_element_names = [
    'PR Headline',
    'PR Lede',
    'PR Key Facts',
    'PR Quote - Executive',
    'PR Quote - Customer'
]

pr_elements = [e for e in elements if e['name'] in pr_element_names]

print(f"\nFound {len(pr_elements)} PR-specific elements to remove:")
for elem in pr_elements:
    print(f"  - {elem['name']} (ID: {elem['id']})")

# Check if any template bindings reference these elements
print("\nChecking template bindings...")
bindings = storage.get_many('template_section_bindings')
affected_bindings = [b for b in bindings if b['element_id'] in [e['id'] for e in pr_elements]]

if affected_bindings:
    print(f"\nWARNING: Found {len(affected_bindings)} template bindings that reference these elements:")
    for binding in affected_bindings:
        print(f"  - Section '{binding['section_name']}' → Element ID {binding['element_id']}")
    print("\nThese bindings will need to be updated to reference instance_data instead.")

# Remove the elements
print("\nRemoving elements...")
for elem in pr_elements:
    try:
        storage.delete_one('unf_elements', elem['id'])
        print(f"  ✓ Removed: {elem['name']}")
    except Exception as e:
        print(f"  ✗ Failed to remove {elem['name']}: {e}")

# Verify removal
remaining_elements = storage.get_many('unf_elements')
remaining_pr = [e for e in remaining_elements if e['name'] in pr_element_names]

print("\n" + "=" * 80)
if not remaining_pr:
    print("✅ ALL PR-SPECIFIC ELEMENTS REMOVED")
    print("=" * 80)
    print(f"\nRemaining UNF elements: {len(remaining_elements)}")
    for elem in sorted(remaining_elements, key=lambda x: x['name']):
        print(f"  - {elem['name']}")
else:
    print("✗ SOME ELEMENTS STILL REMAIN")
    print("=" * 80)
    for elem in remaining_pr:
        print(f"  - {elem['name']} (ID: {elem['id']})")
