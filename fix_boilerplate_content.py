"""
Remove meta-commentary from Boilerplate v1.5 element content
"""
from storage.supabase_storage import SupabaseStorage
from uuid import UUID
import os
from dotenv import load_dotenv

load_dotenv()

storage = SupabaseStorage()

# Get Boilerplate v1.5
boilerplate_id = UUID('e19ab470-1f95-4759-abe4-df7fe95353f2')
element = storage.get_one('unf_elements', boilerplate_id)

print("=" * 80)
print("FIXING BOILERPLATE CONTENT")
print("=" * 80)

print(f"\nCurrent content length: {len(element['content'])} chars")
print(f"\nCurrent last 300 chars:")
print("..." + element['content'][-300:])

# Remove the meta-commentary lines
cleaned_content = element['content']

# Remove the problematic lines
lines_to_remove = [
    "UPDATED VERSION: This boilerplate now includes updated employee count and revenue figures.",
    "UPDATED CONTENT v1.1 - New information added."
]

for line in lines_to_remove:
    cleaned_content = cleaned_content.replace(line, "")

# Clean up extra whitespace
cleaned_content = cleaned_content.strip()

print(f"\n{'=' * 80}")
print("CLEANED CONTENT")
print("=" * 80)

print(f"\nCleaned content length: {len(cleaned_content)} chars")
print(f"\nCleaned last 300 chars:")
print("..." + cleaned_content[-300:])

# Update the element
print(f"\n{'=' * 80}")
print("UPDATING ELEMENT")
print("=" * 80)

storage.update_one(
    'unf_elements',
    boilerplate_id,
    {'content': cleaned_content}
)

print("\n✓ Boilerplate element updated successfully!")

# Verify
updated_element = storage.get_one('unf_elements', boilerplate_id)
print(f"\nVerified content length: {len(updated_element['content'])} chars")

if "UPDATED VERSION" not in updated_element['content'] and "UPDATED CONTENT" not in updated_element['content']:
    print("✓ Meta-commentary successfully removed!")
else:
    print("✗ WARNING: Meta-commentary still present")
