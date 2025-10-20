#!/usr/bin/env python3
"""
Verify that the StoryOS schema was created successfully
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

def verify_schema():
    """Check that all tables were created"""
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not service_role_key:
        print("❌ Missing credentials in .env")
        sys.exit(1)

    print(f"🔗 Connecting to Supabase...")
    supabase: Client = create_client(supabase_url, service_role_key)
    print(f"✅ Connected")

    expected_tables = [
        'unf_layers',
        'unf_elements',
        'brand_voices',
        'story_models',
        'deliverable_templates',
        'template_section_bindings',
        'deliverables',
        'element_dependencies'
    ]

    print("\n📊 Verifying schema...")
    print("="*80)

    # Try to query each table
    for table in expected_tables:
        try:
            result = supabase.table(table).select("*").limit(0).execute()
            print(f"✅ {table:<35} - exists")
        except Exception as e:
            print(f"❌ {table:<35} - ERROR: {e}")

    print("="*80)
    print("\n🎉 Schema verification complete!")
    print("\nNext steps:")
    print("  1. Load dummy data")
    print("  2. Test API endpoints")

if __name__ == "__main__":
    verify_schema()
