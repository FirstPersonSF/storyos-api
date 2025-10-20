#!/usr/bin/env python3
"""
Clear all data from StoryOS tables
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

print("=" * 80)
print("CLEARING ALL STORYOS DATA")
print("=" * 80)

supabase_url = os.getenv('SUPABASE_URL')
service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

client = create_client(supabase_url, service_key)

# List of tables to clear (in order due to foreign keys)
tables = [
    "element_dependencies",
    "deliverables",
    "template_section_bindings",
    "deliverable_templates",
    "story_models",
    "brand_voices",
    "unf_elements",
    "unf_layers"
]

for table in tables:
    print(f"\n🗑️  Clearing table: {table}")
    try:
        # Delete all rows
        # For element_dependencies, use element_id instead of id
        if table == "element_dependencies":
            result = client.table(table).delete().neq('element_id', '00000000-0000-0000-0000-000000000000').execute()
        else:
            result = client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        count = len(result.data) if result.data else 0
        print(f"  ✅ Deleted {count} rows")
    except Exception as e:
        print(f"  ⚠️  Error (table may be empty): {e}")

print("\n" + "=" * 80)
print("✅ ALL DATA CLEARED")
print("=" * 80)
