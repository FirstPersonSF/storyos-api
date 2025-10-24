"""
Fix deliverables with NULL names in the database
"""
import os
from dotenv import load_dotenv
from storage.postgres_storage import PostgresStorage

# Load environment variables
load_dotenv()

def fix_null_names():
    storage = PostgresStorage()

    # Find deliverables with NULL names
    results = storage.execute_query("""
        SELECT id, name, template_id, status, created_at
        FROM deliverables
        WHERE name IS NULL
    """)

    if not results:
        print("No deliverables with NULL names found")
        return

    print(f"Found {len(results)} deliverables with NULL names:")
    for row in results:
        print(f"  ID: {row['id']}")
        print(f"  Template ID: {row['template_id']}")
        print(f"  Status: {row['status']}")
        print(f"  Created: {row['created_at']}")
        print()

    # Ask user what to do
    action = input("Delete these deliverables? (y/n): ").strip().lower()

    if action == 'y':
        for row in results:
            deliverable_id = row['id']
            print(f"Deleting deliverable {deliverable_id}...")
            storage.execute_query(
                "DELETE FROM deliverables WHERE id = %s",
                (deliverable_id,),
                fetch="none"
            )

        print(f"\nDeleted {len(results)} deliverables with NULL names")
    else:
        print("No changes made")

if __name__ == '__main__':
    fix_null_names()
