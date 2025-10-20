"""
Update UNF Elements to include instance field placeholders

This creates new versions of elements that need instance field substitution
"""
from storage.supabase_storage import SupabaseStorage
from services.unf_service import UNFService
from models.unf import ElementUpdate
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize storage and service
storage = SupabaseStorage(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)
unf_service = UNFService(storage)

print("=" * 80)
print("UPDATING UNF ELEMENTS WITH INSTANCE FIELD PLACEHOLDERS")
print("=" * 80)

# Get all approved elements
elements = storage.get_many('unf_elements', filters={'status': 'approved'})

# Find Vision Statement (used in Lede)
vision = next((e for e in elements if e['name'] == 'Vision Statement'), None)

if vision:
    print(f"\n[1] Updating Vision Statement v{vision['version']}...")

    # Create new content with instance field placeholders
    new_content = """
{where}, {when} — {who} {what}.

{why}

Vision: A world where business, humanity, and the planet thrive together.
""".strip()

    print(f"   Old content: {vision['content'][:80]}...")
    print(f"   New content: {new_content[:80]}...")

    # Update the element (creates new version)
    updated = unf_service.update_element(
        vision['id'],
        ElementUpdate(content=new_content)
    )

    print(f"   ✅ Created Vision Statement v{updated.version}")
    print(f"   ✅ Old version (v{vision['version']}) marked as superseded")
else:
    print("❌ Vision Statement not found")

# Find Boilerplate (used in Boilerplate section)
boilerplate = next((e for e in elements if e['name'] == 'Boilerplate'), None)

if boilerplate:
    print(f"\n[2] Updating Boilerplate v{boilerplate['version']}...")

    # Create proper boilerplate content
    new_content = """
About {who}:
Hexagon is a global leader in digital reality solutions, combining sensor, software and autonomous technologies. We put data to work to boost efficiency, productivity, quality and safety across industrial, manufacturing, infrastructure, public sector, and mobility applications.
""".strip()

    print(f"   Old content: {boilerplate['content'][:80]}...")
    print(f"   New content: {new_content[:80]}...")

    # Update the element
    updated = unf_service.update_element(
        boilerplate['id'],
        ElementUpdate(content=new_content)
    )

    print(f"   ✅ Created Boilerplate v{updated.version}")
    print(f"   ✅ Old version (v{boilerplate['version']}) marked as superseded")
else:
    print("❌ Boilerplate not found")

# Approve the new versions
print(f"\n[3] Approving new versions...")

elements_updated = storage.get_many('unf_elements', filters={'status': 'draft'})
for elem in elements_updated:
    if elem['name'] in ['Vision Statement', 'Boilerplate']:
        unf_service.approve_element(elem['id'])
        print(f"   ✅ Approved {elem['name']} v{elem['version']}")

print("\n" + "=" * 80)
print("✅ ELEMENT UPDATES COMPLETE")
print("=" * 80)
