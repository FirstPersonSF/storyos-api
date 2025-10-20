#!/usr/bin/env python3
"""
Verify StoryOS schema using direct SQL query
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("🔍 Checking for storyos schema tables...")
print("="*80)

# Query to check tables in storyos schema
result = supabase.rpc('exec_sql', {
    'query': """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'storyos'
        ORDER BY table_name
    """
}).execute()

if hasattr(result, 'data') and result.data:
    print(f"✅ Found {len(result.data)} tables in storyos schema:")
    for row in result.data:
        print(f"   • {row.get('table_name', 'unknown')}")
else:
    # Try alternative: just query the schema directly
    print("Attempting to verify schema exists...")
    print("\nPlease run this SQL in Supabase SQL Editor to verify:")
    print("-"*80)
    print("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'storyos'
ORDER BY table_name;
    """)
    print("-"*80)

print("\n✅ If you can see tables in the Supabase Table Editor or SQL editor,")
print("   the schema was created successfully!")
print("\nNote: Supabase PostgREST API only exposes the 'public' schema by default.")
print("      We'll access the 'storyos' schema directly via SQL functions.")
