#!/usr/bin/env python3
"""
Test database connectivity
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

print("Testing Supabase connectivity...")
print("="*80)

supabase_url = os.getenv('SUPABASE_URL')
service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print(f"URL: {supabase_url}")
print(f"Key: {'✓ Set' if service_key else '✗ Not set'}")

try:
    supabase = create_client(supabase_url, service_key)
    print("\n✅ Supabase client created successfully")

    # Try a simple RPC call to test connection
    result = supabase.rpc('version').execute()
    print(f"✅ Connected to database!")
    print(f"PostgreSQL version info available: {bool(result)}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
