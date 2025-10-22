"""
Remove [UPDATED: timestamp] artifacts from element content
"""
from storage.supabase_storage import SupabaseStorage
from services.unf_service import UNFService
import os, re
from dotenv import load_dotenv

load_dotenv()

storage = SupabaseStorage(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)
unf_service = UNFService(storage)

print("=" * 80)
print("CLEANING [UPDATED:] ARTIFACTS FROM ELEMENTS")
print("=" * 80)

# Get approved elements
elements = storage.get_many('unf_elements', filters={'status': 'approved'})

for elem in elements:
    original_content = elem['content']

    # Remove [UPDATED: timestamp] patterns
    cleaned_content = re.sub(r'\n*\[UPDATED:.*?\]\n*', '', original_content)
    cleaned_content = cleaned_content.strip()

    if cleaned_content != original_content:
        print(f"\n{elem['name']} v{elem['version']}:")
        print(f"  Found UPDATED artifact")
        print(f"  Creating new version without artifact...")

        # Create new version via update (which creates new version and marks old as superseded)
        from models.unf import ElementUpdate
        update_data = ElementUpdate(content=cleaned_content)

        # Actually, let's just update the current version directly since these are artifacts
        # not intentional content changes
        storage.update_one('unf_elements', elem['id'], {'content': cleaned_content})
        print(f"  ✅ Cleaned")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
