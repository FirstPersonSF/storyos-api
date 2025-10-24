"""
Migration script to add names to existing deliverables without names.

Options:
1. Add default names to existing deliverables
2. Delete deliverables without names
"""
import asyncio
from sqlalchemy import select, delete
from database import get_db, Deliverable

async def add_default_names():
    """Add default names to deliverables that don't have names"""
    async for db in get_db():
        # Get all deliverables
        result = await db.execute(select(Deliverable))
        deliverables = result.scalars().all()

        updated = 0
        for deliverable in deliverables:
            if not deliverable.name or deliverable.name.strip() == "":
                # Generate a default name based on template and created date
                default_name = f"Deliverable {deliverable.created_at.strftime('%Y-%m-%d %H:%M')}"
                deliverable.name = default_name
                updated += 1
                print(f"Updated deliverable {deliverable.id} with name: {default_name}")

        await db.commit()
        print(f"\n✅ Updated {updated} deliverables with default names")


async def delete_nameless_deliverables():
    """Delete all deliverables without names"""
    async for db in get_db():
        # Delete deliverables where name is None or empty
        stmt = delete(Deliverable).where(
            (Deliverable.name == None) | (Deliverable.name == "")
        )
        result = await db.execute(stmt)
        await db.commit()

        print(f"\n✅ Deleted {result.rowcount} deliverables without names")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/fix_deliverable_names.py --add-names    # Add default names")
        print("  python scripts/fix_deliverable_names.py --delete       # Delete nameless deliverables")
        sys.exit(1)

    action = sys.argv[1]

    if action == "--add-names":
        print("Adding default names to deliverables without names...\n")
        asyncio.run(add_default_names())
    elif action == "--delete":
        print("Deleting deliverables without names...\n")
        asyncio.run(delete_nameless_deliverables())
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
