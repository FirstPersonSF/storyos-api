"""
Cleanup Test Data Script

Removes test deliverables and superseded element versions,
leaving a clean database for demos.

Usage:
    python3 scripts/cleanup_test_data.py

What it does:
1. Deletes all deliverables (can be recreated via demo page)
2. Deletes all superseded UNF element versions
3. Keeps all approved elements (current versions only)
4. Keeps all templates, voices, and story models
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
print("CLEANUP TEST DATA")
print("=" * 80)

# Step 1: Show current state
print("\n[BEFORE CLEANUP]")
deliverables = storage.get_many('deliverables')
elements = storage.get_many('unf_elements')

print(f"Deliverables: {len(deliverables)}")
print(f"UNF Elements: {len(elements)}")

approved = [e for e in elements if e['status'] == 'approved']
draft = [e for e in elements if e['status'] == 'draft']
superseded = [e for e in elements if e['status'] == 'superseded']

print(f"  - Approved: {len(approved)}")
print(f"  - Draft: {len(draft)}")
print(f"  - Superseded: {len(superseded)}")

# Step 2: Confirm deletion
print("\n" + "=" * 80)
print("This will DELETE:")
print(f"  - {len(deliverables)} deliverables")
print(f"  - {len(superseded)} superseded element versions")
print(f"  - {len(draft)} draft element versions")
print("\nThis will KEEP:")
print(f"  - {len(approved)} approved elements (current versions)")
print("  - All templates, voices, and story models")
print("=" * 80)

confirm = input("\nProceed with cleanup? (yes/no): ")

if confirm.lower() != 'yes':
    print("❌ Cleanup cancelled")
    exit(0)

# Step 3: Delete deliverables
print("\n[Step 1] Deleting deliverables...")
deleted_deliverables = 0

for d in deliverables:
    try:
        storage.client.table('deliverables').delete().eq('id', d['id']).execute()
        deleted_deliverables += 1
    except Exception as e:
        print(f"  ⚠️  Failed to delete deliverable {d['id']}: {str(e)}")

print(f"✅ Deleted {deleted_deliverables} deliverables")

# Step 4: Delete superseded elements
print("\n[Step 2] Deleting superseded element versions...")
deleted_superseded = 0

for elem in superseded:
    try:
        storage.client.table('unf_elements').delete().eq('id', elem['id']).execute()
        deleted_superseded += 1
    except Exception as e:
        print(f"  ⚠️  Failed to delete element {elem['id']}: {str(e)}")

print(f"✅ Deleted {deleted_superseded} superseded element versions")

# Step 5: Delete draft elements
print("\n[Step 3] Deleting draft element versions...")
deleted_drafts = 0

for elem in draft:
    try:
        storage.client.table('unf_elements').delete().eq('id', elem['id']).execute()
        deleted_drafts += 1
    except Exception as e:
        print(f"  ⚠️  Failed to delete element {elem['id']}: {str(e)}")

print(f"✅ Deleted {deleted_drafts} draft element versions")

# Step 6: Show final state
print("\n" + "=" * 80)
print("[AFTER CLEANUP]")

deliverables_after = storage.get_many('deliverables')
elements_after = storage.get_many('unf_elements')

print(f"Deliverables: {len(deliverables_after)}")
print(f"UNF Elements: {len(elements_after)}")

approved_after = [e for e in elements_after if e['status'] == 'approved']
print(f"  - Approved: {len(approved_after)}")

print("\nRemaining approved elements:")
for e in approved_after:
    print(f"  - {e['name']} v{e['version']}")

print("\n" + "=" * 80)
print("✅ CLEANUP COMPLETE")
print("=" * 80)
print("\nDatabase is now clean and ready for demos!")
print("You can create fresh deliverables via:")
print("  - Demo page: http://localhost:5173/demo")
print("  - Test scripts: python3 test_case_1.py")
